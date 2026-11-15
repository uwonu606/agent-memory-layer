#!/usr/bin/env python3
import collections
import json
import sys

records = [json.loads(line) for line in open(sys.argv[1], encoding="utf-8") if line.strip()]
print("record 종류:", dict(collections.Counter(r.get("type") for r in records)))
for record in records:
    kind = record.get("type")
    if kind == "system":
        body = {k: v for k, v in record.items() if k in ("subtype", "content", "compactMetadata", "level", "timestamp")}
        print("system:", json.dumps(body, ensure_ascii=False)[:400])
    elif kind == "api-request":
        cache = [(c.get("path"), c.get("value", {}).get("ttl")) for c in record.get("cacheControl", [])]
        print(f"api-request {record.get('timestamp')} querySource={record.get('querySource')} keep={record.get('keep')} tail={len(record.get('tail') or [])} cache={cache}")
    elif kind == "assistant":
        usage = record.get("message", {}).get("usage") or {}
        creation = usage.get("cache_creation") or {}
        print(f"assistant {record.get('timestamp')} input={usage.get('input_tokens')} cache_read={usage.get('cache_read_input_tokens')} cache_write={usage.get('cache_creation_input_tokens')} 1h={creation.get('ephemeral_1h_input_tokens')} 5m={creation.get('ephemeral_5m_input_tokens')} out={usage.get('output_tokens')}")
    elif kind == "summary" or "compact" in json.dumps(record.get("subtype", "")):
        print(kind, json.dumps(record, ensure_ascii=False)[:300])
