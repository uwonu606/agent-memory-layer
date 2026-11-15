#!/usr/bin/env python3
import json
import os
import sys
import time

out_dir = os.path.join(os.environ["LAB_ROOT"], "out", os.environ.get("LAB_CASE", "nocase"))
os.makedirs(out_dir, exist_ok=True)
raw = sys.stdin.read()
try:
    hook_input = json.loads(raw)
except Exception:
    hook_input = {"_raw": raw}
with open(os.path.join(out_dir, "events.jsonl"), "a", encoding="utf-8") as f:
    f.write(json.dumps({"time": time.strftime("%H:%M:%S"), "input": hook_input}, ensure_ascii=False) + "\n")
