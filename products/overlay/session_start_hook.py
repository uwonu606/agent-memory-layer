from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from claude_code import emit_hook_output, failure_message, locate, read_hook_input
from memory_journal import SeenOutsideSession, describe_outside_changes, record_load, sync


def screen_message(hook_input: dict[str, Any], env: Mapping[str, str]) -> str:
    place = locate(Path(hook_input.get("cwd") or os.getcwd()), env)
    now = datetime.now(timezone.utc)
    outside_changes = sync(place.memory_dir, place.journal_dir, SeenOutsideSession(), now)
    loaded = record_load(place.memory_dir, place.journal_dir, hook_input["session_id"], now)
    outside_note = describe_outside_changes(outside_changes, place.journal_dir)
    return "\n".join(part for part in (loaded, outside_note) if part)


def main() -> None:
    try:
        message = screen_message(read_hook_input(sys.stdin), os.environ)
    except Exception as error:
        message = failure_message(error)
    emit_hook_output(message)


if __name__ == "__main__":
    main()
