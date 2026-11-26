from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from itertools import groupby
from pathlib import Path

from memory_journal import (
    INDEX_FILE_NAME,
    INDEX_LINK,
    INDEX_SCOPE,
    Event,
    EventKind,
    Journal,
    MemoryVersion,
    read_memory_folder,
)

VALUE_MIN_LENGTH = 2
NOTICE_LINE_LIMIT = 10

CODE_SPAN = re.compile(r"`([^`\n]+)`")
VERBATIM_RUN = re.compile(r"[A-Za-z0-9._/:@~+-]+")
RUN_PART_SEPARATOR = re.compile(r"[:/@]")
VERBATIM_MARKS = frozenset("0123456789/_.@:-")
WORD_CHARS = "A-Za-z0-9_"
JOINER_CHARS = r"._/:@~+\-"
FRONTMATTER_DESCRIPTION = re.compile(r"^description:\s*(.*)$")
WIKI_LINK = re.compile(r"\[\[[^\]]*\]\]")
RELATIVE_LINK = re.compile(r"\[([^\]]*)\]\((?![^)]*://)[^)\s]+\)")


@dataclass(frozen=True)
class FactLine:
    found_in: str
    line: str
    facts: str


@dataclass(frozen=True)
class MemoryFacts:
    description: list[FactLine]
    body: list[FactLine]
    index: list[FactLine]

    def parts(self) -> tuple[list[FactLine], list[FactLine], list[FactLine]]:
        return self.description, self.body, self.index

    def lines(self) -> list[FactLine]:
        return [*self.description, *self.body, *self.index]


@dataclass(frozen=True)
class Rewrite:
    changed_memory: str
    before: list[str]
    after: list[str]


@dataclass(frozen=True)
class OldValue:
    text: str
    changed_memory: str


@dataclass(frozen=True)
class OldValueMention:
    old_value: OldValue
    holder: str
    found_in: str
    line: str


@dataclass(frozen=True)
class OldValueNotice:
    screen_line: str
    model_text: str


def find_old_value_mentions(memory_dir: Path, journal_dir: Path, answer_events: list[Event]) -> list[OldValueMention]:
    candidates = [value for rewrite in answer_rewrites(Journal(journal_dir), answer_events)
                  for value in old_values(rewrite)]
    if not candidates:
        return []
    touched = {event.file for event in answer_events}
    untouched = {file: memory.version for file, memory in read_memory_folder(memory_dir).memories.items()
                 if file not in touched}
    return mentions_of(candidates, untouched)


def answer_rewrites(journal: Journal, answer_events: list[Event]) -> list[Rewrite]:
    def saved_facts(event: Event, version: int) -> MemoryFacts:
        return memory_facts(event.file, journal.load_version(event.file, version))

    created = [saved_facts(event, event.version) for event in answer_events if event.kind is EventKind.CREATED]
    created_parts = MemoryFacts(*(
        [line for memory in created for line in memory.parts()[part]] for part in range(3)))
    rewrites = []
    for event in answer_events:
        if event.kind is EventKind.CHANGED:
            before, after = saved_facts(event, event.version - 1), saved_facts(event, event.version)
        elif event.kind is EventKind.DELETED:
            before, after = saved_facts(event, event.version), created_parts
        else:
            continue
        rewrites.extend(Rewrite(event.file, facts_of(before_part), facts_of(after_part))
                        for before_part, after_part in zip(before.parts(), after.parts()))
    return rewrites


def facts_of(lines: list[FactLine]) -> list[str]:
    return [line.facts for line in lines]


def memory_facts(file: str, version: MemoryVersion) -> MemoryFacts:
    frontmatter, body = split_frontmatter(version.content)
    descriptions = ((line, FRONTMATTER_DESCRIPTION.match(line)) for line in frontmatter)
    return MemoryFacts(
        description=[FactLine(file, line, found.group(1)) for line, found in descriptions if found],
        body=[FactLine(file, line, without_links(line)) for line in body],
        index=([FactLine(INDEX_FILE_NAME, version.index_line, index_description(version.index_line))]
               if version.index_line is not None else []),
    )


def split_frontmatter(content: str) -> tuple[list[str], list[str]]:
    lines = content.splitlines()
    if not lines or lines[0] != "---":
        return [], lines
    for position, line in enumerate(lines[1:], start=1):
        if line == "---":
            return lines[1:position], lines[position + 1:]
    return [], lines


def without_links(line: str) -> str:
    return RELATIVE_LINK.sub(r"\1", WIKI_LINK.sub("", line))


