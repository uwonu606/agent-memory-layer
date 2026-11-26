from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from memory_journal import (
    AnswerEnded,
    Cause,
    Event,
    EventKind,
    RestoreError,
    SeenOutsideSession,
    describe_answer_changes,
    rebuild_history,
    record_load,
    restore,
    sync,
)

NOW = datetime(2026, 11, 25, 9, 0, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 11, 25, 10, 0, 0, tzinfo=timezone.utc)
MTIME_FIRST = datetime(2026, 11, 20, 1, 2, 3, tzinfo=timezone.utc).timestamp()
MTIME_EDIT = datetime(2026, 11, 25, 9, 30, 0, tzinfo=timezone.utc).timestamp()

COMMIT_UNIT = """---
name: 커밋 단위
metadata:
  type: feedback
  originSessionId: s-old
---
커밋은 ticket 하나에 하나로 올린다.
"""
UV = """---
name: uv
---
uv를 쓴다.
"""
INDEX = (
    "- [커밋 단위](commit-unit.md) — [todo-app] ticket 하나에 하나\n"
    "- [uv를 쓴다](uv.md) — [everywhere] 파이썬 패키지는 uv로\n"
)


class MemoryFolderCase(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        self.memory = self.root / "memory"
        self.journal = self.root / "memory-journal"
        self.memory.mkdir()

    def write(self, name: str, text: str, mtime: float = MTIME_FIRST) -> None:
        path = self.memory / name
        path.write_text(text, encoding="utf-8")
        os.utime(path, (mtime, mtime))

    def write_two_memories(self) -> None:
        self.write("MEMORY.md", INDEX)
        self.write("commit-unit.md", COMMIT_UNIT)
        self.write("uv.md", UV)

    def events(self) -> list[dict]:
        lines = (self.journal / "events.jsonl").read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines]

    def history(self, name: str) -> str:
        return (self.journal / "history" / name).read_text(encoding="utf-8")


