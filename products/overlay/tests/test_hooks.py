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


SHOW_COST = ("--show-cost",)
MEMORY_RULES = (OVERLAY / "memory-rules.md").read_text(encoding="utf-8").strip()
UNCOUNTED_NOTE = "Claude Code가 붙이는 기억 지시와 잘림 경고는 세지 않았다."


def token_usage(input_tokens: int, created: int, read: int, output: int) -> dict:
    return {"input_tokens": input_tokens, "cache_creation_input_tokens": created,
            "cache_read_input_tokens": read, "output_tokens": output}


def model_turn(message_id: str, blocks: list[dict], tokens: dict) -> list[dict]:
    return [{"type": "api-request", "querySource": "sdk"}] + [
        {"type": "assistant", "isSidechain": False,
         "message": {"id": message_id, "role": "assistant", "content": [block], "usage": tokens}}
        for block in blocks]


def tool_result_line(tool_use_id: str, text: str) -> dict:
    return {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": tool_use_id, "content": text}]}}


def jsonl_text(entries: list[dict]) -> str:
    return "".join(json.dumps(entry, ensure_ascii=False) + "\n" for entry in entries)


class CostHookCase(HookCase):
    def setUp(self) -> None:
        super().setUp()
        self.use_auto_memory_directory(str(self.memory))
        (self.home / ".claude" / "CLAUDE.md").write_text(f"# 내 지시\n\n{MEMORY_RULES}\n", encoding="utf-8")
        self.transcript = self.root / "s1.jsonl"
        self.costs = self.journal / "costs"

    def start(self, session: str = "s1", source: str = "startup", args: tuple[str, ...] = SHOW_COST) -> dict:
        payload = {"session_id": session, "transcript_path": str(self.transcript), "cwd": str(self.work),
                   "hook_event_name": "SessionStart", "source": source}
        completed = self.run_script("session_start_hook.py", json.dumps(payload), args=args)
        self.assertEqual(completed.returncode, 0)
        return json.loads(completed.stdout)

    def append_transcript(self, entries: list[dict]) -> None:
        with open(self.transcript, "a", encoding="utf-8") as handle:
            handle.write(jsonl_text(entries))

    def end_answer(self, session: str = "s1", args: tuple[str, ...] = SHOW_COST,
                   stop_hook_active: bool = False) -> dict:
        payload = {"session_id": session, "transcript_path": str(self.transcript), "cwd": str(self.work),
                   "hook_event_name": "Stop", "stop_hook_active": stop_hook_active}
        completed = self.run_script("stop_hook.py", json.dumps(payload), args=args)
        self.assertEqual(completed.returncode, 0)
        return json.loads(completed.stdout)

    def cost_records(self, session: str = "s1") -> list[dict]:
        return [json.loads(line) for line in (self.costs / f"{session}.jsonl").read_text(encoding="utf-8").splitlines()]

    def last_answer(self, session: str = "s1") -> dict:
        return [record for record in self.cost_records(session) if record["event"] == "answer_end"][-1]


class CostFlagOffTest(CostHookCase):
    def run_scenario(self, name: str, args: tuple[str, ...]) -> tuple[list[dict], Path]:
        memory = self.root / name
        journal = self.root / f"{name}-journal"
        self.use_auto_memory_directory(str(memory))
        self.write_memories(memory)
        self.transcript = self.root / f"{name}.jsonl"
        self.transcript.write_text(jsonl_text(PROMPT_THEN_TOOL_USE), encoding="utf-8")
        outputs = [self.start(args=args)]
        (memory / "commit-unit.md").write_text(COMMIT_UNIT.replace("ticket", "기능"), encoding="utf-8")
        outputs.append(self.end_answer(args=args))
        return outputs, journal

    def test_without_the_flag_the_output_and_the_journal_folder_are_as_before(self) -> None:
        outputs, journal = self.run_scenario("plain", ())

        self.assertEqual(outputs, [
            {"systemMessage": ("기억 2개가 실렸다.\n- 커밋 단위 [todo-app]\n- uv를 쓴다 [everywhere]\n"
                               f"세션 밖에서 바뀐 기억 2개를 기록에 남겼다. 내력: {journal / 'history'}")},
            {"systemMessage": ("이번 답에서 기억 1개가 바뀌었다: commit-unit.md 고침. "
                               f"되돌리기: python3 {RESTORE} commit-unit.md 1")}])
        self.assertEqual(sorted(path.name for path in journal.iterdir()),
                         [".lock", "events.jsonl", "history", "loads", "versions"])

    def test_with_the_flag_the_other_lines_and_the_events_stay_the_same(self) -> None:
        plain_outputs, plain_journal = self.run_scenario("plain", ())
        cost_outputs, cost_journal = self.run_scenario("cost", SHOW_COST)

        def without_times(journal: Path) -> list[dict]:
            events = [json.loads(line) for line in (journal / "events.jsonl").read_text(encoding="utf-8").splitlines()]
            return [{key: value for key, value in event.items() if key != "at"} for event in events]

        for plain, cost in zip(plain_outputs, cost_outputs):
            plain_lines = plain["systemMessage"].replace(str(plain_journal), "<journal>").splitlines()
            cost_lines = cost["systemMessage"].replace(str(cost_journal), "<journal>").splitlines()
            self.assertEqual(cost_lines[:len(plain_lines)], plain_lines)
        self.assertEqual(without_times(cost_journal), without_times(plain_journal))
        self.assertEqual(sorted(path.name for path in cost_journal.iterdir()),
                         [".lock", "costs", "events.jsonl", "history", "loads", "versions"])


class CostSessionStartTest(CostHookCase):
    def setUp(self) -> None:
        super().setUp()
        self.write_memories(self.memory)

    def test_loaded_text_line_counts_the_index_and_the_rules(self) -> None:
        output = self.start()

        last_line = output["systemMessage"].splitlines()[-1]
        record = self.cost_records()[0]
        total = len(INDEX) + len(MEMORY_RULES)
        self.assertEqual(last_line, (
            f"기억 도구가 이 세션에 실은 글은 {total:,}자다(색인 2줄 {len(INDEX)}자, 얹는 제품의 지시 글 "
            f"{len(MEMORY_RULES):,}자). 이 글은 모델 요청마다 다시 읽힌다. {UNCOUNTED_NOTE} 이 hook {record['hook_ms']}ms(Python이 뜨는 시간은 빼고 잰 값)."))
        self.assertEqual({key: record[key] for key in ("event", "source", "index_lines", "index_chars", "rules_chars")},
                         {"event": "session_start", "source": "startup", "index_lines": 2,
                          "index_chars": len(INDEX), "rules_chars": len(MEMORY_RULES)})

    def test_rules_missing_from_the_instruction_file_are_written_as_not_found(self) -> None:
        (self.home / ".claude" / "CLAUDE.md").write_text("# 내 지시\n", encoding="utf-8")

        output = self.start()

        self.assertIn(f"(색인 2줄 {len(INDEX)}자).", output["systemMessage"])
        self.assertIsNone(self.cost_records()[0]["rules_chars"])
        self.assertIn("| 찾지 못함 |", (self.costs / "s1.md").read_text(encoding="utf-8"))

    def test_previous_session_and_resumed_session_lines(self) -> None:
        self.start("s1")
        self.append_transcript(model_turn("m1", [{"type": "text", "text": "끝"}], token_usage(1, 1, 1, 1)))
        self.end_answer("s1")

        resumed = self.start("s1", source="resume")["systemMessage"].splitlines()
        other = self.start("s2")["systemMessage"].splitlines()

        loaded = len(INDEX) + len(MEMORY_RULES)
        self.assertTrue(resumed[-1].startswith(
            f"이 세션에서 지금까지 기억 도구가 쓴 것: 답 1번, 모델 요청 1번이 실린 글을 다시 읽어 {loaded:,}자, "
            "모델이 기억 폴더를 다룬 호출 0번, 모델에게 보낸 알림 0자, hook 2번 합 "), resumed[-1])
        self.assertTrue(resumed[-1].endswith(f"ms(Python이 뜨는 시간은 빼고). 자세히: {self.costs / 's1.md'}"))
        self.assertRegex(other[-1], r"^지난 세션 s1\(\d{4}-\d\d-\d\d \d\d:\d\d UTC\)에서 기억 도구가 쓴 것: 답 1번, "
                                    r"모델 요청 1번이 .* hook 3번 합 \d+ms\(Python이 뜨는 시간은 빼고\)\. 자세히: ")
        self.assertEqual([(record["event"], record.get("source")) for record in self.cost_records("s1")],
                         [("session_start", "startup"), ("answer_end", None), ("session_start", "resume")])
        self.assertEqual((self.costs / "last-session").read_text(encoding="utf-8"), "s1\n")

    def test_failure_adds_one_line_and_keeps_the_rest(self) -> None:
        self.journal.mkdir()
        self.costs.write_text("폴더가 아니다", encoding="utf-8")

        lines = self.start()["systemMessage"].splitlines()

        self.assertEqual(lines[0], "기억 2개가 실렸다.")
        self.assertTrue(lines[-1].startswith("쓴 양 세기가 실패했다. 기억 기록은 남았고 일은 그대로 이어진다. ("), lines[-1])
        self.assertTrue((self.journal / "events.jsonl").is_file())


class CostStopTest(CostHookCase):
    def setUp(self) -> None:
        super().setUp()
        self.memory.mkdir()
        (self.memory / "MEMORY.md").write_text(REDIS_INDEX, encoding="utf-8")
        (self.memory / "redis-port.md").write_text(REDIS_PORT, encoding="utf-8")
        (self.memory / "local-stack.md").write_text(LOCAL_STACK, encoding="utf-8")
        self.start()
        self.loaded_chars = len(REDIS_INDEX) + len(MEMORY_RULES)
        self.product_hook = f"/usr/bin/python3 {OVERLAY / 'session_start_hook.py'} --show-cost"

    def read_and_fix_turns(self) -> list[dict]:
        return [
            *PORT_PROMPT,
            {"type": "attachment", "attachment": {"type": "hook_success", "command": self.product_hook, "durationMs": 41}},
            *model_turn("m1", [{"type": "thinking"}, {"type": "tool_use", "id": "t1", "name": "Read",
                                                     "input": {"file_path": str(self.memory / "redis-port.md")}}],
                        token_usage(2, 300, 1000, 50)),
            tool_result_line("t1", REDIS_PORT),
            *model_turn("m2", [{"type": "tool_use", "id": "t2", "name": "Edit",
                                "input": {"file_path": str(self.memory / "redis-port.md")}}],
                        token_usage(2, 100, 1300, 40)),
            tool_result_line("t2", "edited"),
            *model_turn("m3", [{"type": "text", "text": "고쳤다."}], token_usage(2, 10, 1400, 30)),
        ]

    def test_counts_of_one_answer_and_the_screen_line(self) -> None:
        self.append_transcript(self.read_and_fix_turns())
        (self.memory / "redis-port.md").write_text(
            REDIS_PORT.replace("6380이다.", "6390이다(6380에서 바뀜)."), encoding="utf-8")

        output = self.end_answer(args=FIND_OLD_VALUES + SHOW_COST)

        record = self.last_answer()
        notice = output["hookSpecificOutput"]["additionalContext"]
        self.assertEqual({key: value for key, value in record.items() if key not in ("at", "hook_ms")}, {
            "event": "answer_end", "transcript_offset": self.transcript.stat().st_size, "requests": 3,
            "usage": token_usage(6, 410, 3700, 120), "query_sources": {"sdk": 3},
            "memory_calls": {"read": {"count": 1, "result_chars": len(REDIS_PORT)},
                             "write": {"count": 1, "result_chars": len("edited")}},
            "notice_chars": len(notice), "stop_hook_active": False, "reread_chars": 3 * self.loaded_chars,
            "claude_code_hook_ms": [41]})
        lines = output["systemMessage"].splitlines()
        self.assertEqual(lines[:2], [self.changes_line(), "옛 값을 품은 다른 기억 1개를 모델에게 알렸다: local-stack.md (6380)."])
        self.assertEqual(lines[2], (
            f"이번 답에서 기억 도구가 쓴 것: 모델이 기억 폴더를 다룬 호출 2번(읽기 1번, 쓰기 1번, "
            f"결과 {len(REDIS_PORT) + 6}자가 대화에 들었다), 알림 {len(notice)}자, hook {record['hook_ms']}ms(Python이 뜨는 시간은 빼고 잰 값). "
            f"세션 합계: {self.costs / 's1.md'}"))

    def changes_line(self) -> str:
        return f"이번 답에서 기억 1개가 바뀌었다: redis-port.md 고침. 되돌리기: python3 {RESTORE} redis-port.md 1"

    def test_answer_without_memory_calls_or_notice_adds_no_line(self) -> None:
        self.append_transcript(model_turn("m1", [{"type": "text", "text": "답"}], token_usage(1, 1, 1, 1)))

        output = self.end_answer()

        self.assertEqual(output, {})
        self.assertEqual(self.last_answer()["requests"], 1)

    def test_second_stop_counts_only_the_new_lines(self) -> None:
        self.append_transcript(self.read_and_fix_turns())
        self.end_answer()
        first_offset = self.last_answer()["transcript_offset"]
        self.append_transcript([*PORT_PROMPT, *model_turn("m4", [{"type": "text", "text": "또"}], token_usage(1, 2, 3, 4))])

        self.end_answer()

        record = self.last_answer()
        self.assertEqual((record["requests"], record["usage"], record["memory_calls"]["read"]["count"]),
                         (1, token_usage(1, 2, 3, 4), 0))
        self.assertGreater(record["transcript_offset"], first_offset)

    def test_an_unfinished_last_line_waits_for_the_next_stop(self) -> None:
        finished = model_turn("m1", [{"type": "text", "text": "앞"}], token_usage(1, 1, 1, 1))
        unfinished = jsonl_text(model_turn("m2", [{"type": "text", "text": "뒤"}], token_usage(1, 1, 1, 1)))
        self.append_transcript(finished)
        with open(self.transcript, "a", encoding="utf-8") as handle:
            handle.write(unfinished[:-1])

        self.end_answer()
        self.assertEqual(self.last_answer()["requests"], 1)
        with open(self.transcript, "a", encoding="utf-8") as handle:
            handle.write("\n")
        self.end_answer()

        self.assertEqual(self.last_answer()["requests"], 1)
        self.assertEqual(self.last_answer()["transcript_offset"], self.transcript.stat().st_size)

    def test_requests_after_a_stop_hook_continued_the_answer_are_summed_apart(self) -> None:
        self.append_transcript(model_turn("m1", [{"type": "text", "text": "앞"}], token_usage(1, 1, 1, 1)))
        self.end_answer()
        self.append_transcript(model_turn("m2", [{"type": "text", "text": "이어"}], token_usage(1, 1, 1, 1)) +
                               model_turn("m3", [{"type": "text", "text": "끝"}], token_usage(1, 1, 1, 1)))

        self.end_answer(stop_hook_active=True)

        self.assertTrue(self.last_answer()["stop_hook_active"])
        self.assertIn("- 답 2번, 모델 요청 3번. 그 가운데 앞 `Stop` hook이 대화를 이어서 생긴 요청 2번",
                      (self.costs / "s1.md").read_text(encoding="utf-8"))

    def test_missing_transcript_is_unknown(self) -> None:
        self.end_answer()

        record = self.last_answer()
        self.assertEqual((record["requests"], record["memory_calls"], record["reread_chars"], record["transcript_offset"]),
                         (None, None, None, 0))

    def test_failure_adds_one_line_keeps_the_other_lines_and_exits_zero(self) -> None:
        shutil.rmtree(self.costs)
        self.costs.write_text("폴더가 아니다", encoding="utf-8")
        (self.memory / "redis-port.md").write_text(
            REDIS_PORT.replace("6380이다.", "6390이다(6380에서 바뀜)."), encoding="utf-8")

        output = self.end_answer(args=FIND_OLD_VALUES + SHOW_COST)

        lines = output["systemMessage"].splitlines()
        self.assertEqual(lines[:2], [self.changes_line(), "옛 값을 품은 다른 기억 1개를 모델에게 알렸다: local-stack.md (6380)."])
        self.assertTrue(lines[2].startswith("쓴 양 세기가 실패했다. 기억 기록은 남았고 일은 그대로 이어진다. ("), lines[2])
        self.assertIn("additionalContext", output["hookSpecificOutput"])


class CostBudgetTest(CostHookCase):
    def test_stop_with_250_memories_and_a_long_transcript_stays_within_100ms(self) -> None:
        self.memory.mkdir()
        index = "".join(f"- [기억 {n}](m{n}.md) — [todo-app] 서비스 {n}의 포트는 {6000 + n}이다\n" for n in range(250))
        (self.memory / "MEMORY.md").write_text(index, encoding="utf-8")
        for n in range(250):
            (self.memory / f"m{n}.md").write_text(
                f"---\nname: 기억 {n}\ndescription: 서비스 {n}의 포트\n---\n서비스 {n}의 포트는 {6000 + n}이다.\n"
                + "자세한 설명이 이어진다. " * 20 + "\n", encoding="utf-8")
        self.start()
        earlier_answers = []
        for answer in range(400):
            earlier_answers.append({"type": "user", "message": {"role": "user", "content": f"말 {answer} " + "가" * 400}})
            for call in range(5):
                tool_id = f"t{answer}-{call}"
                earlier_answers.extend(model_turn(f"m{answer}-{call}", [
                    {"type": "tool_use", "id": tool_id, "name": "Read", "input": {"file_path": str(self.memory / "m1.md")}}],
                    token_usage(2, 100, 40_000, 100)))
                earlier_answers.append(tool_result_line(tool_id, "가" * 2_000))
        self.append_transcript(earlier_answers)
        self.end_answer()
        self.assertGreater(self.transcript.stat().st_size, 10_000_000)
        self.append_transcript([*PORT_PROMPT, *self.long_answer()])
        (self.memory / "m7.md").write_text("---\nname: 기억 7\n---\n서비스 7의 포트는 7100이다(6007에서 바뀜).\n",
                                          encoding="utf-8")

        self.end_answer(args=FIND_OLD_VALUES + SHOW_COST)

        record = self.last_answer()
        self.assertEqual(record["requests"], 60)
        self.assertLessEqual(record["hook_ms"], 100)

    def long_answer(self) -> list[dict]:
        turns = []
        for call in range(60):
            tool_id = f"last-{call}"
            turns.extend(model_turn(f"last-{call}", [
                {"type": "tool_use", "id": tool_id, "name": "Bash", "input": {"command": f"grep -r 포트 {self.memory}"}}],
                token_usage(2, 100, 40_000, 100)))
            turns.append(tool_result_line(tool_id, "가" * 2_000))
        return turns


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
