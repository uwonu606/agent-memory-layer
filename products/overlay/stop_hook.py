from __future__ import annotations

import time

HOOK_STARTED = time.perf_counter()

import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from claude_code import (
    SHOW_COST_FLAG,
    UNCOUNTED_IN_FULL,
    Place,
    cost_failure_message,
    emit_hook_output,
    failure_message,
    joined_lines,
    last_user_prompt,
    locate,
    old_value_failure_message,
    read_answer_usage,
    read_hook_input,
    restore_command,
)
from cost_tally import (
    CostBook,
    answer_end_record,
    describe_answer_cost,
    elapsed_ms,
    last_counted_message_id,
    last_transcript_offset,
)
from memory_journal import AnswerEnded, describe_answer_changes, sync
from old_values import find_old_value_mentions, old_value_notice

FIND_OLD_VALUES_FLAG = "--find-old-values"


@dataclass(frozen=True)
class StopOutput:
    screen_message: str | None
    model_feedback: str | None = None


def transcript_path_of(hook_input: dict[str, Any]) -> Path | None:
    transcript = hook_input.get("transcript_path")
    return Path(transcript).expanduser() if transcript else None


def stop_output(hook_input: dict[str, Any], place: Place, find_old_values: bool) -> StopOutput:
    transcript = transcript_path_of(hook_input)
    prompt = last_user_prompt(transcript) if transcript else None
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


def answer_cost_line(place: Place, hook_input: dict[str, Any], notice_chars: int) -> str | None:
    session = hook_input["session_id"]
    book = CostBook(place.journal_dir, UNCOUNTED_IN_FULL)
    records = book.read(session)
    transcript = read_answer_usage(transcript_path_of(hook_input), last_transcript_offset(records), place.memory_dir,
                                   last_counted_message_id(records))
    record = answer_end_record(records, datetime.now(timezone.utc), transcript.next_offset, transcript.answer,
                               notice_chars, bool(hook_input.get("stop_hook_active")), elapsed_ms(HOOK_STARTED))
    book.append(session, record, answer_ended=True)
    return describe_answer_cost(record, book.summary_path(session))


def main() -> None:
    arguments = sys.argv[1:]
    try:
        hook_input = read_hook_input(sys.stdin)
        place = locate(Path(hook_input.get("cwd") or os.getcwd()), os.environ)
    except Exception as error:
        emit_hook_output(failure_message(error))
        return
    try:
        output = stop_output(hook_input, place, FIND_OLD_VALUES_FLAG in arguments)
    except Exception as error:
        output = StopOutput(failure_message(error))
    if SHOW_COST_FLAG in arguments:
        try:
            cost_line = answer_cost_line(place, hook_input, len(output.model_feedback or ""))
        except Exception as error:
            cost_line = cost_failure_message(error)
        output = StopOutput(joined_lines(output.screen_message, cost_line) or None, output.model_feedback)
    emit_hook_output(output.screen_message, output.model_feedback)


if __name__ == "__main__":
    main()
