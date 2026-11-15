#!/usr/bin/env python3
import json
import os
import sys
import time

ROOT = os.environ["LAB_ROOT"]
REAL_HOME = os.environ["LAB_REAL_HOME"]
HOME = os.environ.get("LAB_HOME", f"{ROOT}/home")
case = os.environ.get("LAB_CASE", "nocase")
out_dir = os.path.join(ROOT, "out", case)
os.makedirs(out_dir, exist_ok=True)

hook_input = json.load(sys.stdin)
tool_input_text = json.dumps(hook_input.get("tool_input", {}), ensure_ascii=False)
touches_real_home = REAL_HOME in tool_input_text
allows_mem = os.environ.get("LAB_PRETOOL_ALLOW_MEM") == "1" and "/.mem" in tool_input_text and not touches_real_home

decision = "deny" if touches_real_home else ("allow" if allows_mem else None)
with open(os.path.join(out_dir, "pretool.jsonl"), "a", encoding="utf-8") as f:
    f.write(json.dumps({
        "time": time.strftime("%H:%M:%S"),
        "tool": hook_input.get("tool_name"),
        "permission_mode": hook_input.get("permission_mode"),
        "agent_id": hook_input.get("agent_id"),
        "agent_type": hook_input.get("agent_type"),
        "cwd": hook_input.get("cwd"),
        "tool_input": hook_input.get("tool_input"),
        "decision": decision,
    }, ensure_ascii=False) + "\n")

if touches_real_home:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": f"이 세션의 HOME은 {HOME} 이다. ~는 그 경로로 푼다.",
    }}, ensure_ascii=False))
elif allows_mem:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "permissionDecisionReason": "실험: ~/.mem 경로를 hook이 allow한다",
    }}, ensure_ascii=False))