def index_description(index_line: str) -> str:
    link = INDEX_LINK.search(index_line)
    if link is None:
        return without_links(index_line)
    after_link = index_line[link.end():]
    scope = INDEX_SCOPE.match(after_link)
    if scope is not None:
        after_link = after_link[scope.end():]
    return without_links(after_link.strip().removeprefix("—").strip())


def old_values(rewrite: Rewrite) -> list[OldValue]:
    found: dict[str, None] = {}
    matcher = difflib.SequenceMatcher(None, rewrite.before, rewrite.after, autojunk=False)
    for tag, before_start, before_end, after_start, after_end in matcher.get_opcodes():
        if tag == "equal":
            continue
        removed = values_in(rewrite.before[before_start:before_end])
        added = set(values_in(rewrite.after[after_start:after_end]))
        if added <= set(removed):
            continue
        gone = [value for value in removed if value not in added]
        found.update(dict.fromkeys(gone or removed))
    return [OldValue(text, rewrite.changed_memory) for text in found]


def values_in(lines: list[str]) -> list[str]:
    found: dict[str, None] = {}
    for line in lines:
        found.update(dict.fromkeys(line_values(line)))
    return list(found)


def line_values(line: str) -> list[str]:
    found: dict[str, None] = {}
    for span in CODE_SPAN.findall(line):
        if len(span.strip()) >= VALUE_MIN_LENGTH:
            found[span.strip()] = None
    for run in VERBATIM_RUN.findall(line):
        for piece in (run, *RUN_PART_SEPARATOR.split(run)):
            token = piece.lstrip(":").rstrip(".:@-")
            if is_verbatim_token(token):
                found[token] = None
    return list(found)


def is_verbatim_token(token: str) -> bool:
    return len(token) >= VALUE_MIN_LENGTH and any(char in VERBATIM_MARKS for char in token)


def verbatim_pattern(value: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?<![{WORD_CHARS}])(?<![{WORD_CHARS}][{JOINER_CHARS}])"
        rf"{re.escape(value)}"
        rf"(?![{WORD_CHARS}])(?![{JOINER_CHARS}][{WORD_CHARS}])")


def mentions_of(candidates: list[OldValue], untouched: dict[str, MemoryVersion]) -> list[OldValueMention]:
    facts_by_holder = {holder: memory_facts(holder, version).lines() for holder, version in untouched.items()}
    mentions = []
    for old_value in candidates:
        pattern = verbatim_pattern(old_value.text)
        for holder, fact_lines in facts_by_holder.items():
            mentions.extend(OldValueMention(old_value, holder, fact_line.found_in, fact_line.line)
                            for fact_line in fact_lines if pattern.search(fact_line.facts))
    return mentions


def old_value_notice(mentions: list[OldValueMention], line_limit: int = NOTICE_LINE_LIMIT) -> OldValueNotice | None:
    if not mentions:
        return None
    shown = mentions[:line_limit]
    hidden = len(mentions) - len(shown)
    return OldValueNotice(screen_line_of(shown, hidden), model_text_of(shown, hidden))


def screen_line_of(shown: list[OldValueMention], hidden: int) -> str:
    values_by_holder: dict[str, dict[str, None]] = {}
    for mention in shown:
        values_by_holder.setdefault(mention.holder, {})[mention.old_value.text] = None
    holders = ", ".join(f"{holder} ({', '.join(values)})" for holder, values in values_by_holder.items())
    line = f"옛 값을 품은 다른 기억 {len(values_by_holder)}개를 모델에게 알렸다: {holders}."
    if hidden:
        line += f" 그 밖에 {hidden}줄."
    return line


def model_text_of(shown: list[OldValueMention], hidden: int) -> str:
    lines = ["기억 도구가 이번 답에서 바뀐 기억의 옛 값을 다른 기억에서 글자 그대로 찾았다. "
             "찾은 기억은 이번 답에서 바뀌지 않았다."]
    for old_value, group in groupby(shown, key=lambda mention: mention.old_value):
        lines.append(f"옛 값 `{old_value.text}` ({old_value.changed_memory}에서 바뀜)")
        lines.extend(f"- {mention.found_in}: {mention.line.strip()}" for mention in group)
    if hidden:
        lines.append(f"그 밖에 옛 값을 품은 줄이 {hidden}개 더 있다.")
    lines.append("이 줄이 바뀐 값과 같은 사실을 적었다면 옛 값이 남아 있는 것이고, 다른 사실을 적었다면 그대로 맞다.")
    return "\n".join(lines)
