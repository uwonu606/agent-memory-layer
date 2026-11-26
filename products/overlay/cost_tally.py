from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Sequence

from memory_journal import (
    INDEX_CHAR_LIMIT,
    INDEX_FILE_NAME,
    INDEX_LINE_LIMIT,
    Journal,
    loaded_index_line_count,
    read_text_verbatim,
    readable_time,
    utc_text,
    write_text_verbatim,
)

HOOK_MS_BUDGET = 100
COSTS_DIR_NAME = "costs"
LAST_SESSION_FILE_NAME = "last-session"
SHORT_SESSION_LENGTH = 8
USAGE_FIELDS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
HOOK_MS_EXCLUDES = "(Python이 뜨는 시간은 빼고 잰 값)"
CACHE_NOTE = "cache에서 다시 읽은 몫은 처음 읽는 값보다 싸게 센다(API 값으로 0.1배 안팎)."


def elapsed_ms(started: float) -> int:
    return round((time.perf_counter() - started) * 1000)


def thousands(number: int) -> str:
    return f"{number:,}"


@dataclass(frozen=True)
class LoadedText:
    index_exists: bool
    index_total_lines: int
    index_lines: int
    index_chars: int
    rules_chars: int | None

    @property
    def total_chars(self) -> int:
        return self.index_chars + (self.rules_chars or 0)

    @property
    def index_truncated(self) -> bool:
        return self.index_lines < self.index_total_lines


def measure_loaded_text(memory_dir: Path, rules_text: str, instructions_text: str | None) -> LoadedText:
    index_path = memory_dir / INDEX_FILE_NAME
    index_text = read_text_verbatim(index_path) if index_path.is_file() else None
    lines = (index_text or "").splitlines(keepends=True)
    loaded_lines = loaded_index_line_count(index_text or "")
    rules = rules_text.strip()
    rules_found = bool(rules) and instructions_text is not None and rules in instructions_text
    return LoadedText(
        index_exists=index_text is not None,
        index_total_lines=len(lines),
        index_lines=loaded_lines,
        index_chars=sum(len(line) for line in lines[:loaded_lines]),
        rules_chars=len(rules) if rules_found else None,
    )


@dataclass(frozen=True)
class CallTally:
    count: int = 0
    result_chars: int = 0

    def plus(self, other: CallTally) -> CallTally:
        return CallTally(self.count + other.count, self.result_chars + other.result_chars)


@dataclass(frozen=True)
class MemoryCalls:
    read: CallTally = CallTally()
    write: CallTally = CallTally()

    @property
    def count(self) -> int:
        return self.read.count + self.write.count

    @property
    def result_chars(self) -> int:
        return self.read.result_chars + self.write.result_chars

    def plus(self, other: MemoryCalls) -> MemoryCalls:
        return MemoryCalls(self.read.plus(other.read), self.write.plus(other.write))

    def to_json(self) -> dict:
        return {kind: {"count": tally.count, "result_chars": tally.result_chars}
                for kind, tally in (("read", self.read), ("write", self.write))}

    @classmethod
    def from_json(cls, record: dict) -> MemoryCalls:
        return cls(*(CallTally(record[kind]["count"], record[kind]["result_chars"]) for kind in ("read", "write")))


@dataclass(frozen=True)
class AnswerUsage:
    requests: int
    usage: dict[str, int]
    query_sources: dict[str, int]
    memory_calls: MemoryCalls
    harness_hook_ms: list[int]
    last_message_id: str | None = None


@dataclass(frozen=True)
class SessionStartRecord:
    at: str
    source: str | None
    index_lines: int
    index_chars: int
    rules_chars: int | None
    hook_ms: int

    def to_json(self) -> dict:
        return {"event": "session_start", "at": self.at, "source": self.source, "index_lines": self.index_lines,
                "index_chars": self.index_chars, "rules_chars": self.rules_chars, "hook_ms": self.hook_ms}

    @classmethod
    def from_json(cls, record: dict) -> SessionStartRecord:
        return cls(record["at"], record.get("source"), record["index_lines"], record["index_chars"],
                   record.get("rules_chars"), record["hook_ms"])

    @property
    def loaded_chars(self) -> int:
        return self.index_chars + (self.rules_chars or 0)


