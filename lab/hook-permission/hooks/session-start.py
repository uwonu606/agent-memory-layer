#!/usr/bin/env python3
import json
import os
import sys
import time

ROOT = os.environ["LAB_ROOT"]
case = os.environ.get("LAB_CASE", "nocase")
out_dir = os.path.join(ROOT, "out", case)
os.makedirs(out_dir, exist_ok=True)
log_path = os.path.join(out_dir, "hook-input.jsonl")

raw = sys.stdin.read()
try:
    hook_input = json.loads(raw)
except Exception:
    hook_input = {"_raw": raw}

try:
    with open(log_path, encoding="utf-8") as f:
        call_number = sum(1 for _ in f) + 1
except FileNotFoundError:
    call_number = 1

source = hook_input.get("source", "?")


def fill(text, chars=0):
    return (text.replace("{N}", str(call_number))
            .replace("{SOURCE}", str(source))
            .replace("{CHARS}", str(chars))
            .replace("{HOME}", os.path.expanduser("~")))


context = None
context_file = os.environ.get("LAB_CONTEXT_FILE")
if context_file:
    with open(context_file, encoding="utf-8") as f:
        context = fill(f.read())
elif os.environ.get("LAB_CONTEXT"):
    context = fill(os.environ["LAB_CONTEXT"])

system_message = os.environ.get("LAB_SYSMSG")
if system_message:
    system_message = fill(system_message, len(context) if context else 0)

with open(log_path, "a", encoding="utf-8") as f:
    f.write(json.dumps({
        "n": call_number,
        "time": time.strftime("%H:%M:%S"),
        "input": hook_input,
        "getcwd": os.getcwd(),
        "env": {k: os.environ.get(k) for k in ("CLAUDE_PROJECT_DIR", "PWD", "CLAUDE_ENV_FILE", "CLAUDE_CODE_ENTRYPOINT")},
        "context_chars": len(context) if context else 0,
        "sysmsg": system_message,
    }, ensure_ascii=False) + "\n")

try:
    with open(os.path.join(ROOT, "hookmode"), encoding="utf-8") as f:
        mode = f.read().strip()
except FileNotFoundError:
    mode = "ok"

if mode == "exit1":
    print("mem-hook: 맥락 규칙 파일을 읽지 못했다 (exit 1)", file=sys.stderr)
    sys.exit(1)
if mode == "exit2":
    print("mem-hook: 맥락 규칙 파일을 읽지 못했다 (exit 2)", file=sys.stderr)
    sys.exit(2)
if mode == "plain":
    print(f"plain stdout 글이다. 표지 낱말은 MARK-plain-{call_number}이다.")
    sys.exit(0)
if mode == "badjson":
    print('{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "깨진')
    sys.exit(0)
if mode == "empty":
    sys.exit(0)
if mode == "toplevel":
    print(json.dumps({
        "additionalContext": f"최상위에 둔 글. 표지 낱말은 MARK-toplevel-{call_number}이다.",
        "systemMessage": f"실림: 최상위 시험 {call_number}",
    }, ensure_ascii=False))
    sys.exit(0)
if mode == "multiline":
    system_message = f"실림: style.md, work/api-naming.md (1,240자)\n10,000자 넘음: 모델은 앞 2,000자만 받았다\n맥락: work [{call_number}]"
if mode == "nosys":
    system_message = None

output = {}
if context:
    output["hookSpecificOutput"] = {"hookEventName": "SessionStart", "additionalContext": context}
if system_message:
    output["systemMessage"] = system_message
print(json.dumps(output, ensure_ascii=False))
