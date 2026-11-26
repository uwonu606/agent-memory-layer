from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import Any, Iterator, Mapping, TextIO

from cost_tally import USAGE_FIELDS, AnswerUsage, CallTally, MemoryCalls

JOURNAL_DIR_ENV = "AML_OVERLAY_JOURNAL_DIR"
TRANSCRIPT_TAIL_BYTES = 1 << 20
PRODUCT_DIR = Path(__file__).resolve().parent
RESTORE_SCRIPT = PRODUCT_DIR / "restore.py"
MEMORY_RULES_PATH = PRODUCT_DIR / "memory-rules.md"
SHOW_COST_FLAG = "--show-cost"
FILE_PATH_TOOLS = {"Read": "read", "Write": "write", "Edit": "write", "MultiEdit": "write"}
SEARCH_PATH_TOOLS = {"Grep", "Glob"}
PRODUCT_HOOK_ATTACHMENTS = {"hook_success", "hook_non_blocking_error"}
UNCOUNTED_ON_SCREEN = "Claude Code가 붙이는 기억 지시와 잘림 경고는 세지 않았다."
UNCOUNTED_IN_FULL = (
    "Claude Code가 system prompt에 넣는 기억 지시(`# Memory` 절)",
    "색인 앞에 붙는 머리 줄과, 색인이 잘렸을 때 붙는 경고",
    "hook 안에서 잰 시간에 들지 않는, Python이 뜨는 시간. Claude Code가 잰 hook 시간에는 든다",
    "구독의 사용 한도에 얼마로 잡히는지",
    "`~`나 상대 경로, 변수로 기억 폴더를 부른 shell 호출과, 기억 폴더 밖의 경로로 들어간 호출(링크 따위)",
)


@dataclass(frozen=True)
class Place:
    memory_dir: Path
    journal_dir: Path


def locate(cwd: Path, env: Mapping[str, str]) -> Place:
    home = Path(env["HOME"])
    memory_dir = configured_memory_dir(home) or default_memory_dir(home, cwd)
    return place_for(memory_dir, env)


def place_for(memory_dir: Path, env: Mapping[str, str]) -> Place:
    override = env.get(JOURNAL_DIR_ENV)
    journal_dir = Path(override) if override else memory_dir.parent / f"{memory_dir.name}-journal"
    return Place(memory_dir, journal_dir)


def configured_memory_dir(home: Path) -> Path | None:
    settings_path = home / ".claude" / "settings.json"
    if not settings_path.is_file():
        return None
    configured = json.loads(settings_path.read_text(encoding="utf-8")).get("autoMemoryDirectory")
    if not configured:
        return None
    if configured == "~":
        return home
    if configured.startswith("~/"):
        return home / configured[2:]
    return Path(configured)


def default_memory_dir(home: Path, cwd: Path) -> Path:
    project_name = re.sub(r"[^A-Za-z0-9]", "-", str(repository_root(cwd)))
    return home / ".claude" / "projects" / project_name / "memory"