@dataclass(frozen=True)
class AnswerEndRecord:
    at: str
    transcript_offset: int
    requests: int | None
    usage: dict[str, int] | None
    query_sources: dict[str, int] | None
    memory_calls: MemoryCalls | None
    notice_chars: int
    stop_hook_active: bool
    reread_chars: int | None
    hook_ms: int
    claude_code_hook_ms: list[int] | None = field(default=None)
    last_message_id: str | None = None

    def to_json(self) -> dict:
        return {"event": "answer_end", "at": self.at, "transcript_offset": self.transcript_offset,
                "requests": self.requests, "usage": self.usage, "query_sources": self.query_sources,
                "memory_calls": self.memory_calls.to_json() if self.memory_calls is not None else None,
                "notice_chars": self.notice_chars, "stop_hook_active": self.stop_hook_active,
                "reread_chars": self.reread_chars, "hook_ms": self.hook_ms,
                "claude_code_hook_ms": self.claude_code_hook_ms, "last_message_id": self.last_message_id}

    @classmethod
    def from_json(cls, record: dict) -> AnswerEndRecord:
        calls = record.get("memory_calls")
        return cls(record["at"], record["transcript_offset"], record.get("requests"), record.get("usage"),
                   record.get("query_sources"), MemoryCalls.from_json(calls) if calls is not None else None,
                   record["notice_chars"], record["stop_hook_active"], record.get("reread_chars"),
                   record["hook_ms"], record.get("claude_code_hook_ms"), record.get("last_message_id"))

    @property
    def transcript_known(self) -> bool:
        return self.requests is not None


CostRecord = SessionStartRecord | AnswerEndRecord


class CostBook:
    def __init__(self, journal_dir: Path, uncounted: Sequence[str] = ()):
        self.journal = Journal(journal_dir)
        self.uncounted = tuple(uncounted)
        self.root = journal_dir / COSTS_DIR_NAME
        self.last_session_path = self.root / LAST_SESSION_FILE_NAME

    def records_path(self, session: str) -> Path:
        return self.root / f"{session}.jsonl"

    def summary_path(self, session: str) -> Path:
        return self.root / f"{session}.md"

    def read(self, session: str) -> list[CostRecord]:
        path = self.records_path(session)
        if not path.is_file():
            return []
        records: list[CostRecord] = []
        for line in read_text_verbatim(path).splitlines():
            try:
                record = json.loads(line)
                if record.get("event") == "session_start":
                    records.append(SessionStartRecord.from_json(record))
                elif record.get("event") == "answer_end":
                    records.append(AnswerEndRecord.from_json(record))
            except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
                continue
        return records

    def append(self, session: str, record: CostRecord, answer_ended: bool = False) -> None:
        with self.journal.locked():
            self.root.mkdir(parents=True, exist_ok=True)
            with open(self.records_path(session), "a", encoding="utf-8", newline="") as handle:
                handle.write(json.dumps(record.to_json(), ensure_ascii=False) + "\n")
            write_text_verbatim(self.summary_path(session), render_session_costs(session, self.read(session), self.uncounted))
            if answer_ended:
                write_text_verbatim(self.last_session_path, session + "\n")

    def last_session(self) -> str | None:
        if not self.last_session_path.is_file():
            return None
        session = read_text_verbatim(self.last_session_path).strip()
        return session or None


def session_start_record(now: datetime, source: str | None, loaded: LoadedText, hook_ms: int) -> SessionStartRecord:
    return SessionStartRecord(utc_text(now), source, loaded.index_lines, loaded.index_chars, loaded.rules_chars, hook_ms)


def last_transcript_offset(records: Sequence[CostRecord]) -> int:
    answers = [record for record in records if isinstance(record, AnswerEndRecord)]
    return answers[-1].transcript_offset if answers else 0


def last_counted_message_id(records: Sequence[CostRecord]) -> str | None:
    answers = [record for record in records if isinstance(record, AnswerEndRecord)]
    return answers[-1].last_message_id if answers else None


