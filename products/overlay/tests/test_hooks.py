from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

OVERLAY = Path(__file__).resolve().parent.parent
RESTORE = OVERLAY / "restore.py"

INDEX = (
    "- [커밋 단위](commit-unit.md) — [todo-app] ticket 하나에 하나\n"
    "- [uv를 쓴다](uv.md) — [everywhere] 파이썬 패키지는 uv로\n"
)
COMMIT_UNIT = "---\nname: 커밋 단위\n---\n커밋은 ticket 하나에 하나로 올린다.\n"
UV = "---\nname: uv\n---\nuv를 쓴다.\n"


def project_folder_name(path: Path) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


class HookCase(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        self.home = self.root / "home"
        self.work = self.root / "work"
        self.memory = self.root / "agent-memory"
        self.journal = self.root / "agent-memory-journal"
        (self.home / ".claude").mkdir(parents=True)
        self.work.mkdir()
        self.env = {"HOME": str(self.home), "PATH": os.environ["PATH"]}

    def use_auto_memory_directory(self, value: str) -> None:
        (self.home / ".claude" / "settings.json").write_text(json.dumps({"autoMemoryDirectory": value}))

    def write_memories(self, folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "MEMORY.md").write_text(INDEX, encoding="utf-8")
        (folder / "commit-unit.md").write_text(COMMIT_UNIT, encoding="utf-8")
        (folder / "uv.md").write_text(UV, encoding="utf-8")

    def run_script(self, script: str, stdin: str = "", args: tuple[str, ...] = (),
                   cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(OVERLAY / script), *args], input=stdin, text=True,
                              capture_output=True, env=self.env, cwd=cwd or self.work, encoding="utf-8")

    def session_start(self, session: str = "s1", cwd: Path | None = None) -> dict:
        payload = {"session_id": session, "transcript_path": str(self.root / "t.jsonl"),
                   "cwd": str(cwd or self.work), "hook_event_name": "SessionStart", "source": "startup"}
        completed = self.run_script("session_start_hook.py", json.dumps(payload))
        self.assertEqual(completed.returncode, 0)
        return json.loads(completed.stdout)

    def stop(self, transcript_lines: list[dict], session: str = "s1", args: tuple[str, ...] = (),
             stop_hook_active: bool = False) -> dict:
        transcript = self.root / f"{session}.jsonl"
        transcript.write_text("".join(json.dumps(line, ensure_ascii=False) + "\n" for line in transcript_lines),
                              encoding="utf-8")
        payload = {"session_id": session, "transcript_path": str(transcript), "cwd": str(self.work),
                   "permission_mode": "default", "hook_event_name": "Stop", "stop_hook_active": stop_hook_active,
                   "last_assistant_message": "고쳤다."}
        completed = self.run_script("stop_hook.py", json.dumps(payload), args=args)
        self.assertEqual(completed.returncode, 0)
        return json.loads(completed.stdout)


PROMPT_THEN_TOOL_USE = [
    {"type": "user", "message": {"role": "user", "content": "앞의 말"}},
    {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "커밋은 이제 기능 하나에 하나다, 고쳐"}]}},
    {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "tool_use", "name": "Bash"}]}},
    {"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "content": "ok"}]}},
    {"type": "user", "isMeta": True, "message": {"role": "user", "content": "<system-reminder>무시</system-reminder>"}},
    {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "고쳤다."}]}},
]


