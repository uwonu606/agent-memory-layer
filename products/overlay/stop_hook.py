from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from claude_code import (
    emit_hook_output,
    failure_message,
    last_user_prompt,
    locate,
    old_value_failure_message,
    read_hook_input,
    restore_command,
)
from memory_journal import AnswerEnded, describe_answer_changes, sync
from old_values import find_old_value_mentions, old_value_notice

FIND_OLD_VALUES_FLAG = "--find-old-values"


@dataclass(frozen=True)
class StopOutput:
    screen_message: str | None
    model_feedback: str | None = None


def stop_output(hook_input: dict[str, Any], env: Mapping[str, str], find_old_values: bool) -> StopOutput:
    place = locate(Path(hook_input.get("cwd") or os.getcwd()), env)
    transcript = hook_input.get("transcript_path")
    prompt = last_user_prompt(Path(transcript).expanduser()) if transcript else None
    trigger = AnswerEnded(session=hook_input["session_id"], prompt=prompt)
    changes = sync(place.memory_dir, place.journal_dir, trigger, datetime.now(timezone.utc))
    changes_line = describe_answer_changes(changes, restore_command())
    if not find_old_values or hook_input.get("stop_hook_active"):
        return StopOutput(changes_line)
    try:
        notice = old_value_notice(find_old_value_mentions(place.memory_dir, place.journal_dir, changes))
    except Exception as error:
        return StopOutput(joined_lines(changes_line, old_value_failure_message(error)))
    if notice is None:
        return StopOutput(changes_line)
    return StopOutput(joined_lines(changes_line, notice.screen_line), notice.model_text)


def joined_lines(*lines: str | None) -> str:
    return "\n".join(line for line in lines if line)


def main() -> None:
    find_old_values = FIND_OLD_VALUES_FLAG in sys.argv[1:]
    try:
        output = stop_output(read_hook_input(sys.stdin), os.environ, find_old_values)
    except Exception as error:
        output = StopOutput(failure_message(error))
    emit_hook_output(output.screen_message, output.model_feedback)


if __name__ == "__main__":
    main()