def answer_end_record(
    records: Sequence[CostRecord],
    now: datetime,
    transcript_offset: int,
    answer: AnswerUsage | None,
    notice_chars: int,
    stop_hook_active: bool,
    hook_ms: int,
) -> AnswerEndRecord:
    starts = [record for record in records if isinstance(record, SessionStartRecord)]
    reread = answer.requests * starts[-1].loaded_chars if answer is not None and starts else None
    return AnswerEndRecord(
        at=utc_text(now),
        transcript_offset=transcript_offset,
        requests=answer.requests if answer else None,
        usage=answer.usage if answer else None,
        query_sources=answer.query_sources if answer else None,
        memory_calls=answer.memory_calls if answer else None,
        notice_chars=notice_chars,
        stop_hook_active=stop_hook_active,
        reread_chars=reread,
        hook_ms=hook_ms,
        claude_code_hook_ms=answer.harness_hook_ms if answer else None,
        last_message_id=answer.last_message_id if answer else last_counted_message_id(records),
    )


@dataclass(frozen=True)
class SessionTotals:
    answers: int
    unknown_answers: int
    requests: int
    continued_requests: int
    usage: dict[str, int]
    reread_chars: int
    memory_calls: MemoryCalls
    notice_chars: int
    hook_runs: int
    hook_ms: int
    longest_hook_ms: int
    harness_hook_ms: list[int]


def session_totals(records: Sequence[CostRecord]) -> SessionTotals:
    answers = [record for record in records if isinstance(record, AnswerEndRecord)]
    known = [answer for answer in answers if answer.transcript_known]
    calls = MemoryCalls()
    for answer in known:
        if answer.memory_calls is not None:
            calls = calls.plus(answer.memory_calls)
    return SessionTotals(
        answers=len(answers),
        unknown_answers=len(answers) - len(known),
        requests=sum(answer.requests for answer in known),
        continued_requests=sum(answer.requests for answer in known if answer.stop_hook_active),
        usage={name: sum((answer.usage or {}).get(name, 0) for answer in known) for name in USAGE_FIELDS},
        reread_chars=sum(answer.reread_chars or 0 for answer in known),
        memory_calls=calls,
        notice_chars=sum(answer.notice_chars for answer in answers),
        hook_runs=len(records),
        hook_ms=sum(record.hook_ms for record in records),
        longest_hook_ms=max((record.hook_ms for record in records), default=0),
        harness_hook_ms=[ms for answer in answers for ms in (answer.claude_code_hook_ms or [])],
    )


def describe_loaded_text(loaded: LoadedText, hook_ms: int, uncounted_note: str) -> str:
    hook = f"이 hook {thousands(hook_ms)}ms{HOOK_MS_EXCLUDES}."
    if loaded.total_chars == 0:
        missing = " 색인 MEMORY.md가 없다." if not loaded.index_exists else ""
        return f"기억 도구가 이 세션에 실은 글이 없다.{missing} {hook}"
    parts = []
    if loaded.index_exists:
        lines = f"앞 {loaded.index_lines}줄" if loaded.index_truncated else f"{loaded.index_lines}줄"
        parts.append(f"색인 {lines} {thousands(loaded.index_chars)}자")
    if loaded.rules_chars is not None:
        parts.append(f"얹는 제품의 지시 글 {thousands(loaded.rules_chars)}자")
    return (f"기억 도구가 이 세션에 실은 글은 {thousands(loaded.total_chars)}자다({', '.join(parts)}). "
            f"이 글은 모델 요청마다 다시 읽힌다. {uncounted_note} {hook}")


