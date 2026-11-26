from __future__ import annotations

import time

HOOK_STARTED = time.perf_counter()

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from claude_code import (
    SHOW_COST_FLAG,
    UNCOUNTED_IN_FULL,
    UNCOUNTED_ON_SCREEN,
    Place,
    cost_failure_message,
    emit_hook_output,
    failure_message,
    instructions_text,
    joined_lines,
    locate,
    memory_rules_text,
    read_hook_input,
)
from cost_tally import (
    CostBook,
    describe_loaded_text,
    describe_previous_session,
    elapsed_ms,
    measure_loaded_text,
    session_start_record,
)
from memory_journal import SeenOutsideSession, describe_outside_changes, record_load, sync


def screen_message(place: Place, session: str) -> str:
    now = datetime.now(timezone.utc)
    outside_changes = sync(place.memory_dir, place.journal_dir, SeenOutsideSession(), now)
    loaded = record_load(place.memory_dir, place.journal_dir, session, now)
    outside_note = describe_outside_changes(outside_changes, place.journal_dir)
    return "\n".join(part for part in (loaded, outside_note) if part)


def cost_lines(place: Place, hook_input: dict[str, Any], env: Mapping[str, str]) -> str:
    session = hook_input["session_id"]
    book = CostBook(place.journal_dir, UNCOUNTED_IN_FULL)
    previous = describe_previous_session(book, session)
    loaded = measure_loaded_text(place.memory_dir, memory_rules_text(), instructions_text(Path(env["HOME"])))
    hook_ms = elapsed_ms(HOOK_STARTED)
    book.append(session, session_start_record(datetime.now(timezone.utc), hook_input.get("source"), loaded, hook_ms))
    return joined_lines(describe_loaded_text(loaded, hook_ms, UNCOUNTED_ON_SCREEN), previous)


def main() -> None:
    show_cost = SHOW_COST_FLAG in sys.argv[1:]
    try:
        hook_input = read_hook_input(sys.stdin)
        place = locate(Path(hook_input.get("cwd") or os.getcwd()), os.environ)
    except Exception as error:
        emit_hook_output(failure_message(error))
        return
    try:
        message = screen_message(place, hook_input["session_id"])
    except Exception as error:
        message = failure_message(error)
    if show_cost:
        try:
            message = joined_lines(message, cost_lines(place, hook_input, os.environ))
        except Exception as error:
            message = joined_lines(message, cost_failure_message(error))
    emit_hook_output(message)


if __name__ == "__main__":
    main()
