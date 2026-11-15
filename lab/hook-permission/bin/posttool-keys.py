#!/usr/bin/env python3
import argparse
import json


def brief(value):
    if isinstance(value, str):
        return f"str({len(value)}) {value[:60]!r}"
    if isinstance(value, list):
        return f"list({len(value)})"
    if isinstance(value, dict):
        return "dict(" + ", ".join(value) + ")"
    return repr(value)


def paths_holding(value, needle, where=""):
    if isinstance(value, str):
        return [where] if needle in value else []
    if isinstance(value, dict):
        return [hit for key, child in value.items() for hit in paths_holding(child, needle, f"{where}.{key}")]
    if isinstance(value, list):
        return [hit for index, child in enumerate(value) for hit in paths_holding(child, needle, f"{where}[{index}]")]
    return []


parser = argparse.ArgumentParser(description="PostToolUse hook이 떠 둔 입력에서 key 목록과, 찾는 글이 든 key를 보인다.")
parser.add_argument("dump", nargs="+", help="hooks/post-tool-dump.py가 쓴 posttool.jsonl")
parser.add_argument("--find", action="append", default=[], help="입력 어디에 들어 있는지 찾을 글")
args = parser.parse_args()

for dump in args.dump:
    for line in open(dump, encoding="utf-8"):
        hook_input = json.loads(line)
        print(f"== {dump}\n   tool_name={hook_input.get('tool_name')} top-level keys={list(hook_input)}")
        for part in ("tool_input", "tool_response"):
            print(f"   {part}:")
            body = hook_input.get(part)
            if not isinstance(body, dict):
                print(f"      {brief(body)}")
                continue
            for key, value in body.items():
                print(f"      {key}: {brief(value)}")
        for needle in args.find:
            print(f"   {needle!r} 가 든 곳: {paths_holding(hook_input, needle) or '없음'}")