def describe_previous_session(book: CostBook, current_session: str) -> str | None:
    session = book.last_session()
    if session is None:
        return None
    records = book.read(session)
    if not records:
        return None
    totals = session_totals(records)
    if session == current_session:
        head = "이 세션에서 지금까지"
    else:
        head = f"지난 세션 {session[:SHORT_SESSION_LENGTH]}({readable_time(records[-1].at)[:16]} UTC)에서"
    if totals.answers == totals.unknown_answers:
        requests = "모델 요청은 모름"
    else:
        requests = (f"모델 요청 {thousands(totals.requests)}번이 실린 글을 다시 읽어 "
                    f"{thousands(totals.reread_chars)}자")
    calls = totals.memory_calls
    calls_text = f"모델이 기억 폴더를 다룬 호출 {thousands(calls.count)}번"
    if calls.count:
        calls_text += f"(결과 {thousands(calls.result_chars)}자)"
    unknown = f" transcript를 읽지 못한 답 {totals.unknown_answers}번은 세지 않았다." if totals.unknown_answers else ""
    return (f"{head} 기억 도구가 쓴 것: 답 {thousands(totals.answers)}번, {requests}, {calls_text}, "
            f"모델에게 보낸 알림 {thousands(totals.notice_chars)}자, "
            f"hook {totals.hook_runs}번 합 {thousands(totals.hook_ms)}ms(Python이 뜨는 시간은 빼고).{unknown} 자세히: {book.summary_path(session)}")


def describe_answer_cost(record: AnswerEndRecord, summary_path: Path) -> str | None:
    calls = record.memory_calls
    if not ((calls is not None and calls.count) or record.notice_chars or record.hook_ms > HOOK_MS_BUDGET):
        return None
    return (f"이번 답에서 기억 도구가 쓴 것: {memory_calls_text(calls)}, 알림 {thousands(record.notice_chars)}자, "
            f"hook {thousands(record.hook_ms)}ms{HOOK_MS_EXCLUDES}. 세션 합계: {summary_path}")


def memory_calls_text(calls: MemoryCalls | None) -> str:
    if calls is None:
        return "모델이 기억 폴더를 다룬 호출은 모름"
    text = f"모델이 기억 폴더를 다룬 호출 {thousands(calls.count)}번"
    if not calls.count:
        return text
    kinds = [f"{label} {thousands(tally.count)}번" for label, tally in (("읽기", calls.read), ("쓰기", calls.write))
             if tally.count]
    return text + f"({', '.join(kinds)}, 결과 {thousands(calls.result_chars)}자가 대화에 들었다)"


def render_session_costs(session: str, records: Sequence[CostRecord], uncounted: Sequence[str]) -> str:
    totals = session_totals(records)
    starts = [record for record in records if isinstance(record, SessionStartRecord)]
    answers = [record for record in records if isinstance(record, AnswerEndRecord)]
    usage = totals.usage
    calls = totals.memory_calls
    parts = [
        f"# 세션 {session}에서 기억 도구가 쓴 것\n",
        "기억 도구(얹는 제품)가 이 세션에서 쓴 양이다. 같은 폴더의 "
        f"`{session}.jsonl`에서 지었다. 시각은 UTC이고, 글자 수는 줄바꿈을 포함한다.\n",
        "## 합계\n",
        "\n".join([
            f"- 답 {thousands(totals.answers)}번, 모델 요청 {thousands(totals.requests)}번. "
            f"그 가운데 앞 `Stop` hook이 대화를 이어서 생긴 요청 {thousands(totals.continued_requests)}번",
            f"- 요청의 token: 입력 {thousands(usage['input_tokens'])}, "
            f"cache 만듦 {thousands(usage['cache_creation_input_tokens'])}, "
            f"cache 읽음 {thousands(usage['cache_read_input_tokens'])}, 출력 {thousands(usage['output_tokens'])}",
            f"- 실린 글을 모델 요청마다 다시 읽은 양: {thousands(totals.reread_chars)}자. {CACHE_NOTE}",
            f"- 모델이 기억 폴더를 다룬 호출: 읽기 {thousands(calls.read.count)}번, 쓰기 {thousands(calls.write.count)}번, "
            f"결과 {thousands(calls.result_chars)}자가 대화에 들었다",
            f"- 모델에게 보낸 알림: {thousands(totals.notice_chars)}자",
            f"- hook: {totals.hook_runs}번, hook 안에서 잰 합 {thousands(totals.hook_ms)}ms, "
            f"가장 긴 것 {thousands(totals.longest_hook_ms)}ms. Claude Code가 잰 이 제품의 hook "
            f"{len(totals.harness_hook_ms)}번 합 {thousands(sum(totals.harness_hook_ms))}ms",
        ] + ([f"- transcript를 읽지 못해 모델 요청, token, 호출을 모르는 답: {totals.unknown_answers}번"]
             if totals.unknown_answers else [])) + "\n",
        "## 예산\n",
        "\n".join(budget_lines(totals, starts)) + "\n",
        "## 세션 시작마다\n",
        render_starts(starts),
        "## 답마다\n",
        render_answers(answers),
        "## 세지 못한 것\n",
        "\n".join(f"- {item}" for item in uncounted) + "\n" if uncounted else "없다.\n",
    ]
    return "\n".join(parts)


