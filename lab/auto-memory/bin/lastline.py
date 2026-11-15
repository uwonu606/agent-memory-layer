#!/usr/bin/env python3
import json
import re
import sys

records = [json.loads(line) for line in open(sys.argv[1], encoding="utf-8") if line.strip()]
for record in records:
    if record.get("type") == "attachment" and record["attachment"].get("type") == "instructions":
        for item in record["attachment"].get("files", []):
            content = item.get("content", "")
            numbers = re.findall(r"- L(\d{4}) ", content)
            tail = content[-220:].replace("\n", " ⏎ ")
            print(f"type={item.get('type')} load된 글자={len(content)} byte={len(content.encode())} 줄={content.count(chr(10)) + 1} 첫 L{numbers[0] if numbers else '-'} 끝 L{numbers[-1] if numbers else '-'}")
            print("   끝 220자:", tail)
            print("   그 밖의 key:", {k: (v if not isinstance(v, str) or len(v) < 80 else v[:80]) for k, v in item.items() if k != "content"})
