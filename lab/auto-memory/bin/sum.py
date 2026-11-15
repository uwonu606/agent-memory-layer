#!/usr/bin/env python3
import json
import sys

LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 600


def clip(text):
    text = str(text).replace("\n", " ⏎ ")
    return text if len(text) <= LIMIT else text[:LIMIT] + f"…(+{len(text) - LIMIT}자)"


for line in open(sys.argv[1], encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    try:
        event = json.loads(line)
    except Exception:
        print("RAW", clip(line))
        continue
    kind = event.get("type")
    subtype = event.get("subtype")
    if kind == "system" and subtype == "init":
        keep = ("session_id", "cwd", "model", "permissionMode", "apiKeySource", "claude_code_version", "output_style")
        print("INIT", {k: event.get(k) for k in keep})
        print("     tools:", len(event.get("tools", [])), "| mcp:", [m.get("name") for m in event.get("mcp_servers", [])],
              "| plugins:", [p.get("name") for p in event.get("plugins", [])] if event.get("plugins") else event.get("plugins"),
              "| skills:", len(event.get("skills", []) or []), "| memory_paths:", event.get("memory_paths"))
    elif kind == "system" and subtype in ("commands_changed", "thinking_tokens"):
        continue
    elif kind == "rate_limit_event":
        continue
    elif kind == "system":
        body = {k: v for k, v in event.items() if k not in ("type", "uuid", "session_id")}
        print(f"SYSTEM/{subtype}", clip(json.dumps(body, ensure_ascii=False)))
    elif kind == "assistant":
        for block in event.get("message", {}).get("content", []):
            if block.get("type") == "text":
                print("ASSISTANT", clip(block["text"]))
            elif block.get("type") == "tool_use":
                print("TOOL_USE", block.get("name"), clip(json.dumps(block.get("input"), ensure_ascii=False)))
    elif kind == "user":
        content = event.get("message", {}).get("content", [])
        if isinstance(content, str):
            print("USER", clip(content))
        else:
            for block in content:
                if block.get("type") == "tool_result":
                    print("TOOL_RESULT", "error" if block.get("is_error") else "ok", clip(json.dumps(block.get("content"), ensure_ascii=False)))
                elif block.get("type") == "text":
                    print("USER", clip(block["text"]))
    elif kind == "result":
        keep = ("subtype", "is_error", "num_turns", "total_cost_usd", "permission_denials", "session_id")
        print("RESULT", {k: event.get(k) for k in keep})
    else:
        print(str(kind).upper(), clip(json.dumps(event, ensure_ascii=False)))