def budget_lines(totals: SessionTotals, starts: Sequence[SessionStartRecord]) -> list[str]:
    hook_verdict = "안이다" if totals.longest_hook_ms <= HOOK_MS_BUDGET else "넘었다"
    lines = [f"- hook 한 번 {HOOK_MS_BUDGET}ms: 가장 긴 hook이 {thousands(totals.longest_hook_ms)}ms로 예산 {hook_verdict}"]
    if starts:
        last = starts[-1]
        index_verdict = ("안이다" if last.index_lines <= INDEX_LINE_LIMIT and last.index_chars <= INDEX_CHAR_LIMIT
                         else "넘었다")
        lines.append(f"- 색인 상한 {INDEX_LINE_LIMIT}줄과 {thousands(INDEX_CHAR_LIMIT)}자: 마지막 세션 시작에 실린 색인이 "
                     f"{last.index_lines}줄 {thousands(last.index_chars)}자로 상한 {index_verdict}")
    else:
        lines.append(f"- 색인 상한 {INDEX_LINE_LIMIT}줄과 {thousands(INDEX_CHAR_LIMIT)}자: 이 세션의 시작을 세지 못했다")
    return lines


def render_starts(starts: Sequence[SessionStartRecord]) -> str:
    if not starts:
        return "세지 못했다. 세션이 시작할 때의 hook이 쓴 양을 세지 않았다.\n"
    rows = ["| 시각 | 계기 | 색인 줄 | 색인 글자 | 지시 글 글자 | hook ms |", "|---|---|---|---|---|---|"]
    rows.extend(
        f"| {readable_time(start.at)} | {start.source or '모름'} | {start.index_lines} | {thousands(start.index_chars)} | "
        f"{thousands(start.rules_chars) if start.rules_chars is not None else '찾지 못함'} | {start.hook_ms} |"
        for start in starts)
    return "\n".join(rows) + "\n"


def render_answers(answers: Sequence[AnswerEndRecord]) -> str:
    if not answers:
        return "아직 끝난 답이 없다.\n"
    rows = ["| 시각 | 모델 요청 | 이어진 답 | token 입력 / cache 만듦 / cache 읽음 / 출력 | 다시 읽은 글자 | "
            "기억 폴더 읽기 / 쓰기 | 결과 글자 | 알림 글자 | hook ms | Claude Code가 잰 hook ms |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for answer in answers:
        unknown = "모름"
        usage = (" / ".join(thousands(answer.usage.get(name, 0)) for name in USAGE_FIELDS)
                 if answer.usage is not None else unknown)
        calls = answer.memory_calls
        rows.append(" | ".join([
            f"| {readable_time(answer.at)}",
            thousands(answer.requests) if answer.requests is not None else unknown,
            "예" if answer.stop_hook_active else "아니오",
            usage,
            thousands(answer.reread_chars) if answer.reread_chars is not None else unknown,
            f"{calls.read.count} / {calls.write.count}" if calls is not None else unknown,
            thousands(calls.result_chars) if calls is not None else unknown,
            thousands(answer.notice_chars),
            str(answer.hook_ms),
            ", ".join(str(ms) for ms in answer.claude_code_hook_ms) if answer.claude_code_hook_ms else "-",
        ]) + " |")
    return "\n".join(rows) + "\n"