class SyncTest(MemoryFolderCase):
    def test_first_sync_records_existing_memories_as_seen_outside_session(self) -> None:
        self.write_two_memories()

        sync(self.memory, self.journal, SeenOutsideSession(), NOW)

        self.assertEqual(self.events(), [
            {"event": "created", "file": "commit-unit.md", "at": "2026-11-20T01:02:03Z", "session": "s-old",
             "version": 1, "cause": "outside_session", "prompt": None},
            {"event": "created", "file": "uv.md", "at": "2026-11-20T01:02:03Z", "session": None,
             "version": 1, "cause": "outside_session", "prompt": None},
        ])
        self.assertEqual((self.journal / "versions/commit-unit.md/1.md").read_text(encoding="utf-8"), COMMIT_UNIT)
        self.assertEqual((self.journal / "versions/commit-unit.md/1.index-line").read_text(encoding="utf-8"),
                         "- [커밋 단위](commit-unit.md) — [todo-app] ticket 하나에 하나")

    def test_second_sync_without_changes_adds_nothing(self) -> None:
        self.write_two_memories()
        sync(self.memory, self.journal, SeenOutsideSession(), NOW)
        before = (self.journal / "events.jsonl").read_text(encoding="utf-8")

        again = sync(self.memory, self.journal, AnswerEnded("s1", "아무 말"), LATER)

        self.assertEqual(again, [])
        self.assertEqual((self.journal / "events.jsonl").read_text(encoding="utf-8"), before)

    def test_change_at_answer_end_records_the_prompt_and_the_file_mtime(self) -> None:
        self.write_two_memories()
        sync(self.memory, self.journal, SeenOutsideSession(), NOW)
        self.write("commit-unit.md", COMMIT_UNIT.replace("ticket", "기능"), MTIME_EDIT)

        changes = sync(self.memory, self.journal, AnswerEnded("s1", "커밋은 이제 기능 하나에 하나다, 고쳐"), LATER)

        self.assertEqual(changes, [Event(EventKind.CHANGED, "commit-unit.md", "2026-11-25T09:30:00Z", "s1", 2,
                                         Cause.PROMPT, "커밋은 이제 기능 하나에 하나다, 고쳐")])
        self.assertEqual((self.journal / "versions/commit-unit.md/2.md").read_text(encoding="utf-8"),
                         COMMIT_UNIT.replace("ticket", "기능"))

    def test_index_line_change_alone_is_a_change_timed_by_the_index(self) -> None:
        self.write_two_memories()
        sync(self.memory, self.journal, SeenOutsideSession(), NOW)
        self.write("MEMORY.md", INDEX.replace("[everywhere]", "[todo-app]"), MTIME_EDIT)

        changes = sync(self.memory, self.journal, AnswerEnded("s1", None), LATER)

        self.assertEqual(changes, [Event(EventKind.CHANGED, "uv.md", "2026-11-25T09:30:00Z", "s1", 2,
                                         Cause.PROMPT_NOT_FOUND, None)])

    def test_remove_and_rewrite_under_a_new_name_is_a_deletion_and_a_creation(self) -> None:
        self.write_two_memories()
        sync(self.memory, self.journal, SeenOutsideSession(), NOW)
        (self.memory / "commit-unit.md").unlink()
        self.write("commit-rule.md", COMMIT_UNIT.replace("ticket", "기능"), MTIME_EDIT)

        changes = sync(self.memory, self.journal, AnswerEnded("s1", "고쳐"), LATER)

        self.assertEqual(changes, [
            Event(EventKind.CREATED, "commit-rule.md", "2026-11-25T09:30:00Z", "s1", 1, Cause.PROMPT, "고쳐"),
            Event(EventKind.DELETED, "commit-unit.md", "2026-11-25T10:00:00Z", "s1", 1, Cause.PROMPT, "고쳐"),
        ])

    def test_change_seen_at_session_start_has_no_session(self) -> None:
        self.write_two_memories()
        sync(self.memory, self.journal, SeenOutsideSession(), NOW)
        self.write("commit-unit.md", COMMIT_UNIT.replace("ticket", "기능"), MTIME_EDIT)

        changes = sync(self.memory, self.journal, SeenOutsideSession(), LATER)

        self.assertEqual(changes, [Event(EventKind.CHANGED, "commit-unit.md", "2026-11-25T09:30:00Z", None, 2,
                                         Cause.OUTSIDE_SESSION)])

    def test_version_left_behind_by_a_crash_is_overwritten(self) -> None:
        self.write_two_memories()
        orphan = self.journal / "versions/uv.md/1.md"
        orphan.parent.mkdir(parents=True)
        orphan.write_text("반쯤 쓰다 멈춘 판", encoding="utf-8")

        sync(self.memory, self.journal, SeenOutsideSession(), NOW)

        self.assertEqual(orphan.read_text(encoding="utf-8"), UV)
        self.assertEqual([(e["event"], e["file"], e["version"]) for e in self.events()],
                         [("created", "commit-unit.md", 1), ("created", "uv.md", 1)])


class HistoryTest(MemoryFolderCase):
    def test_history_tells_first_write_change_and_loads(self) -> None:
        self.write_two_memories()
        sync(self.memory, self.journal, SeenOutsideSession(), NOW)
        record_load(self.memory, self.journal, "s1", NOW)
        self.write("commit-unit.md", COMMIT_UNIT.replace("ticket", "기능"), MTIME_EDIT)
        sync(self.memory, self.journal, AnswerEnded("s1", "커밋은 이제 기능 하나에 하나다, 고쳐"), LATER)

        self.assertEqual(self.history("commit-unit.md"), """# commit-unit.md의 내력

기억 도구(얹는 제품)가 이 기억 파일에 대해 남긴 기록이다. 기록 폴더의 `events.jsonl`과 `versions/`에서 지었다. 시각은 UTC다.

- 처음 남은 때: 2026-11-20 01:02:03, 세션 s-old
- 바뀐 횟수: 1, 마지막은 2026-11-25 09:30:00
- 실린 횟수: 1, 마지막은 2026-11-25 09:00:00 세션 s1
- 지금: 판 2

## 바뀐 차례

### 2026-11-20 01:02:03 처음 봄, 판 1

- 세션: s-old (파일의 originSessionId)
- 계기: 세션이 시작할 때 처음 잡혀서 그때의 사람 말을 모른다. 이 도구를 붙이기 전에 있었거나, 세션 밖에서 바뀌었거나, 답이 끝나기 전에 끊긴 turn에서 바뀐 것이다

색인 줄:

```text
- [커밋 단위](commit-unit.md) — [todo-app] ticket 하나에 하나
```

파일:

```markdown
---
name: 커밋 단위
metadata:
  type: feedback
  originSessionId: s-old
---
커밋은 ticket 하나에 하나로 올린다.
```

### 2026-11-25 09:30:00 바뀜, 판 2

- 세션: s1
- 계기: 이 답을 시킨 사람의 말

> 커밋은 이제 기능 하나에 하나다, 고쳐

파일:

```diff
--- 판 1
+++ 판 2
@@ -6,2 +6,2 @@
 ---
-커밋은 ticket 하나에 하나로 올린다.
+커밋은 기능 하나에 하나로 올린다.
```

## 실린 때

- 2026-11-25 09:00:00, 세션 s1, 판 1
""")

    def test_rebuilt_history_matches_the_written_one(self) -> None:
        self.write_two_memories()
        sync(self.memory, self.journal, SeenOutsideSession(), NOW)
        record_load(self.memory, self.journal, "s1", NOW)
        self.write("commit-unit.md", COMMIT_UNIT.replace("ticket", "기능"), MTIME_EDIT)
        sync(self.memory, self.journal, AnswerEnded("s1", "고쳐"), LATER)
        written = self.history("commit-unit.md")
        shutil.rmtree(self.journal / "history")

        rebuild_history(self.journal)

        self.assertEqual(self.history("commit-unit.md"), written)