def repository_root(cwd: Path) -> Path:
    toplevel = git_output(cwd, "rev-parse", "--show-toplevel")
    if toplevel is None:
        return cwd
    common_dir = git_output(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if common_dir is not None and Path(common_dir).name == ".git":
        return Path(common_dir).parent
    return Path(toplevel)


def git_output(cwd: Path, *args: str) -> str | None:
    try:
        completed = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return completed.stdout.strip() if completed.returncode == 0 else None


def last_user_prompt(transcript_path: Path) -> str | None:
    if not transcript_path.is_file():
        return None
    size = transcript_path.stat().st_size
    for window in (TRANSCRIPT_TAIL_BYTES, size):
        start = max(0, size - window)
        with open(transcript_path, "rb") as handle:
            handle.seek(start)
            lines = handle.read().decode("utf-8", errors="replace").splitlines()
        if start > 0:
            lines = lines[1:]
        for line in reversed(lines):
            prompt = prompt_text(line)
            if prompt is not None:
                return prompt
        if start == 0:
            return None
    return None


def prompt_text(transcript_line: str) -> str | None:
    try:
        entry = json.loads(transcript_line)
    except json.JSONDecodeError:
        return None
    if not isinstance(entry, dict) or entry.get("type") != "user":
        return None
    if entry.get("isMeta") or entry.get("isCompactSummary") or entry.get("isSidechain"):
        return None
    message = entry.get("message")
    if not isinstance(message, dict) or message.get("role") != "user":
        return None
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = [block.get("text", "") for block in content
                 if isinstance(block, dict) and block.get("type") == "text"]
        return "\n".join(texts) if texts else None
    return None


def instructions_text(home: Path) -> str | None:
    path = home / ".claude" / "CLAUDE.md"
    return path.read_text(encoding="utf-8") if path.is_file() else None


def memory_rules_text() -> str:
    return MEMORY_RULES_PATH.read_text(encoding="utf-8")


@dataclass(frozen=True)
class TranscriptSlice:
    answer: AnswerUsage | None
    next_offset: int


def read_answer_usage(transcript_path: Path | None, offset: int, memory_dir: Path) -> TranscriptSlice:
    if transcript_path is None or not transcript_path.is_file():
        return TranscriptSlice(None, offset)
    lines, next_offset = complete_lines_from(transcript_path, offset)
    return TranscriptSlice(answer_usage(transcript_entries(lines), MemoryFolderMatcher(memory_dir)), next_offset)


def complete_lines_from(path: Path, offset: int) -> tuple[list[str], int]:
    start = offset if offset <= path.stat().st_size else 0
    with open(path, "rb") as handle:
        handle.seek(start)
        data = handle.read()
    complete_end = data.rfind(b"\n") + 1
    return data[:complete_end].decode("utf-8", errors="replace").splitlines(), start + complete_end


def transcript_entries(lines: list[str]) -> Iterator[dict[str, Any]]:
    for line in lines:
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(entry, dict):
            yield entry


class MemoryFolderMatcher:
    def __init__(self, memory_dir: Path):
        roots = {os.path.normpath(str(memory_dir)), os.path.realpath(str(memory_dir))}
        self.roots = [PurePath(root) for root in roots]
        self.mentions = [re.compile(re.escape(root) + r"(?![A-Za-z0-9._-])") for root in roots]

    def holds(self, path_text: object) -> bool:
        if not isinstance(path_text, str) or not os.path.isabs(path_text):
            return False
        path = PurePath(os.path.normpath(path_text))
        return any(path.is_relative_to(root) for root in self.roots)

    def mentioned_in(self, command: object) -> bool:
        return isinstance(command, str) and any(pattern.search(command) for pattern in self.mentions)

    def call_kind(self, block: dict[str, Any]) -> str | None:
        name = block.get("name")
        tool_input = block.get("input")
        if not isinstance(tool_input, dict):
            return None
        if name in FILE_PATH_TOOLS:
            return FILE_PATH_TOOLS[name] if self.holds(tool_input.get("file_path")) else None
        if name in SEARCH_PATH_TOOLS:
            return "read" if self.holds(tool_input.get("path")) else None
        if name == "Bash":
            return "read" if self.mentioned_in(tool_input.get("command")) else None
        return None


def answer_usage(entries: Iterator[dict[str, Any]], memory_folder: MemoryFolderMatcher) -> AnswerUsage:
    usage_by_message: dict[str, dict[str, Any]] = {}
    query_sources: Counter[str] = Counter()
    memory_call_kinds: dict[str, str] = {}
    result_chars: dict[str, int] = {}
    hook_ms: list[int] = []
    for entry in entries:
        kind = entry.get("type")
        if kind == "assistant" and not entry.get("isSidechain"):
            message = entry.get("message")
            if not isinstance(message, dict):
                continue
            message_id = message.get("id")
            if isinstance(message_id, str):
                usage = message.get("usage")
                usage_by_message[message_id] = usage if isinstance(usage, dict) else {}
            for block in content_blocks(message):
                if block.get("type") == "tool_use" and isinstance(block.get("id"), str):
                    call_kind = memory_folder.call_kind(block)
                    if call_kind is not None:
                        memory_call_kinds[block["id"]] = call_kind
        elif kind == "user":
            message = entry.get("message")
            for block in content_blocks(message) if isinstance(message, dict) else ():
                if block.get("type") == "tool_result" and isinstance(block.get("tool_use_id"), str):
                    result_chars[block["tool_use_id"]] = tool_result_length(block.get("content"))
        elif kind == "api-request":
            source = entry.get("querySource")
            if isinstance(source, str):
                query_sources[source] += 1
        elif kind == "attachment":
            duration = product_hook_duration(entry.get("attachment"))
            if duration is not None:
                hook_ms.append(duration)
    return AnswerUsage(
        requests=len(usage_by_message),
        usage={name: sum(token_count(usage.get(name)) for usage in usage_by_message.values()) for name in USAGE_FIELDS},
        query_sources=dict(query_sources),
        memory_calls=memory_calls_of(memory_call_kinds, result_chars),
        harness_hook_ms=hook_ms,
    )


def content_blocks(message: dict[str, Any]) -> list[dict[str, Any]]:
    content = message.get("content")
    return [block for block in content if isinstance(block, dict)] if isinstance(content, list) else []


def tool_result_length(content: object) -> int:
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        return sum(len(block.get("text", "")) for block in content
                   if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str))
    return 0


def token_count(value: object) -> int:
    return value if isinstance(value, int) else 0


def product_hook_duration(attachment: object) -> int | None:
    if not isinstance(attachment, dict) or attachment.get("type") not in PRODUCT_HOOK_ATTACHMENTS:
        return None
    command = attachment.get("command")
    duration = attachment.get("durationMs")
    if not isinstance(command, str) or str(PRODUCT_DIR) not in command or not isinstance(duration, int):
        return None
    return duration


def memory_calls_of(call_kinds: dict[str, str], result_chars: dict[str, int]) -> MemoryCalls:
    tallies = {"read": CallTally(), "write": CallTally()}
    for tool_use_id, call_kind in call_kinds.items():
        tallies[call_kind] = tallies[call_kind].plus(CallTally(1, result_chars.get(tool_use_id, 0)))
    return MemoryCalls(tallies["read"], tallies["write"])


def restore_command() -> str:
    return f"python3 {shlex.quote(str(RESTORE_SCRIPT))}"


def read_hook_input(stdin: TextIO) -> dict[str, Any]:
    return json.loads(stdin.read())


def failure_message(error: Exception) -> str:
    return f"기억 기록이 실패했다. 일은 그대로 이어진다. ({type(error).__name__}: {error})"


def old_value_failure_message(error: Exception) -> str:
    return f"옛 값 찾기가 실패했다. 기억 기록은 남았고 일은 그대로 이어진다. ({type(error).__name__}: {error})"


def cost_failure_message(error: Exception) -> str:
    return f"쓴 양 세기가 실패했다. 기억 기록은 남았고 일은 그대로 이어진다. ({type(error).__name__}: {error})"


def joined_lines(*lines: str | None) -> str:
    return "\n".join(line for line in lines if line)


def emit_hook_output(screen_message: str | None, stop_feedback: str | None = None) -> None:
    payload: dict[str, Any] = {"systemMessage": screen_message} if screen_message else {}
    if stop_feedback:
        payload["hookSpecificOutput"] = {"hookEventName": "Stop", "additionalContext": stop_feedback}
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
