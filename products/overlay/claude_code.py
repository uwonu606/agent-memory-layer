from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, TextIO

JOURNAL_DIR_ENV = "AML_OVERLAY_JOURNAL_DIR"
TRANSCRIPT_TAIL_BYTES = 1 << 20
RESTORE_SCRIPT = Path(__file__).resolve().parent / "restore.py"


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


def restore_command() -> str:
    return f"python3 {shlex.quote(str(RESTORE_SCRIPT))}"


def read_hook_input(stdin: TextIO) -> dict[str, Any]:
    return json.loads(stdin.read())


def failure_message(error: Exception) -> str:
    return f"기억 기록이 실패했다. 일은 그대로 이어진다. ({type(error).__name__}: {error})"


def old_value_failure_message(error: Exception) -> str:
    return f"옛 값 찾기가 실패했다. 기억 기록은 남았고 일은 그대로 이어진다. ({type(error).__name__}: {error})"


def emit_hook_output(screen_message: str | None, stop_feedback: str | None = None) -> None:
    payload: dict[str, Any] = {"systemMessage": screen_message} if screen_message else {}
    if stop_feedback:
        payload["hookSpecificOutput"] = {"hookEventName": "Stop", "additionalContext": stop_feedback}
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
