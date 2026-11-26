from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from claude_code import PRODUCT_DIR, read_answer_usage
from cost_tally import (
    AnswerEndRecord,
    AnswerUsage,
    CallTally,
    CostBook,
    LoadedText,
    MemoryCalls,
    SessionStartRecord,
    answer_end_record,
    describe_answer_cost,
    describe_loaded_text,
    describe_previous_session,
    last_transcript_offset,
    measure_loaded_text,
)

NOW = datetime(2026, 11, 26, 4, 42, 0, tzinfo=timezone.utc)
UNCOUNTED = "Claude Code가 붙이는 기억 지시와 잘림 경고는 세지 않았다."
RULES = "\n# 규칙\n\n기억마다 저장소를 적는다.\n\n"


def usage(input_tokens: int, created: int, read: int, output: int) -> dict:
    return {"input_tokens": input_tokens, "cache_creation_input_tokens": created,
            "cache_read_input_tokens": read, "output_tokens": output, "service_tier": "standard"}


def assistant(message_id: str, blocks: list[dict], tokens: dict, sidechain: bool = False) -> dict:
    return {"type": "assistant", "isSidechain": sidechain,
            "message": {"id": message_id, "role": "assistant", "content": blocks, "usage": tokens}}


def tool_use(tool_use_id: str, name: str, **tool_input: str) -> dict:
    return {"type": "tool_use", "id": tool_use_id, "name": name, "input": tool_input}


def tool_result(tool_use_id: str, content: object) -> dict:
    return {"type": "user", "isSidechain": False,
            "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": tool_use_id, "content": content}]}}


def api_request(source: str) -> dict:
    return {"type": "api-request", "querySource": source}


def hook_attachment(command: str, duration_ms: int, kind: str = "hook_success") -> dict:
    return {"type": "attachment", "attachment": {"type": kind, "hookName": "Stop", "hookEvent": "Stop",
                                                 "command": command, "durationMs": duration_ms, "exitCode": 0}}


def jsonl(entries: list[dict]) -> str:
    return "".join(json.dumps(entry, ensure_ascii=False) + "\n" for entry in entries)


