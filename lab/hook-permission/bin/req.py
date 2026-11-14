#!/usr/bin/env python3
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument("transcript")
parser.add_argument("--which", default="last", help="last | all | 숫자(0부터)")
parser.add_argument("--clip", type=int, default=220)
parser.add_argument("--grep", default=None, help="이 글이 든 메시지만 길게 보인다")
parser.add_argument("--around", type=int, default=600)
args = parser.parse_args()

records = [json.loads(line) for line in open(args.transcript, encoding="utf-8") if line.strip()]
blobs = {r["hash"]: r["message"] for r in records if r.get("type") == "api-request-blob"}
requests = [r for r in records if r.get("type") == "api-request"]


def text_of(message):
    content = message.get("content")
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        if block.get("type") == "text":
            parts.append(block["text"])
        elif block.get("type") == "tool_use":
            parts.append("[tool_use " + block.get("name", "") + " " + json.dumps(block.get("input"), ensure_ascii=False) + "]")
        elif block.get("type") == "tool_result":
            parts.append("[tool_result " + json.dumps(block.get("content"), ensure_ascii=False) + "]")
        elif block.get("type") == "thinking":
            parts.append("[thinking]")
        else:
            parts.append("[" + str(block.get("type")) + "]")
    return " ‖ ".join(parts)


def show(index, request):
    hashes = request.get("tail") or []
    print(f"=== 요청 {index} ({request.get('timestamp')}, model={request.get('params', {}).get('model')}, 메시지 {len(hashes)}개, source={request.get('querySource')})")
    for position, digest in enumerate(hashes):
        message = blobs.get(digest)
        if message is None:
            print(f"  [{position}] (본문 없음 {digest[:8]})")
            continue
        text = text_of(message)
        if args.grep and args.grep in text:
            at = text.find(args.grep)
            start = max(0, at - args.around)
            shown = ("…" if start else "") + text[start:at + args.around] + ("…" if at + args.around < len(text) else "")
            print(f"  [{position}] {message.get('role')} ({len(text)}자) >>>\n{shown}\n  <<<")
        else:
            flat = text.replace("\n", " ⏎ ")
            clipped = flat if len(flat) <= args.clip else flat[:args.clip] + f"…(+{len(flat) - args.clip}자)"
            print(f"  [{position}] {message.get('role')}: {clipped}")


if args.which == "all":
    for index, request in enumerate(requests):
        show(index, request)
elif args.which == "last":
    if requests:
        show(len(requests) - 1, requests[-1])
    else:
        print("api-request record 없음")
else:
    show(int(args.which), requests[int(args.which)])
