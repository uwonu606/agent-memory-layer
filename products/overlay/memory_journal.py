from __future__ import annotations

import difflib
import fcntl
import json
import re
import shlex
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Iterator

INDEX_FILE_NAME = "MEMORY.md"
INDEX_LINE_LIMIT = 200
INDEX_CHAR_LIMIT = 25_000
SCREEN_MEMORY_LINE_LIMIT = 10


class EventKind(str, Enum):
    CREATED = "created"
    CHANGED = "changed"
    DELETED = "deleted"
    LOADED = "loaded"
    RESTORED = "restored"


class Cause(str, Enum):
    PROMPT = "prompt"
    PROMPT_NOT_FOUND = "prompt_not_found"
    OUTSIDE_SESSION = "outside_session"
    SESSION_START = "session_start"
    RESTORE_COMMAND = "restore_command"


VERSION_MAKING_KINDS = (EventKind.CREATED, EventKind.CHANGED, EventKind.RESTORED)


@dataclass(frozen=True)
class Event:
    kind: EventKind
    file: str
    at: str
    session: str | None
    version: int | None
    cause: Cause
    prompt: str | None = None
    restored_from: int | None = None

    def to_json_line(self) -> str:
        record = {
            "event": self.kind.value,
            "file": self.file,
            "at": self.at,
            "session": self.session,
            "version": self.version,
            "cause": self.cause.value,
            "prompt": self.prompt,
        }
        if self.kind is EventKind.RESTORED:
            record["restored_from"] = self.restored_from
        return json.dumps(record, ensure_ascii=False)

    @classmethod
    def from_json_line(cls, line: str) -> Event:
        record = json.loads(line)
        return cls(
            kind=EventKind(record["event"]),
            file=record["file"],
            at=record["at"],
            session=record["session"],
            version=record["version"],
            cause=Cause(record["cause"]),
            prompt=record.get("prompt"),
            restored_from=record.get("restored_from"),
        )


@dataclass(frozen=True)
class AnswerEnded:
    session: str
    prompt: str | None


@dataclass(frozen=True)
class SeenOutsideSession:
    pass


Trigger = AnswerEnded | SeenOutsideSession


@dataclass(frozen=True)
class IndexEntry:
    line: str
    title: str
    file: str
    scope: str | None


@dataclass(frozen=True)
class MemoryVersion:
    content: str
    index_line: str | None


@dataclass(frozen=True)
class ObservedMemory:
    version: MemoryVersion
    content_mtime: float


@dataclass(frozen=True)
class MemoryFolder:
    memories: dict[str, ObservedMemory]
    index_text: str | None
    index_mtime: float | None


@dataclass(frozen=True)
class Tracked:
    latest_version: int
    present: bool


class RestoreError(Exception):
    pass


INDEX_LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
INDEX_SCOPE = re.compile(r"\s—\s*\[([^\]]+)\]")
ORIGIN_SESSION = re.compile(r"^\s*originSessionId:\s*['\"]?([^'\"\s]+)['\"]?\s*$", re.MULTILINE)


def parse_index_entry(line: str) -> IndexEntry | None:
    link = INDEX_LINK.search(line)
    if link is None or "://" in link.group(2):
        return None
    after_link = line[link.end():]
    scope = INDEX_SCOPE.match(after_link)
    return IndexEntry(
        line=line,
        title=link.group(1),
        file=link.group(2).removeprefix("./"),
        scope=scope.group(1) if scope else None,
    )


def index_entries(index_text: str) -> list[IndexEntry]:
    entries = (parse_index_entry(line) for line in index_text.splitlines())
    return [entry for entry in entries if entry is not None]


def first_index_line_per_file(index_text: str | None) -> dict[str, str]:
    lines: dict[str, str] = {}
    for entry in index_entries(index_text or ""):
        lines.setdefault(entry.file, entry.line)
    return lines


