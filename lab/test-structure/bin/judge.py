#!/usr/bin/env python3
import glob
import hashlib
import json
import os
import sys

SEALED = os.environ["LAB_SEALED"]
run_dir = sys.argv[1]
record = json.load(open(f"{run_dir}/result.json", encoding="utf-8"))


def tree(path):
    return {os.path.relpath(p, path): hashlib.sha256(open(p, "rb").read()).hexdigest()
            for p in glob.glob(f"{path}/**", recursive=True) if os.path.isfile(p)}


def text(path, name):
    return open(f"{path}/{name}", encoding="utf-8").read()


def judge_ending(answer, before_dir, after_dir):
    before, after = tree(before_dir), tree(after_dir)
    stale_files = answer.get("stale_files") or [answer["stale_file"]]
    reasons = []
    index_before = text(before_dir, "MEMORY.md").splitlines()
    index_after = text(after_dir, "MEMORY.md").splitlines() if "MEMORY.md" in after else []
    for stale in stale_files:
        if stale not in after:
            if any(f"({stale})" in line for line in index_after):
                reasons.append(f"{stale}를 지웠는데 색인 줄이 남았다")
        else:
            body = text(after_dir, stale)
            if answer["must_contain"] not in body:
                reasons.append(f"{stale}에 {answer['must_contain']}이 없다")
            if answer["must_not_contain"] in body:
                reasons.append(f"{stale}에 {answer['must_not_contain']}이 남았다")
    for name in answer["untouched"]:
        if after.get(name) != before[name]:
            reasons.append(f"{name}이 바뀌었거나 없어졌다")
    for name in sorted(set(after) - set(before)):
        reasons.append(f"새 파일 {name}")
    for line in index_before:
        if not any(f"({stale})" in line for stale in stale_files) and line not in index_after:
            reasons.append(f"색인의 다른 줄이 바뀌었다: {line[:40]}")
    return reasons


def minute_of_first_memory_write(session, memory_dir):
    projects = os.path.dirname(os.path.dirname(memory_dir))
    transcript = next(iter(glob.glob(f"{projects}/*/{session}.jsonl")), None)
    if transcript is None:
        return None
    for line in open(transcript, encoding="utf-8"):
        row = json.loads(line)
        content = (row.get("message") or {}).get("content")
        if row.get("type") != "assistant" or not isinstance(content, list):
            continue
        for block in content:
            path = (block.get("input") or {}).get("file_path", "")
            if block.get("type") == "tool_use" and block.get("name") in ("Write", "Edit") and path.startswith(memory_dir):
                return row["timestamp"]
    return None


before_dir, after_dir = f"{run_dir}/memory-before", f"{run_dir}/memory-after"
if record["kind"] == "script":
    answer = json.load(open(f"{SEALED}/{record['test']}.json", encoding="utf-8"))
    reasons = judge_ending(answer, before_dir, after_dir)
    record["verdict"], record["reasons"] = ("fail" if reasons else "pass"), reasons
else:
    written_at = minute_of_first_memory_write(record["session"], record["memory_dir"])
    if written_at is None:
        record["verdict"], record["reasons"] = "fail", ["기억 폴더에 쓴 호출이 없다"]
    else:
        record["verdict"] = "human-pending"
        os.makedirs(SEALED, exist_ok=True)
        json.dump({"answer": written_at[:16], "written_at": written_at},
                  open(f"{SEALED}/{record['run_id']}.json", "w"))

json.dump(record, open(f"{run_dir}/result.json", "w"), ensure_ascii=False, indent=2)
print(record["verdict"], record.get("reasons", ""))
sys.exit(0 if record["verdict"] in ("pass", "human-pending") else 1)
