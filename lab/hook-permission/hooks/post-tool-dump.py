#!/usr/bin/env python3
import json
import os
import sys

out_dir = os.path.join(os.environ["LAB_ROOT"], "out", os.environ.get("LAB_CASE", "nocase"))
os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(out_dir, "posttool.jsonl"), "a", encoding="utf-8") as f:
    f.write(json.dumps(json.load(sys.stdin), ensure_ascii=False) + "\n")