class RecordLoadTest(MemoryFolderCase):
    def test_screen_lists_loaded_memories_with_scope(self) -> None:
        self.write_two_memories()

        screen = record_load(self.memory, self.journal, "s1", NOW)

        self.assertEqual(screen, "기억 2개가 실렸다.\n- 커밋 단위 [todo-app]\n- uv를 쓴다 [everywhere]")
        self.assertEqual([(e["event"], e["file"], e["session"], e["version"]) for e in self.events()],
                         [("loaded", "commit-unit.md", "s1", None), ("loaded", "uv.md", "s1", None)])

    def test_index_cut_at_200_lines_is_announced_and_long_list_is_folded(self) -> None:
        self.write("MEMORY.md", "".join(f"- [기억 {n}](m{n}.md) — [todo-app] 설명\n" for n in range(1, 251)))

        screen = record_load(self.memory, self.journal, "s1", NOW, screen_line_limit=3)

        full_list = self.journal / "loads" / "s1.md"
        self.assertEqual(screen, (
            "기억 200개가 실렸다. 색인 250줄 가운데 앞 200줄만 실렸다.\n"
            "- 기억 1 [todo-app]\n- 기억 2 [todo-app]\n- 기억 3 [todo-app]\n"
            f"- 그 밖에 197개. 전체 목록: {full_list}"))
        self.assertEqual(len(self.events()), 200)
        full_text = full_list.read_text(encoding="utf-8")
        self.assertIn("- 기억 200 [todo-app] (m200.md)\n\n## 색인이 잘려 실리지 않은 기억 50개\n\n- 기억 201 [todo-app] (m201.md)",
                      full_text)

    def test_index_cut_by_the_character_limit(self) -> None:
        long_line = "- [긴 기억 {n}](long{n}.md) — " + "가" * 990 + "\n"
        self.write("MEMORY.md", "".join(long_line.replace("{n}", str(n)) for n in range(1, 31)))

        screen = record_load(self.memory, self.journal, "s1", NOW, screen_line_limit=0)

        self.assertEqual(screen, (
            "기억 24개가 실렸다. 색인 30줄 가운데 앞 24줄만 실렸다.\n"
            f"- 그 밖에 24개. 전체 목록: {self.journal / 'loads' / 's1.md'}"))

    def test_same_session_is_recorded_once(self) -> None:
        self.write_two_memories()
        record_load(self.memory, self.journal, "s1", NOW)

        screen = record_load(self.memory, self.journal, "s1", LATER)

        self.assertEqual(screen, "기억 2개가 실렸다.\n- 커밋 단위 [todo-app]\n- uv를 쓴다 [everywhere]")
        self.assertEqual(len(self.events()), 2)

    def test_missing_index_says_nothing_was_loaded(self) -> None:
        self.assertEqual(record_load(self.memory, self.journal, "s1", NOW),
                         "실린 기억이 없다. 색인 MEMORY.md가 없다.")


