#!/usr/bin/env python3
import argparse
import json
import re

parser = argparse.ArgumentParser(description="transcript에서 모델에게 간 요청(system과 messages)을 다시 짜서 보인다.")
parser.add_argument("transcript")
parser.add_argument("command", choices=["reqs", "outline", "find", "dump"])
parser.add_argument("args", nargs="*")
parser.add_argument("--req", default="last", help="요청 번호(0부터), last, all")
parser.add_argument("--around", type=int, default=160)
options = parser.parse_args()

records = [json.loads(line) for line in open(options.transcript, encoding="utf-8") if line.strip()]
shapes = {r["shapeHash"]: r["shape"] for r in records if r.get("type") == "api-request-shape"}
blobs = {r["hash"]: r["message"] for r in records if r.get("type") == "api-request-blob"}
requests = [r for r in records if r.get("type") == "api-request"]


def block_text(block):
    kind = block.get("type")
    if kind == "text":
        return block["text"]
    if kind == "tool_use":
        return "[tool_use " + block.get("name", "") + " " + json.dumps(block.get("input"), ensure_ascii=False) + "]"
    if kind == "tool_result":
        return "[tool_result " + json.dumps(block.get("content"), ensure_ascii=False) + "]"
    return "[" + str(kind) + "]"


def message_text(message):
    content = message.get("content")
    if isinstance(content, str):
        return content
    return "\n‖\n".join(block_text(block) for block in content)


def message_hashes():
    by_request, previous = {}, []
    for request in requests:
        previous = previous[:request.get("keep") or 0] + (request.get("tail") or [])
        by_request[request["id"]] = previous
    return by_request


HASHES = message_hashes()


def parts(request):
    shape = shapes.get(request.get("shapeHash"), {})
    out = [(f"system[{i}]", block.get("text", "")) for i, block in enumerate(shape.get("system", []))]
    for position, digest in enumerate(HASHES[request["id"]]):
        message = blobs.get(digest)
        if message is None:
            out.append((f"messages[{position}] (본문 없음)", ""))
        else:
            out.append((f"messages[{position}] role={message.get('role')}", message_text(message)))
    return out


def chosen():
    if options.req == "all":
        return list(enumerate(requests))
    if options.req == "last":
        return [(len(requests) - 1, requests[-1])] if requests else []
    return [(int(options.req), requests[int(options.req)])]


def header(index, request):
    print(f"=== 요청 {index} {request.get('timestamp')} querySource={request.get('querySource')} model={request.get('params', {}).get('model')} 메시지 {len(HASHES[request['id']])}개(keep {request.get('keep')})")


if options.command == "reqs":
    for index, request in enumerate(requests):
        header(index, request)
elif options.command == "outline":
    for index, request in chosen():
        header(index, request)
        for name, text in parts(request):
            print(f"-- {name} ({len(text)}자)")
            for line in text.split("\n"):
                if re.match(r"^(#{1,4} |<[a-zA-Z_-]+>$)", line.strip()):
                    print("     ", line.strip()[:110])
elif options.command == "find":
    for index, request in chosen():
        header(index, request)
        for needle in options.args:
            hits = 0
            for name, text in parts(request):
                for match in re.finditer(re.escape(needle), text):
                    hits += 1
                    start = max(0, match.start() - options.around)
                    snippet = text[start:match.end() + options.around].replace("\n", " ⏎ ")
                    print(f"  [{needle}] {name} @{match.start()}: …{snippet}…")
            if not hits:
                print(f"  [{needle}] 없음")
elif options.command == "dump":
    target = options.args[0]
    for index, request in chosen():
        for name, text in parts(request):
            if name.startswith(target):
                print(f"##### {name} ({len(text)}자)\n{text}\n")