class SessionStartHookTest(HookCase):
    def test_shows_loaded_memories_and_records_them(self) -> None:
        self.use_auto_memory_directory(str(self.memory))
        self.write_memories(self.memory)

        output = self.session_start()

        self.assertEqual(output, {"systemMessage": (
            "기억 2개가 실렸다.\n- 커밋 단위 [todo-app]\n- uv를 쓴다 [everywhere]\n"
            f"세션 밖에서 바뀐 기억 2개를 기록에 남겼다. 내력: {self.journal / 'history'}")})
        events = [json.loads(line) for line in (self.journal / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual([(e["event"], e["file"], e["session"]) for e in events], [
            ("created", "commit-unit.md", None), ("created", "uv.md", None),
            ("loaded", "commit-unit.md", "s1"), ("loaded", "uv.md", "s1")])

    def test_tilde_in_auto_memory_directory_is_read_from_home(self) -> None:
        self.use_auto_memory_directory("~/memories")
        self.write_memories(self.home / "memories")

        output = self.session_start()

        self.assertEqual(output["systemMessage"].splitlines()[0], "기억 2개가 실렸다.")
        self.assertTrue((self.home / "memories-journal" / "events.jsonl").is_file())

    def test_default_folder_is_named_after_the_working_folder(self) -> None:
        default_memory = self.home / ".claude" / "projects" / project_folder_name(self.work) / "memory"
        self.write_memories(default_memory)

        output = self.session_start()

        self.assertEqual(output["systemMessage"].splitlines()[0], "기억 2개가 실렸다.")
        self.assertTrue((default_memory.parent / "memory-journal" / "history" / "uv.md").is_file())

    def test_worktree_uses_the_main_repository_folder(self) -> None:
        repository = self.root / "todo-app"
        worktree = self.root / "todo-app-feature"
        git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com"]
        subprocess.run(["git", "init", "-q", str(repository)], check=True, env=self.env)
        subprocess.run([*git, "-C", str(repository), "commit", "-q", "--allow-empty", "-m", "init"], check=True, env=self.env)
        subprocess.run(["git", "-C", str(repository), "worktree", "add", "-q", str(worktree)], check=True, env=self.env)
        self.write_memories(self.home / ".claude" / "projects" / project_folder_name(repository) / "memory")

        output = self.session_start(cwd=worktree)

        self.assertEqual(output["systemMessage"].splitlines()[0], "기억 2개가 실렸다.")

    def test_journal_folder_follows_the_environment_variable(self) -> None:
        self.use_auto_memory_directory(str(self.memory))
        self.write_memories(self.memory)
        elsewhere = self.root / "elsewhere"
        self.env["AML_OVERLAY_JOURNAL_DIR"] = str(elsewhere)

        self.session_start()

        self.assertTrue((elsewhere / "events.jsonl").is_file())
        self.assertFalse(self.journal.exists())

    def test_failure_is_one_screen_line_and_exit_zero(self) -> None:
        (self.home / ".claude" / "settings.json").write_text("{ 깨진 settings")

        output = self.session_start()

        self.assertEqual(output, {"systemMessage": (
            "기억 기록이 실패했다. 일은 그대로 이어진다. "
            "(JSONDecodeError: Expecting property name enclosed in double quotes: line 1 column 3 (char 2))")})


class StopHookTest(HookCase):
    def setUp(self) -> None:
        super().setUp()
        self.use_auto_memory_directory(str(self.memory))
        self.write_memories(self.memory)
        self.session_start()

    def test_change_in_this_answer_is_announced_with_undo_command(self) -> None:
        (self.memory / "commit-unit.md").write_text(COMMIT_UNIT.replace("ticket", "기능"), encoding="utf-8")

        output = self.stop(PROMPT_THEN_TOOL_USE)

        self.assertEqual(output, {"systemMessage": (
            "이번 답에서 기억 1개가 바뀌었다: commit-unit.md 고침. "
            f"되돌리기: python3 {RESTORE} commit-unit.md 1")})
        last = json.loads((self.journal / "events.jsonl").read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual((last["event"], last["session"], last["cause"], last["prompt"]),
                         ("changed", "s1", "prompt", "커밋은 이제 기능 하나에 하나다, 고쳐"))

    def test_answer_without_memory_change_shows_nothing(self) -> None:
        self.assertEqual(self.stop(PROMPT_THEN_TOOL_USE), {})

    def test_missing_transcript_still_records_the_change(self) -> None:
        (self.memory / "uv.md").unlink()
        payload = {"session_id": "s1", "transcript_path": str(self.root / "없음.jsonl"), "cwd": str(self.work),
                   "hook_event_name": "Stop"}

        completed = self.run_script("stop_hook.py", json.dumps(payload))

        self.assertEqual(json.loads(completed.stdout), {"systemMessage": (
            f"이번 답에서 기억 1개가 바뀌었다: uv.md 지움. 되돌리기: python3 {RESTORE} uv.md 1")})
        last = json.loads((self.journal / "events.jsonl").read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual((last["event"], last["cause"], last["prompt"]), ("deleted", "prompt_not_found", None))


REDIS_INDEX = (
    "- [Redis 포트](redis-port.md) — 캐시 서버의 포트\n"
    "- [로컬 스택](local-stack.md) — 로컬에서 띄우는 것들\n"
)
REDIS_PORT = "---\nname: Redis 포트\n---\nRedis 포트는 6380이다.\n"
LOCAL_STACK = "---\nname: 로컬 스택\n---\n로컬 스택을 띄우면 캐시는 6380에서 듣는다.\n"
PORT_PROMPT = [{"type": "user", "message": {"role": "user", "content": "Redis 포트를 6390으로 바꿨어, 기억 고쳐"}}]
FIND_OLD_VALUES = ("--find-old-values",)


class OldValueStopHookTest(HookCase):
    def setUp(self) -> None:
        super().setUp()
        self.use_auto_memory_directory(str(self.memory))
        self.memory.mkdir()
        (self.memory / "MEMORY.md").write_text(REDIS_INDEX, encoding="utf-8")
        (self.memory / "redis-port.md").write_text(REDIS_PORT, encoding="utf-8")
        (self.memory / "local-stack.md").write_text(LOCAL_STACK, encoding="utf-8")
        self.session_start()
        self.changes_line = (f"이번 답에서 기억 1개가 바뀌었다: redis-port.md 고침. "
                             f"되돌리기: python3 {RESTORE} redis-port.md 1")

    def fix_redis_port_only(self) -> None:
        (self.memory / "redis-port.md").write_text(
            REDIS_PORT.replace("6380이다.", "6390이다(6380에서 바뀜)."), encoding="utf-8")

    def test_old_value_left_in_another_memory_goes_to_the_model_and_the_screen(self) -> None:
        self.fix_redis_port_only()

        output = self.stop(PORT_PROMPT, args=FIND_OLD_VALUES)

        self.assertEqual(output, {
            "systemMessage": self.changes_line + "\n옛 값을 품은 다른 기억 1개를 모델에게 알렸다: local-stack.md (6380).",
            "hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": (
                "기억 도구가 이번 답에서 바뀐 기억의 옛 값을 다른 기억에서 글자 그대로 찾았다. "
                "찾은 기억은 이번 답에서 바뀌지 않았다.\n"
                "옛 값 `6380` (redis-port.md에서 바뀜)\n"
                "- local-stack.md: 로컬 스택을 띄우면 캐시는 6380에서 듣는다.\n"
                "이 줄이 바뀐 값과 같은 사실을 적었다면 옛 값이 남아 있는 것이고, 다른 사실을 적었다면 그대로 맞다.")}})

    def test_without_the_flag_the_output_is_the_changes_line_alone(self) -> None:
        self.fix_redis_port_only()

        self.assertEqual(self.stop(PORT_PROMPT), {"systemMessage": self.changes_line})

    def test_continuation_by_a_stop_hook_records_but_does_not_notify(self) -> None:
        self.fix_redis_port_only()

        output = self.stop(PORT_PROMPT, args=FIND_OLD_VALUES, stop_hook_active=True)

        self.assertEqual(output, {"systemMessage": self.changes_line})
        last = json.loads((self.journal / "events.jsonl").read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual((last["event"], last["file"], last["version"]), ("changed", "redis-port.md", 2))

    def test_change_without_a_new_value_gives_the_same_output_as_without_the_flag(self) -> None:
        (self.memory / "redis-port.md").write_text(
            REDIS_PORT.replace("Redis 포트는 6380이다.", "Redis는 6380 포트에서 듣는다."), encoding="utf-8")

        self.assertEqual(self.stop(PORT_PROMPT, args=FIND_OLD_VALUES), {"systemMessage": self.changes_line})


class RestoreCommandTest(HookCase):
    def setUp(self) -> None:
        super().setUp()
        self.use_auto_memory_directory(str(self.memory))
        self.write_memories(self.memory)
        self.session_start()

    def test_restores_the_version_named_in_the_stop_message(self) -> None:
        (self.memory / "commit-unit.md").write_text(COMMIT_UNIT.replace("ticket", "기능"), encoding="utf-8")
        self.stop(PROMPT_THEN_TOOL_USE)

        completed = self.run_script("restore.py", args=("commit-unit.md", "1"))

        self.assertEqual((completed.returncode, completed.stdout), (0, (
            "되돌렸다. commit-unit.md의 내용을 판 1의 내용으로 바꾸고 새 판 3으로 남겼다. "
            f"내력: {self.journal / 'history' / 'commit-unit.md'}\n")))
        self.assertEqual((self.memory / "commit-unit.md").read_text(encoding="utf-8"), COMMIT_UNIT)
        self.assertEqual(self.stop(PROMPT_THEN_TOOL_USE), {})

    def test_unknown_version_fails_with_a_reason(self) -> None:
        completed = self.run_script("restore.py", args=("commit-unit.md", "9"))

        self.assertEqual((completed.returncode, completed.stderr),
                         (1, "되돌리지 못했다. commit-unit.md의 판은 1부터 1까지 있다.\n"))


if __name__ == "__main__":
    unittest.main()