class RestoreTest(MemoryFolderCase):
    def test_restore_brings_back_a_removed_memory_and_its_index_line(self) -> None:
        self.write_two_memories()
        sync(self.memory, self.journal, SeenOutsideSession(), NOW)
        (self.memory / "commit-unit.md").unlink()
        self.write("MEMORY.md", "- [uv를 쓴다](uv.md) — [everywhere] 파이썬 패키지는 uv로\n")
        sync(self.memory, self.journal, AnswerEnded("s1", "커밋 규칙은 지워"), NOW)

        event = restore(self.memory, self.journal, "commit-unit.md", 1, LATER)

        self.assertEqual(event, Event(EventKind.RESTORED, "commit-unit.md", "2026-11-25T10:00:00Z", None, 2,
                                      Cause.RESTORE_COMMAND, restored_from=1))
        self.assertEqual((self.memory / "commit-unit.md").read_text(encoding="utf-8"), COMMIT_UNIT)
        self.assertEqual((self.memory / "MEMORY.md").read_text(encoding="utf-8"),
                         "- [uv를 쓴다](uv.md) — [everywhere] 파이썬 패키지는 uv로\n"
                         "- [커밋 단위](commit-unit.md) — [todo-app] ticket 하나에 하나\n")
        self.assertEqual(sync(self.memory, self.journal, AnswerEnded("s1", "다음 말"), LATER), [])

    def test_restore_replaces_the_changed_index_line_in_place(self) -> None:
        self.write_two_memories()
        sync(self.memory, self.journal, SeenOutsideSession(), NOW)
        self.write("MEMORY.md", INDEX.replace("ticket 하나에 하나", "기능 하나에 하나"), MTIME_EDIT)
        self.write("commit-unit.md", COMMIT_UNIT.replace("ticket", "기능"), MTIME_EDIT)

        restore(self.memory, self.journal, "commit-unit.md", 1, LATER)

        self.assertEqual((self.memory / "MEMORY.md").read_text(encoding="utf-8"), INDEX)
        self.assertEqual([(e["event"], e["file"], e["version"], e.get("restored_from")) for e in self.events()], [
            ("created", "commit-unit.md", 1, None),
            ("created", "uv.md", 1, None),
            ("changed", "commit-unit.md", 2, None),
            ("restored", "commit-unit.md", 3, 1),
        ])

    def test_restore_to_the_current_content_changes_nothing(self) -> None:
        self.write_two_memories()
        sync(self.memory, self.journal, SeenOutsideSession(), NOW)

        self.assertIsNone(restore(self.memory, self.journal, "uv.md", 1, LATER))
        self.assertEqual(len(self.events()), 2)

    def test_restore_rejects_unknown_file_and_version(self) -> None:
        self.write_two_memories()
        sync(self.memory, self.journal, SeenOutsideSession(), NOW)

        with self.assertRaises(RestoreError) as unknown:
            restore(self.memory, self.journal, "nothing.md", 1, LATER)
        with self.assertRaises(RestoreError) as out_of_range:
            restore(self.memory, self.journal, "uv.md", 5, LATER)

        self.assertEqual(str(unknown.exception), "nothing.md의 판이 기록에 없다.")
        self.assertEqual(str(out_of_range.exception), "uv.md의 판은 1부터 1까지 있다.")


class DescribeAnswerChangesTest(unittest.TestCase):
    def test_one_line_with_undo_commands(self) -> None:
        events = [
            Event(EventKind.CHANGED, "commit-unit.md", "t", "s1", 3, Cause.PROMPT, "고쳐"),
            Event(EventKind.CREATED, "pr-language.md", "t", "s1", 1, Cause.PROMPT, "고쳐"),
            Event(EventKind.DELETED, "old note.md", "t", "s1", 2, Cause.PROMPT, "고쳐"),
        ]

        self.assertEqual(describe_answer_changes(events, "python3 /x/restore.py"), (
            "이번 답에서 기억 3개가 바뀌었다: commit-unit.md 고침, pr-language.md 새로 씀, old note.md 지움. "
            "되돌리기: python3 /x/restore.py commit-unit.md 2; python3 /x/restore.py 'old note.md' 2"))
        self.assertIsNone(describe_answer_changes([], "python3 /x/restore.py"))


if __name__ == "__main__":
    unittest.main()
