#!/usr/bin/env python3
import json
import os
import sys

root = os.environ["LAB_ROOT"]
stream = sys.argv[1]
for line in open(stream, encoding="utf-8"):
    try:
        event = json.loads(line)
    except Exception:
        continue
    kind = event.get("type")
    if kind == "assistant":
        for block in event.get("message", {}).get("content", []):
            if block.get("type") == "tool_use":
                tool_input = block.get("input", {})
                target = tool_input.get("file_path") or tool_input.get("command") or tool_input.get("pattern") or json.dumps(tool_input, ensure_ascii=False)
                print("   CALL", block.get("name"), str(target).replace(root, "<LAB>")[:230])
            elif block.get("type") == "text":
                print("   SAY ", block["text"].replace("\n", " ⏎ ").replace(root, "<LAB>")[:330])
    elif kind == "user":
        content = event.get("message", {}).get("content", [])
        if not isinstance(content, str):
            for block in content:
                if block.get("type") == "tool_result":
                    text = json.dumps(block.get("content"), ensure_ascii=False).replace(root, "<LAB>")
                    print("   →", ("error " + text[:170]) if block.get("is_error") else "ok " + text[:90])
