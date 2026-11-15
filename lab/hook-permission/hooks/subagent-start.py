#!/usr/bin/env python3
import json
import os
import sys
import time

out_dir = os.path.join(os.environ["LAB_ROOT"], "out", os.environ.get("LAB_CASE", "nocase"))
os.makedirs(out_dir, exist_ok=True)
log_path = os.path.join(out_dir, "subagent-start.jsonl")

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

with open(log_path, "a", encoding="utf-8") as f:
    f.write(json.dumps({"n": call_number, "time": time.strftime("%H:%M:%S"), "input": hook_input}, ensure_ascii=False) + "\n")

if os.environ.get("LAB_SUBSTART_CONTEXT") == "1":
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SubagentStart",
        "additionalContext": f"이 subagent의 표지 낱말은 MARK-SUBSTART-{call_number}이다.",
    }}, ensure_ascii=False))
