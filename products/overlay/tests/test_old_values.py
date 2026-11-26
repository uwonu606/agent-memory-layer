from __future__ import annotations

import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from memory_journal import AnswerEnded, SeenOutsideSession, sync
from old_values import OldValue, OldValueMention, OldValueNotice, find_old_value_mentions, old_value_notice

NOW = datetime(2026, 11, 26, 9, 0, 0, tzinfo=timezone.utc)

REDIS_PORT = """---
name: Redis 포트
metadata:
  type: project
  originSessionId: s-old
---
Redis 포트는 6380이다.
"""
LOCAL_STACK_LINE = "로컬 스택을 띄우면 캐시는 6380에서 듣는다."
LOCAL_STACK = f"---\nname: 로컬 스택\n---\n{LOCAL_STACK_LINE}\n"
INDEX = (
    "- [Redis 포트](redis-port.md) — 캐시 서버의 포트\n"
    "- [로컬 스택](local-stack.md) — 로컬에서 띄우는 것들\n"
)
OLD_PORT = OldValue("6380", "redis-port.md")


def body_changed(content: str, old: str, new: str) -> str:
    assert old in content
    return content.replace(old, new)


class OldValueCase(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        self.memory = self.root / "memory"
        self.journal = self.root / "memory-journal"
        self.memory.mkdir()

    def start(self, local_stack: str = LOCAL_STACK, index: str = INDEX, redis_port: str = REDIS_PORT) -> None:
        self.write("MEMORY.md", index)
        self.write("redis-port.md", redis_port)
        self.write("local-stack.md", local_stack)
        sync(self.memory, self.journal, SeenOutsideSession(), NOW)

    def write(self, name: str, text: str) -> None:
        (self.memory / name).write_text(text, encoding="utf-8")

    def remove(self, name: str) -> None:
        (self.memory / name).unlink()

    def answer_ends(self) -> list[OldValueMention]:
        events = sync(self.memory, self.journal, AnswerEnded("s1", "Redis 포트를 6390으로 바꿨어, 기억 고쳐"), NOW)
        return find_old_value_mentions(self.memory, self.journal, events)


class FindOldValueMentionsTest(OldValueCase):
    def test_value_replaced_and_gone_is_found_in_another_memory(self) -> None:
        self.start(local_stack="---\nname: 로컬 스택\n---\n로컬 캐시 포트는 6380.\n")
        self.write("redis-port.md", body_changed(REDIS_PORT, "6380", "6390"))

        self.assertEqual(self.answer_ends(), [
            OldValueMention(OLD_PORT, "local-stack.md", "local-stack.md", "로컬 캐시 포트는 6380.")])

    def test_value_kept_as_history_in_the_changed_memory_is_still_old(self) -> None:
        self.start()
        self.write("redis-port.md", body_changed(REDIS_PORT, "6380이다.", "6390이다(6380에서 바뀜)."))

        self.assertEqual(self.answer_ends(), [
            OldValueMention(OLD_PORT, "local-stack.md", "local-stack.md", LOCAL_STACK_LINE)])

    def test_reworded_line_with_the_same_values_is_silent(self) -> None:
        self.start()
        self.write("redis-port.md", body_changed(REDIS_PORT, "Redis 포트는 6380이다.", "Redis는 6380 포트에서 듣는다."))

        self.assertEqual(self.answer_ends(), [])

    def test_new_memory_is_silent(self) -> None:
        self.start()
        self.write("sentinel.md", "---\nname: sentinel\n---\nSentinel은 6380 옆의 26380에서 듣는다.\n")

        self.assertEqual(self.answer_ends(), [])

    def test_memory_changed_in_the_same_answer_is_not_a_holder(self) -> None:
        self.start()
        self.write("redis-port.md", body_changed(REDIS_PORT, "6380", "6390"))
        self.write("local-stack.md", body_changed(LOCAL_STACK, "듣는다.", "듣는다. DB는 5432에서 듣는다."))

        self.assertEqual(self.answer_ends(), [])

    def test_memory_rewritten_under_a_new_name_is_not_a_holder(self) -> None:
        self.start()
        self.remove("redis-port.md")
        self.write("redis.md", body_changed(REDIS_PORT, "6380이다.", "6390이다(6380에서 바뀜)."))

        self.assertEqual(self.answer_ends(), [
            OldValueMention(OLD_PORT, "local-stack.md", "local-stack.md", LOCAL_STACK_LINE)])

    def test_value_inside_a_longer_number_is_not_a_mention(self) -> None:
        self.start(local_stack="---\nname: 로컬 스택\n---\n로컬 캐시는 16380에서 듣는다.\n")
        self.write("redis-port.md", body_changed(REDIS_PORT, "6380", "6390"))

        self.assertEqual(self.answer_ends(), [])

    def test_value_followed_by_a_korean_particle_is_a_mention(self) -> None:
        self.start()
        self.write("redis-port.md", body_changed(REDIS_PORT, "6380", "6390"))

        self.assertEqual([mention.line for mention in self.answer_ends()], [LOCAL_STACK_LINE])

    def test_frontmatter_written_by_the_harness_is_silent(self) -> None:
        machine_fields = "metadata:\n  originSessionId: s-old\n  modified: 2026-11-20T01:02:03Z\n"
        self.start(
            redis_port=body_changed(REDIS_PORT, "metadata:\n  type: project\n  originSessionId: s-old\n", machine_fields),
            local_stack=body_changed(LOCAL_STACK, "name: 로컬 스택\n", "name: 로컬 스택\n" + machine_fields))
        self.write("redis-port.md", body_changed(
            REDIS_PORT, "metadata:\n  type: project\n  originSessionId: s-old\n",
            "metadata:\n  originSessionId: s-new\n  modified: 2026-11-26T09:00:00Z\n"))

        self.assertEqual(self.answer_ends(), [])

    def test_only_the_changed_value_of_a_line_is_old(self) -> None:
        self.start(
            redis_port=body_changed(REDIS_PORT, "Redis 포트는 6380이다.", "Redis는 6380, Postgres는 5432다."),
            local_stack="---\nname: 로컬 스택\n---\n캐시는 6380에서 듣는다.\nDB는 5432에서 듣는다.\n")
        self.write("redis-port.md", body_changed(REDIS_PORT, "Redis 포트는 6380이다.", "Redis는 6390, Postgres는 5432다."))

        self.assertEqual(self.answer_ends(), [
            OldValueMention(OLD_PORT, "local-stack.md", "local-stack.md", "캐시는 6380에서 듣는다.")])

    def test_index_line_of_another_memory_is_searched(self) -> None:
        index_line = "- [로컬 스택](local-stack.md) — 캐시는 6380"
        self.start(index="- [Redis 포트](redis-port.md) — 캐시 서버의 포트\n" + index_line + "\n")
        self.write("redis-port.md", body_changed(REDIS_PORT, "6380", "6390"))

        self.assertEqual(self.answer_ends(), [
            OldValueMention(OLD_PORT, "local-stack.md", "local-stack.md", LOCAL_STACK_LINE),
            OldValueMention(OLD_PORT, "local-stack.md", "MEMORY.md", index_line)])

    def test_name_in_backticks_is_a_value(self) -> None:
        self.start(
            redis_port="---\nname: 패키지 관리자\n---\n패키지는 `pnpm`으로 깐다.\n",
            local_stack="---\nname: CI\n---\nCI는 pnpm install로 의존성을 깐다.\n")
        self.write("redis-port.md", "---\nname: 패키지 관리자\n---\n패키지는 `uv`로 깐다.\n")

        self.assertEqual(self.answer_ends(), [
            OldValueMention(OldValue("pnpm", "redis-port.md"), "local-stack.md", "local-stack.md",
                            "CI는 pnpm install로 의존성을 깐다.")])

    def test_removed_memory_without_a_rewrite_is_silent(self) -> None:
        self.start()
        self.remove("redis-port.md")

        self.assertEqual(self.answer_ends(), [])


def scoped_memory(name: str, body: str, description: str = "") -> str:
    return (f"---\nname: {name}\ndescription: {description}\nmetadata:\n  type: project\n"
            f"  repo: todo-app\n  everywhere: false\n---\n{body}\n")


def index_line(title: str, file: str, description: str) -> str:
    return f"- [{title}]({file}) — [todo-app] {description}"


SCOPED_REDIS_BEFORE = scoped_memory("redis-port", "Redis 포트는 `6380`이다. 로컬에서 캐시를 볼 때 이 포트를 쓴다.")
SCOPED_REDIS_AFTER = scoped_memory(
    "redis-port",
    "Redis 포트는 `6390`이다. 로컬에서 캐시를 볼 때 이 포트를 쓴다. 예전 포트 `6380`은 더 쓰지 않는다.\n"
    "\n로컬 스택 기억에도 이 포트가 있다: [[local-stack]]")
SCOPED_REDIS_INDEX_BEFORE = index_line("Redis 포트", "redis-port.md", "캐시가 듣는 포트")
SCOPED_REDIS_INDEX_AFTER = index_line("Redis 포트(새)", "redis-port.md", "캐시가 듣는 새 포트")
SCOPED_NEIGHBOURS = {
    "uv.md": (scoped_memory("uv", "파이썬 패키지는 uv로 깐다."), index_line("uv를 쓴다", "uv.md", "패키지 관리")),
    "todo-app.md": (scoped_memory("todo-app", "이 저장소는 할 일 앱이다."),
                    index_line("todo-app", "todo-app.md", "저장소 소개")),
}


class StructureIsNotAValueTest(OldValueCase):
    def start_scoped(self, redis_port: str, redis_index_line: str,
                     others: dict[str, tuple[str, str]]) -> None:
        memories = {"redis-port.md": (redis_port, redis_index_line), **SCOPED_NEIGHBOURS, **others}
        self.write("MEMORY.md", "".join(line + "\n" for _, line in memories.values()))
        for name, (content, _) in memories.items():
            self.write(name, content)
        sync(self.memory, self.journal, SeenOutsideSession(), NOW)

    def fix_redis(self, content: str, index_line_after: str) -> None:
        self.write("redis-port.md", content)
        index = (self.memory / "MEMORY.md").read_text(encoding="utf-8")
        old_line = next(line for line in index.splitlines() if "(redis-port.md)" in line)
        self.write("MEMORY.md", index.replace(old_line, index_line_after))

    def test_fix_with_history_an_added_line_and_a_retitled_index_line_is_silent(self) -> None:
        self.start_scoped(SCOPED_REDIS_BEFORE, SCOPED_REDIS_INDEX_BEFORE, {})
        self.fix_redis(SCOPED_REDIS_AFTER, SCOPED_REDIS_INDEX_AFTER)

        self.assertEqual(self.answer_ends(), [])

    def test_same_fix_finds_only_the_body_line_holding_the_old_value(self) -> None:
        self.start_scoped(SCOPED_REDIS_BEFORE, SCOPED_REDIS_INDEX_BEFORE, {
            "local-stack.md": (scoped_memory("local-stack", "로컬 스택을 띄운다.\n캐시는 6380에서 듣는다."),
                               index_line("로컬 스택", "local-stack.md", "로컬에서 띄우는 것들"))})
        self.fix_redis(SCOPED_REDIS_AFTER, SCOPED_REDIS_INDEX_AFTER)

        self.assertEqual(self.answer_ends(), [
            OldValueMention(OldValue("6380", "redis-port.md"), "local-stack.md", "local-stack.md",
                            "캐시는 6380에서 듣는다.")])

    def test_scope_and_own_file_name_in_a_changed_index_line_are_not_old_values(self) -> None:
        self.start_scoped(SCOPED_REDIS_BEFORE, index_line("Redis 포트", "redis-port.md", "캐시 포트 6380"), {
            "local-stack.md": (scoped_memory("local-stack", "todo-app의 로컬 스택은 redis-port.md의 포트를 본다.\n"
                                                            "캐시는 6380에서 듣는다."),
                               index_line("로컬 스택", "local-stack.md", "로컬에서 띄우는 것들"))})
        self.fix_redis(SCOPED_REDIS_BEFORE, index_line("Redis 포트", "redis-port.md", "캐시 포트 6390 (6380에서 바뀜)"))

        self.assertEqual(self.answer_ends(), [
            OldValueMention(OldValue("6380", "redis-port.md"), "local-stack.md", "local-stack.md",
                            "캐시는 6380에서 듣는다.")])

    def test_index_line_is_compared_apart_from_the_body(self) -> None:
        self.start_scoped(SCOPED_REDIS_BEFORE, index_line("Redis 포트", "redis-port.md", "캐시 포트, DB는 5432"), {
            "local-stack.md": (scoped_memory("local-stack", "캐시는 6380에서 듣는다.\nDB는 5432에서 듣는다."),
                               index_line("로컬 스택", "local-stack.md", "로컬에서 띄우는 것들"))})
        self.fix_redis(SCOPED_REDIS_AFTER, index_line("Redis 포트", "redis-port.md", "캐시의 새 포트, DB는 5432"))

        self.assertEqual([mention.line for mention in self.answer_ends()], ["캐시는 6380에서 듣는다."])

    def test_links_between_memories_are_not_values(self) -> None:
        self.start_scoped(scoped_memory("redis-port", "Redis 포트는 6380이다. [[local-stack]]과 [로컬 스택](local-stack.md)도 본다."),
                          SCOPED_REDIS_INDEX_BEFORE, {
            "local-stack.md": (scoped_memory("local-stack", "캐시는 6380에서 듣는다."),
                               index_line("로컬 스택", "local-stack.md", "로컬에서 띄우는 것들")),
            "monitoring.md": (scoped_memory("monitoring", "대시보드는 [[local-stack]]과 [로컬 스택](local-stack.md)을 본다."),
                              index_line("모니터링", "monitoring.md", "대시보드")),
        })
        self.fix_redis(scoped_memory("redis-port", "Redis 포트는 6390이다(6380에서 바뀜). [[local-stack]]과 [로컬 스택](local-stack.md)도 본다."),
                       SCOPED_REDIS_INDEX_BEFORE)

        self.assertEqual([(mention.holder, mention.line) for mention in self.answer_ends()],
                         [("local-stack.md", "캐시는 6380에서 듣는다.")])

    def test_old_value_spelled_like_the_repository_counts_only_in_body_and_description(self) -> None:
        deploy_before = scoped_memory("deploy-target", "배포 대상은 `todo-app`이다.")
        self.start_scoped(SCOPED_REDIS_BEFORE, SCOPED_REDIS_INDEX_BEFORE, {
            "deploy-target.md": (deploy_before, index_line("배포 대상", "deploy-target.md", "어디로 배포하나")),
            "image.md": (scoped_memory("image", "todo-app 이미지를 올린다."),
                         index_line("이미지", "image.md", "이미지 이름")),
            "ci.md": (scoped_memory("ci", "CI는 매일 돈다.", description="todo-app CI 일정"),
                      index_line("CI", "ci.md", "todo-app 빌드")),
        })
        self.write("deploy-target.md", deploy_before.replace("`todo-app`", "`todo-web`"))

        old_name = OldValue("todo-app", "deploy-target.md")
        self.assertEqual(self.answer_ends(), [
            OldValueMention(old_name, "ci.md", "ci.md", "description: todo-app CI 일정"),
            OldValueMention(old_name, "ci.md", "MEMORY.md", index_line("CI", "ci.md", "todo-app 빌드")),
            OldValueMention(old_name, "image.md", "image.md", "todo-app 이미지를 올린다."),
        ])


class OldValueNoticeTest(unittest.TestCase):
    def test_lines_past_the_limit_are_counted(self) -> None:
        mentions = [
            OldValueMention(OLD_PORT, "local-stack.md", "local-stack.md", LOCAL_STACK_LINE),
            OldValueMention(OLD_PORT, "local-stack.md", "MEMORY.md", "- [로컬 스택](local-stack.md) — 캐시는 6380"),
            OldValueMention(OldValue("3.12", "python.md"), "ci.md", "ci.md", "CI는 3.12로 돈다."),
        ]

        self.assertEqual(old_value_notice(mentions, line_limit=2), OldValueNotice(
            screen_line="옛 값을 품은 다른 기억 1개를 모델에게 알렸다: local-stack.md (6380). 그 밖에 1줄.",
            model_text=(
                "기억 도구가 이번 답에서 바뀐 기억의 옛 값을 다른 기억에서 글자 그대로 찾았다. "
                "찾은 기억은 이번 답에서 바뀌지 않았다.\n"
                "옛 값 `6380` (redis-port.md에서 바뀜)\n"
                f"- local-stack.md: {LOCAL_STACK_LINE}\n"
                "- MEMORY.md: - [로컬 스택](local-stack.md) — 캐시는 6380\n"
                "그 밖에 옛 값을 품은 줄이 1개 더 있다.\n"
                "이 줄이 바뀐 값과 같은 사실을 적었다면 옛 값이 남아 있는 것이고, 다른 사실을 적었다면 그대로 맞다.")))
        self.assertIsNone(old_value_notice([]))


if __name__ == "__main__":
    unittest.main()
