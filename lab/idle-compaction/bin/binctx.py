#!/usr/bin/env python3
import mmap
import sys

path, needle, before, after = sys.argv[1], sys.argv[2].encode(), int(sys.argv[3]), int(sys.argv[4])
limit = int(sys.argv[5]) if len(sys.argv) > 5 else 3
seen = set()
with open(path, "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as data:
    position = 0
    while len(seen) < limit:
        position = data.find(needle, position)
        if position < 0:
            break
        chunk = data[max(0, position - before):position + len(needle) + after]
        text = chunk.decode("utf-8", "replace").replace("\n", " ")
        if text not in seen:
            seen.add(text)
            print(f"@{position}: {text}\n")
        position += len(needle)