def loaded_index_line_count(index_text: str) -> int:
    loaded = 0
    chars = 0
    for line in index_text.splitlines(keepends=True):
        chars += len(line)
        if loaded == INDEX_LINE_LIMIT or chars > INDEX_CHAR_LIMIT:
            break
        loaded += 1
    return loaded


def origin_session_of(content: str) -> str | None:
    if not content.startswith("---"):
        return None
    frontmatter_end = content.find("\n---", 3)
    frontmatter = content[: frontmatter_end if frontmatter_end != -1 else len(content)]
    found = ORIGIN_SESSION.search(frontmatter)
    return found.group(1) if found else None


def read_text_verbatim(path: Path) -> str:
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.read()


def write_text_verbatim(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def read_memory_folder(memory_dir: Path) -> MemoryFolder:
    index_path = memory_dir / INDEX_FILE_NAME
    index_text = read_text_verbatim(index_path) if index_path.is_file() else None
    index_lines = first_index_line_per_file(index_text)
    memories: dict[str, ObservedMemory] = {}
    if memory_dir.is_dir():
        for path in sorted(memory_dir.glob("*.md")):
            if path.name == INDEX_FILE_NAME or path.name.startswith(".") or not path.is_file():
                continue
            memories[path.name] = ObservedMemory(
                version=MemoryVersion(read_text_verbatim(path), index_lines.get(path.name)),
                content_mtime=path.stat().st_mtime,
            )
    return MemoryFolder(
        memories=memories,
        index_text=index_text,
        index_mtime=index_path.stat().st_mtime if index_text is not None else None,
    )


def utc_text(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_text_of_mtime(mtime: float) -> str:
    return utc_text(datetime.fromtimestamp(mtime, timezone.utc))


class Journal:
    def __init__(self, root: Path):
        self.root = root
        self.events_path = root / "events.jsonl"
        self.versions_dir = root / "versions"
        self.history_dir = root / "history"
        self.loads_dir = root / "loads"

    @contextmanager
    def locked(self) -> Iterator[None]:
        self.root.mkdir(parents=True, exist_ok=True)
        with open(self.root / ".lock", "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def read_events(self) -> list[Event]:
        if not self.events_path.is_file():
            return []
        lines = read_text_verbatim(self.events_path).splitlines()
        return [Event.from_json_line(line) for line in lines if line.strip()]

    def append(self, events: list[Event]) -> None:
        if not events:
            return
        with open(self.events_path, "a", encoding="utf-8", newline="") as handle:
            handle.write("".join(event.to_json_line() + "\n" for event in events))

    def version_paths(self, file: str, version: int) -> tuple[Path, Path]:
        folder = self.versions_dir / file
        return folder / f"{version}.md", folder / f"{version}.index-line"

    def save_version(self, file: str, version: int, memory: MemoryVersion) -> None:
        content_path, index_line_path = self.version_paths(file, version)
        write_text_verbatim(content_path, memory.content)
        if memory.index_line is None:
            index_line_path.unlink(missing_ok=True)
        else:
            write_text_verbatim(index_line_path, memory.index_line)

    def load_version(self, file: str, version: int) -> MemoryVersion:
        content_path, index_line_path = self.version_paths(file, version)
        index_line = read_text_verbatim(index_line_path) if index_line_path.is_file() else None
        return MemoryVersion(read_text_verbatim(content_path), index_line)


def tracked_files(events: list[Event]) -> dict[str, Tracked]:
    tracked: dict[str, Tracked] = {}
    for event in events:
        if event.kind in VERSION_MAKING_KINDS:
            tracked[event.file] = Tracked(event.version, present=True)
        elif event.kind is EventKind.DELETED:
            tracked[event.file] = Tracked(event.version, present=False)
    return tracked


def sync(memory_dir: Path, journal_dir: Path, trigger: Trigger, now: datetime) -> list[Event]:
    journal = Journal(journal_dir)
    with journal.locked():
        new_events = sync_locked(memory_dir, journal, trigger, now)
        write_histories(journal, {event.file for event in new_events})
    return new_events


def sync_locked(memory_dir: Path, journal: Journal, trigger: Trigger, now: datetime) -> list[Event]:
    folder = read_memory_folder(memory_dir)
    tracked = tracked_files(journal.read_events())
    new_events: list[Event] = []
    for file in sorted(folder.memories.keys() | tracked.keys()):
        event = observe_one(journal, file, folder, tracked.get(file), trigger, now)
        if event is None:
            continue
        if event.kind in VERSION_MAKING_KINDS:
            journal.save_version(file, event.version, folder.memories[file].version)
        new_events.append(event)
    journal.append(new_events)
    return new_events


def observe_one(
    journal: Journal,
    file: str,
    folder: MemoryFolder,
    tracked: Tracked | None,
    trigger: Trigger,
    now: datetime,
) -> Event | None:
    observed = folder.memories.get(file)
    is_tracked_present = tracked is not None and tracked.present
    if observed is not None and not is_tracked_present:
        next_version = tracked.latest_version + 1 if tracked else 1
        return event_for(EventKind.CREATED, file, utc_text_of_mtime(observed.content_mtime),
                         next_version, trigger, observed.version.content)
    if observed is None and is_tracked_present:
        return event_for(EventKind.DELETED, file, utc_text(now), tracked.latest_version, trigger, None)
    if observed is None:
        return None
    previous = journal.load_version(file, tracked.latest_version)
    if previous == observed.version:
        return None
    changed_mtime = observed.content_mtime if previous.content != observed.version.content else folder.index_mtime
    return event_for(EventKind.CHANGED, file, utc_text_of_mtime(changed_mtime),
                     tracked.latest_version + 1, trigger, None)


def event_for(
    kind: EventKind,
    file: str,
    at: str,
    version: int,
    trigger: Trigger,
    created_content: str | None,
) -> Event:
    match trigger:
        case AnswerEnded(session=session, prompt=prompt):
            cause = Cause.PROMPT if prompt is not None else Cause.PROMPT_NOT_FOUND
            return Event(kind, file, at, session, version, cause, prompt)
        case SeenOutsideSession():
            session = origin_session_of(created_content) if created_content is not None else None
            return Event(kind, file, at, session, version, Cause.OUTSIDE_SESSION)


def record_load(
    memory_dir: Path,
    journal_dir: Path,
    session: str,
    now: datetime,
    screen_line_limit: int = SCREEN_MEMORY_LINE_LIMIT,
) -> str:
    journal = Journal(journal_dir)
    with journal.locked():
        folder = read_memory_folder(memory_dir)
        index_text = folder.index_text or ""
        all_lines = index_text.splitlines()
        loaded_line_count = loaded_index_line_count(index_text)
        loaded = unique_by_file(index_entries("\n".join(all_lines[:loaded_line_count])))
        not_loaded = unique_by_file(index_entries("\n".join(all_lines[loaded_line_count:])))
        events = journal.read_events()
        already_recorded = any(e.kind is EventKind.LOADED and e.session == session for e in events)
        if not already_recorded:
            tracked = tracked_files(events)
            load_events = [
                Event(EventKind.LOADED, entry.file, utc_text(now), session,
                      tracked[entry.file].latest_version if entry.file in tracked else None,
                      Cause.SESSION_START)
                for entry in loaded
            ]
            journal.append(load_events)
            write_histories(journal, {event.file for event in load_events})
        full_list_path = journal.loads_dir / f"{session}.md"
        write_text_verbatim(full_list_path, describe_load_in_full(
            session, now, folder.index_text is not None, len(all_lines), loaded_line_count, loaded, not_loaded))
    return describe_load_on_screen(
        folder.index_text is not None, len(all_lines), loaded_line_count, loaded, full_list_path, screen_line_limit)


def unique_by_file(entries: list[IndexEntry]) -> list[IndexEntry]:
    seen: set[str] = set()
    unique = []
    for entry in entries:
        if entry.file not in seen:
            seen.add(entry.file)
            unique.append(entry)
    return unique


def restore(memory_dir: Path, journal_dir: Path, file: str, version: int, now: datetime) -> Event | None:
    journal = Journal(journal_dir)
    with journal.locked():
        captured = sync_locked(memory_dir, journal, SeenOutsideSession(), now)
        tracked = tracked_files(journal.read_events()).get(file)
        if tracked is None:
            raise RestoreError(f"{file}의 판이 기록에 없다.")
        if not 1 <= version <= tracked.latest_version:
            raise RestoreError(f"{file}의 판은 1부터 {tracked.latest_version}까지 있다.")
        wanted = journal.load_version(file, version)
        current = read_memory_folder(memory_dir).memories.get(file)
        if current is not None and current.version == wanted:
            write_histories(journal, {event.file for event in captured})
            return None
        write_text_verbatim(memory_dir / file, wanted.content)
        if wanted.index_line is not None:
            put_index_line(memory_dir / INDEX_FILE_NAME, file, wanted.index_line)
        restored_version = tracked.latest_version + 1
        journal.save_version(file, restored_version, read_memory_folder(memory_dir).memories[file].version)
        event = Event(EventKind.RESTORED, file, utc_text(now), None, restored_version,
                      Cause.RESTORE_COMMAND, restored_from=version)
        journal.append([event])
        write_histories(journal, {e.file for e in captured} | {file})
    return event


def put_index_line(index_path: Path, file: str, index_line: str) -> None:
    lines = read_text_verbatim(index_path).splitlines(keepends=True) if index_path.is_file() else []
    for position, line in enumerate(lines):
        entry = parse_index_entry(line.rstrip("\r\n"))
        if entry is not None and entry.file == file:
            line_ending = line[len(line.rstrip("\r\n")):]
            lines[position] = index_line + line_ending
            break
    else:
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        lines.append(index_line + "\n")
    write_text_verbatim(index_path, "".join(lines))


def rebuild_history(journal_dir: Path) -> None:
    journal = Journal(journal_dir)
    with journal.locked():
        write_histories(journal, {event.file for event in journal.read_events()})


def write_histories(journal: Journal, files: set[str]) -> None:
    if not files:
        return
    events = journal.read_events()
    for file in files:
        own_events = [event for event in events if event.file == file]
        write_text_verbatim(journal.history_dir / file, render_history(journal, file, own_events))


EVENT_LABELS = {
    EventKind.CREATED: "처음 봄",
    EventKind.CHANGED: "바뀜",
    EventKind.DELETED: "지워짐",
    EventKind.RESTORED: "되돌림",
}


def render_history(journal: Journal, file: str, events: list[Event]) -> str:
    changes = [event for event in events if event.kind is not EventKind.LOADED]
    loads = [event for event in events if event.kind is EventKind.LOADED]
    parts = [
        f"# {file}의 내력\n",
        "기억 도구(얹는 제품)가 이 기억 파일에 대해 남긴 기록이다. "
        "기록 폴더의 `events.jsonl`과 `versions/`에서 지었다. 시각은 UTC다.\n",
        render_summary(changes, loads),
        "## 바뀐 차례\n",
    ]
    previous_version: int | None = None
    for event in changes:
        parts.append(render_change(journal, file, event, previous_version))
        if event.kind in VERSION_MAKING_KINDS:
            previous_version = event.version
    parts.append("## 실린 때\n")
    if loads:
        parts.append("\n".join(
            f"- {readable_time(event.at)}, 세션 {event.session}, {version_text(event.version)}"
            for event in loads) + "\n")
    else:
        parts.append("아직 실린 적이 없다.\n")
    return "\n".join(parts)


def render_summary(changes: list[Event], loads: list[Event]) -> str:
    lines = []
    first = changes[0] if changes else None
    if first is not None:
        lines.append(f"- 처음 남은 때: {readable_time(first.at)}, 세션 {session_text(first.session)}")
    edits = [event for event in changes[1:] if event.kind is not EventKind.DELETED]
    if edits:
        lines.append(f"- 바뀐 횟수: {len(edits)}, 마지막은 {readable_time(edits[-1].at)}")
    else:
        lines.append("- 바뀐 횟수: 0")
    if loads:
        lines.append(f"- 실린 횟수: {len(loads)}, 마지막은 {readable_time(loads[-1].at)} 세션 {loads[-1].session}")
    else:
        lines.append("- 실린 횟수: 0")
    last = changes[-1] if changes else None
    if last is not None and last.kind is EventKind.DELETED:
        lines.append(f"- 지금: 지워졌다. 마지막 판은 {last.version}이다")
    elif last is not None:
        lines.append(f"- 지금: 판 {last.version}")
    return "\n".join(lines) + "\n"


def render_change(
    journal: Journal,
    file: str,
    event: Event,
    previous_version: int | None,
) -> str:
    label = EVENT_LABELS[event.kind]
    if event.kind is EventKind.CREATED and previous_version is not None:
        label = "다시 생김"
    heading = f"### {readable_time(event.at)} {label}, {version_text(event.version)}"
    body = [heading, "", f"- 세션: {change_session_text(event)}", f"- 계기: {cause_text(event)}"]
    if event.kind is EventKind.RESTORED:
        body.append(f"- 판 {event.restored_from}의 내용으로 되돌렸다")
    body.append("")
    if event.prompt is not None:
        body.extend(["> " + line for line in event.prompt.splitlines()] + [""])
    if event.kind is EventKind.DELETED:
        return "\n".join(body)
    current = journal.load_version(file, event.version)
    if previous_version is None or event.kind is EventKind.CREATED:
        body.extend(["색인 줄:", "", fenced(current.index_line or "(색인에 줄이 없다)", "text"), "",
                     "파일:", "", fenced(current.content, "markdown"), ""])
    else:
        before = journal.load_version(file, previous_version)
        body.extend(render_difference(before, current, previous_version, event.version))
    return "\n".join(body)


def render_difference(before: MemoryVersion, after: MemoryVersion, before_version: int, after_version: int) -> list[str]:
    lines: list[str] = []
    if before.index_line != after.index_line:
        lines.extend(["색인 줄:", "", fenced(
            f"- {before.index_line or '(색인에 줄이 없다)'}\n+ {after.index_line or '(색인에 줄이 없다)'}", "diff"), ""])
    if before.content != after.content:
        diff = difflib.unified_diff(
            before.content.splitlines(), after.content.splitlines(),
            fromfile=f"판 {before_version}", tofile=f"판 {after_version}", lineterm="", n=1)
        lines.extend(["파일:", "", fenced("\n".join(diff), "diff"), ""])
    return lines


def fenced(text: str, language: str) -> str:
    longest_backtick_run = max((len(run) for run in re.findall(r"`+", text)), default=0)
    fence = "`" * max(3, longest_backtick_run + 1)
    return f"{fence}{language}\n{text.rstrip(chr(10))}\n{fence}"


def readable_time(at: str) -> str:
    return at.replace("T", " ").removesuffix("Z")


def session_text(session: str | None) -> str:
    return session if session is not None else "모름"


def change_session_text(event: Event) -> str:
    if event.cause is Cause.OUTSIDE_SESSION and event.session is not None:
        return f"{event.session} (파일의 originSessionId)"
    if event.cause is Cause.RESTORE_COMMAND:
        return "없음. 사람이 세션 밖에서 부른 명령이다"
    return session_text(event.session)


def version_text(version: int | None) -> str:
    return f"판 {version}" if version is not None else "기록에 판이 없음"


def cause_text(event: Event) -> str:
    match event.cause:
        case Cause.PROMPT:
            return "이 답을 시킨 사람의 말"
        case Cause.PROMPT_NOT_FOUND:
            return "답이 끝날 때 잡았지만, 그 답을 시킨 사람의 말을 찾지 못했다"
        case Cause.OUTSIDE_SESSION:
            return ("세션이 시작할 때 처음 잡혀서 그때의 사람 말을 모른다. 이 도구를 붙이기 전에 있었거나, "
                    "세션 밖에서 바뀌었거나, 답이 끝나기 전에 끊긴 turn에서 바뀐 것이다")
        case Cause.RESTORE_COMMAND:
            return "사람이 부른 되돌리는 명령"
        case Cause.SESSION_START:
            return "세션 시작"


def describe_load_on_screen(
    index_exists: bool,
    total_lines: int,
    loaded_lines: int,
    loaded: list[IndexEntry],
    full_list_path: Path,
    screen_line_limit: int,
) -> str:
    if not index_exists:
        return "실린 기억이 없다. 색인 MEMORY.md가 없다."
    if not loaded:
        return "실린 기억이 없다."
    head = f"기억 {len(loaded)}개가 실렸다."
    if loaded_lines < total_lines:
        head += f" 색인 {total_lines}줄 가운데 앞 {loaded_lines}줄만 실렸다."
    lines = [head] + [f"- {memory_line(entry)}" for entry in loaded[:screen_line_limit]]
    hidden = len(loaded) - screen_line_limit
    if hidden > 0:
        lines.append(f"- 그 밖에 {hidden}개. 전체 목록: {full_list_path}")
    return "\n".join(lines)


def describe_load_in_full(
    session: str,
    now: datetime,
    index_exists: bool,
    total_lines: int,
    loaded_lines: int,
    loaded: list[IndexEntry],
    not_loaded: list[IndexEntry],
) -> str:
    parts = [f"# 세션 {session}에 실린 기억\n"]
    if not index_exists:
        parts.append(f"{readable_time(utc_text(now))}(UTC)에 세션이 시작할 때 색인 MEMORY.md가 없어서 실린 기억이 없다.\n")
        return "\n".join(parts)
    parts.append(
        f"{readable_time(utc_text(now))}(UTC)에 세션이 시작할 때 색인 MEMORY.md {total_lines}줄 가운데 "
        f"앞 {loaded_lines}줄이 실렸다. 실린 기억은 {len(loaded)}개다.\n")
    parts.append("\n".join(f"- {memory_line(entry)} ({entry.file})" for entry in loaded) + "\n" if loaded else "")
    if not_loaded:
        parts.append(f"## 색인이 잘려 실리지 않은 기억 {len(not_loaded)}개\n")
        parts.append("\n".join(f"- {memory_line(entry)} ({entry.file})" for entry in not_loaded) + "\n")
    return "\n".join(part for part in parts if part)


def memory_line(entry: IndexEntry) -> str:
    return f"{entry.title} [{entry.scope}]" if entry.scope else entry.title


def describe_outside_changes(events: list[Event], journal_dir: Path) -> str | None:
    if not events:
        return None
    return f"세션 밖에서 바뀐 기억 {len(events)}개를 기록에 남겼다. 내력: {Journal(journal_dir).history_dir}"


ANSWER_CHANGE_WORDS = {
    EventKind.CREATED: "새로 씀",
    EventKind.CHANGED: "고침",
    EventKind.DELETED: "지움",
}


def describe_answer_changes(events: list[Event], restore_command: str) -> str | None:
    if not events:
        return None
    changed = ", ".join(f"{event.file} {ANSWER_CHANGE_WORDS[event.kind]}" for event in events)
    undo = [undo_command(event, restore_command) for event in events]
    undo = [command for command in undo if command is not None]
    message = f"이번 답에서 기억 {len(events)}개가 바뀌었다: {changed}."
    if undo:
        message += " 되돌리기: " + "; ".join(undo)
    return message


def undo_command(event: Event, restore_command: str) -> str | None:
    match event.kind:
        case EventKind.CHANGED:
            return f"{restore_command} {shlex.quote(event.file)} {event.version - 1}"
        case EventKind.DELETED:
            return f"{restore_command} {shlex.quote(event.file)} {event.version}"
        case _:
            return None
