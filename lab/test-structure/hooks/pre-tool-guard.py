#!/usr/bin/env python3
import json
import os
import sys
import time

ROOT = os.environ["LAB_ROOT"]
REAL_HOME = os.environ["LAB_REAL_HOME"]
case = os.environ.get("LAB_CASE", "nocase")
out_dir = os.path.join(ROOT, "out", case)
os.makedirs(out_dir, exist_ok=True)

hook_input = json.load(sys.stdin)
tool_input_text = json.dumps(hook_input.get("tool_input", {}), ensure_ascii=False)
touches_real_home = REAL_HOME in tool_input_text.replace(ROOT, "")

with open(os.path.join(out_dir, "pretool.jsonl"), "a", encoding="utf-8") as f:
    f.write(json.dumps({
        "time": time.strftime("%H:%M:%S"),
        "tool": hook_input.get("tool_name"),
        "tool_input": hook_input.get("tool_input"),
        "denied": touches_real_home,
    }, ensure_ascii=False) + "\n")

if touches_real_home:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": f"이 세션의 HOME은 {ROOT}/home 이다. ~는 그 경로로 푼다.",
    }}, ensure_ascii=False))