class TempFolderCase(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        self.memory = self.root / "memory"
        self.memory.mkdir()
        self.transcript = self.root / "t.jsonl"


class AnswerUsageTest(TempFolderCase):
    def read(self, entries: list[dict], offset: int = 0):
        self.transcript.write_text(jsonl(entries), encoding="utf-8")
        return read_answer_usage(self.transcript, offset, self.memory)

    def test_requests_are_distinct_message_ids_and_usage_is_added_once_per_id(self) -> None:
        answer = self.read([
            api_request("sdk"),
            assistant("m1", [{"type": "thinking"}], usage(2, 100, 1000, 10)),
            assistant("m1", [{"type": "text", "text": "본다"}], usage(2, 100, 1000, 10)),
            assistant("m1", [tool_use("t1", "Bash", command="ls")], usage(2, 100, 1000, 10)),
            api_request("sdk"),
            assistant("m2", [{"type": "text", "text": "끝"}], usage(3, 5, 1100, 20)),
            api_request("compact"),
            assistant("m3", [{"type": "text", "text": "옆"}], usage(50, 50, 50, 50), sidechain=True),
        ]).answer

        self.assertEqual(answer.requests, 2)
        self.assertEqual(answer.usage, {"input_tokens": 5, "cache_creation_input_tokens": 105,
                                        "cache_read_input_tokens": 2100, "output_tokens": 30})
        self.assertEqual(answer.query_sources, {"sdk": 2, "compact": 1})

    def test_the_last_line_of_a_message_id_gives_its_usage(self) -> None:
        answer = self.read([
            assistant("m1", [{"type": "text", "text": "a"}], usage(1, 1, 1, 1)),
            assistant("m1", [{"type": "text", "text": "b"}], usage(1, 1, 1, 9)),
        ]).answer

        self.assertEqual(answer.usage["output_tokens"], 9)

    def test_memory_folder_calls_are_split_into_reads_and_writes_with_result_lengths(self) -> None:
        inside = str(self.memory / "redis-port.md")
        answer = self.read([
            assistant("m1", [
                tool_use("r1", "Read", file_path=inside),
                tool_use("r2", "Grep", pattern="6380", path=str(self.memory)),
                tool_use("r3", "Glob", pattern="*.md", path=str(self.memory)),
                tool_use("r4", "Bash", command=f"ls {self.memory} | grep -i redis"),
                tool_use("w1", "Write", file_path=inside, content="x"),
                tool_use("w2", "Edit", file_path=inside, old_string="a", new_string="b"),
                tool_use("w3", "MultiEdit", file_path=inside),
            ], usage(1, 1, 1, 1)),
            tool_result("r1", "가" * 100),
            tool_result("r2", [{"type": "text", "text": "가" * 20}, {"type": "text", "text": "나" * 5}]),
            tool_result("r3", ""),
            tool_result("r4", "가" * 7),
            tool_result("w1", "written"),
        ]).answer

        self.assertEqual(answer.memory_calls, MemoryCalls(read=CallTally(4, 132), write=CallTally(3, 7)))

    def test_calls_outside_the_memory_folder_are_not_counted(self) -> None:
        journal = self.root / "memory-journal"
        answer = self.read([
            assistant("m1", [
                tool_use("o1", "Read", file_path=str(self.root / "work" / "README.md")),
                tool_use("o2", "Bash", command=f"cat {journal}/events.jsonl"),
                tool_use("o3", "Read", file_path="memory/redis-port.md"),
                tool_use("o4", "Grep", pattern="6380"),
                tool_use("o5", "Bash", command="ls ~/memory"),
                tool_use("o6", "Read", file_path=str(self.root / "memory.bak" / "a.md")),
            ], usage(1, 1, 1, 1)),
            assistant("side", [tool_use("s1", "Read", file_path=str(self.memory / "a.md"))], usage(1, 1, 1, 1),
                      sidechain=True),
            tool_result("o1", "가" * 50),
            tool_result("s1", "가" * 50),
        ]).answer

        self.assertEqual(answer.memory_calls, MemoryCalls())

    def test_hook_durations_are_the_attachments_of_this_product_only(self) -> None:
        ours = f"/usr/bin/python3 {PRODUCT_DIR}/stop_hook.py --show-cost"
        answer = self.read([
            hook_attachment(f"/usr/bin/python3 {PRODUCT_DIR}/session_start_hook.py", 40),
            hook_attachment("/usr/bin/python3 /elsewhere/pre-tool-guard.py", 3, "hook_non_blocking_error"),
            hook_attachment(ours, 56),
            hook_attachment(ours, 70, "hook_non_blocking_error"),
            {"type": "system", "subtype": "stop_hook_summary", "hookInfos": [{"command": ours, "durationMs": 56}]},
        ]).answer

        self.assertEqual(answer.harness_hook_ms, [40, 56, 70])

    def test_reading_starts_at_the_offset_and_leaves_an_unfinished_last_line(self) -> None:
        first = jsonl([assistant("m1", [], usage(1, 1, 1, 1))])
        second = jsonl([assistant("m2", [], usage(1, 1, 1, 1))])
        unfinished = json.dumps(assistant("m3", [], usage(1, 1, 1, 1)))[:30]
        self.transcript.write_text(first + second + unfinished, encoding="utf-8")
        offset = len(first.encode("utf-8"))

        read = read_answer_usage(self.transcript, offset, self.memory)

        self.assertEqual((read.answer.requests, read.next_offset), (1, offset + len(second.encode("utf-8"))))

    def test_a_transcript_shorter_than_the_offset_is_read_from_the_start(self) -> None:
        read = self.read([assistant("m1", [], usage(1, 1, 1, 1))], offset=10_000)

        self.assertEqual(read.answer.requests, 1)

    def test_unreadable_lines_are_skipped(self) -> None:
        self.transcript.write_text("{깨진 줄\n" + jsonl([assistant("m1", [], usage(1, 1, 1, 1))]) + "[1, 2]\n",
                                   encoding="utf-8")

        self.assertEqual(read_answer_usage(self.transcript, 0, self.memory).answer.requests, 1)

    def test_missing_transcript_is_unknown_and_keeps_the_offset(self) -> None:
        read = read_answer_usage(self.root / "없음.jsonl", 123, self.memory)

        self.assertEqual((read.answer, read.next_offset), (None, 123))


class LoadedTextTest(TempFolderCase):
    def test_index_chars_follow_the_loaded_lines_and_rules_are_counted_when_found_verbatim(self) -> None:
        lines = [f"- [기억 {n}](m{n}.md) — [todo-app] 설명 {n}\n" for n in range(250)]
        (self.memory / "MEMORY.md").write_text("".join(lines), encoding="utf-8")

        loaded = measure_loaded_text(self.memory, RULES, "# 내 지시\n" + RULES.strip() + "\n끝\n")

        self.assertEqual(loaded, LoadedText(True, 250, 200, sum(len(line) for line in lines[:200]), len(RULES.strip())))

    def test_rules_not_in_the_instruction_file_are_not_found(self) -> None:
        loaded = measure_loaded_text(self.memory, RULES, "기억마다 저장소를 적는다.")

        self.assertEqual((loaded.index_exists, loaded.rules_chars), (False, None))

    def test_screen_line_for_a_truncated_index_with_rules(self) -> None:
        loaded = LoadedText(True, 250, 200, 20_001, 969)

        self.assertEqual(describe_loaded_text(loaded, 45, UNCOUNTED), (
            "기억 도구가 이 세션에 실은 글은 20,970자다(색인 앞 200줄 20,001자, 얹는 제품의 지시 글 969자). "
            "이 글은 모델 요청마다 다시 읽힌다. Claude Code가 붙이는 기억 지시와 잘림 경고는 세지 않았다. 이 hook 45ms(Python이 뜨는 시간은 빼고 잰 값)."))

    def test_screen_line_without_rules_shows_the_index_alone(self) -> None:
        loaded = LoadedText(True, 2, 2, 120, None)

        self.assertEqual(describe_loaded_text(loaded, 12, UNCOUNTED), (
            "기억 도구가 이 세션에 실은 글은 120자다(색인 2줄 120자). "
            "이 글은 모델 요청마다 다시 읽힌다. Claude Code가 붙이는 기억 지시와 잘림 경고는 세지 않았다. 이 hook 12ms(Python이 뜨는 시간은 빼고 잰 값)."))

    def test_screen_line_without_index_or_rules(self) -> None:
        loaded = LoadedText(False, 0, 0, 0, None)

        self.assertEqual(describe_loaded_text(loaded, 9, UNCOUNTED),
                         "기억 도구가 이 세션에 실은 글이 없다. 색인 MEMORY.md가 없다. 이 hook 9ms(Python이 뜨는 시간은 빼고 잰 값).")


def answer_record(**overrides) -> AnswerEndRecord:
    fields = dict(at="2026-11-26T04:42:30Z", transcript_offset=0, requests=7, usage=None, query_sources={},
                  memory_calls=MemoryCalls(), notice_chars=0, stop_hook_active=False, reread_chars=146_790,
                  hook_ms=30, claude_code_hook_ms=[])
    return AnswerEndRecord(**(fields | overrides))


class CostRecordTest(TempFolderCase):
    def setUp(self) -> None:
        super().setUp()
        self.book = CostBook(self.root / "journal", ("세지 못한 것 하나",))
        self.start = SessionStartRecord("2026-11-26T04:42:00Z", "startup", 200, 20_001, 969, 28)

    def test_reread_is_requests_times_the_text_loaded_at_the_last_session_start(self) -> None:
        resumed = SessionStartRecord("2026-11-26T05:00:00Z", "resume", 10, 1_000, None, 20)
        seven = AnswerUsage(7, {}, {}, MemoryCalls(), [])

        self.assertEqual(answer_end_record([self.start], NOW, 0, seven, 0, False, 1).reread_chars, 146_790)
        self.assertEqual(answer_end_record([self.start, resumed], NOW, 0, seven, 0, False, 1).reread_chars, 7_000)
        self.assertIsNone(answer_end_record([], NOW, 0, seven, 0, False, 1).reread_chars)
        self.assertIsNone(answer_end_record([self.start], NOW, 0, None, 0, False, 1).reread_chars)

    def test_records_round_trip_and_the_last_answer_gives_the_offset(self) -> None:
        self.book.append("s1", self.start)
        self.book.append("s1", answer_record(transcript_offset=500), answer_ended=True)
        self.book.append("s1", answer_record(transcript_offset=900, memory_calls=None, requests=None,
                                             reread_chars=None), answer_ended=True)

        records = self.book.read("s1")

        self.assertEqual(records[0], self.start)
        self.assertEqual(last_transcript_offset(records), 900)
        self.assertEqual(self.book.last_session(), "s1")
        self.assertTrue(self.book.summary_path("s1").is_file())

    def test_previous_session_line(self) -> None:
        self.book.append("9a3ad47e-9115-4b28", self.start)
        self.book.append("9a3ad47e-9115-4b28", answer_record(
            memory_calls=MemoryCalls(read=CallTally(1, 126))), answer_ended=True)

        line = describe_previous_session(self.book, "next-session")

        self.assertEqual(line, (
            "지난 세션 9a3ad47e(2026-11-26 04:42 UTC)에서 기억 도구가 쓴 것: 답 1번, 모델 요청 7번이 실린 글을 "
            "다시 읽어 146,790자, 모델이 기억 폴더를 다룬 호출 1번(결과 126자), 모델에게 보낸 알림 0자, "
            f"hook 2번 합 58ms(Python이 뜨는 시간은 빼고). 자세히: {self.book.summary_path('9a3ad47e-9115-4b28')}"))

    def test_resumed_session_line_says_so_far_in_this_session(self) -> None:
        self.book.append("s1", self.start)
        self.book.append("s1", answer_record(), answer_ended=True)

        self.assertTrue(describe_previous_session(self.book, "s1").startswith("이 세션에서 지금까지 기억 도구가 쓴 것: 답 1번,"))

    def test_no_previous_session_line_before_any_answer_ended(self) -> None:
        self.book.append("s1", self.start)

        self.assertIsNone(describe_previous_session(self.book, "s2"))

    def test_answer_line_only_when_memory_calls_a_notice_or_a_slow_hook(self) -> None:
        path = self.book.summary_path("s1")

        self.assertIsNone(describe_answer_cost(answer_record(hook_ms=100), path))
        self.assertEqual(describe_answer_cost(answer_record(hook_ms=101), path), (
            f"이번 답에서 기억 도구가 쓴 것: 모델이 기억 폴더를 다룬 호출 0번, 알림 0자, hook 101ms(Python이 뜨는 시간은 빼고 잰 값). 세션 합계: {path}"))
        self.assertEqual(describe_answer_cost(answer_record(
            memory_calls=MemoryCalls(read=CallTally(2, 3_120)), notice_chars=412, hook_ms=28), path), (
            "이번 답에서 기억 도구가 쓴 것: 모델이 기억 폴더를 다룬 호출 2번(읽기 2번, 결과 3,120자가 대화에 들었다), "
            f"알림 412자, hook 28ms(Python이 뜨는 시간은 빼고 잰 값). 세션 합계: {path}"))
        self.assertEqual(describe_answer_cost(answer_record(
            memory_calls=MemoryCalls(read=CallTally(1, 10), write=CallTally(1, 5))), path), (
            "이번 답에서 기억 도구가 쓴 것: 모델이 기억 폴더를 다룬 호출 2번(읽기 1번, 쓰기 1번, 결과 15자가 대화에 들었다), "
            f"알림 0자, hook 30ms(Python이 뜨는 시간은 빼고 잰 값). 세션 합계: {path}"))


if __name__ == "__main__":
    unittest.main()
