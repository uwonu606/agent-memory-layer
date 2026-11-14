#!/usr/bin/env python3
import argparse
import os
import random

ROOT = os.environ["LAB_ROOT"]
HEAD = "이 세션의 머리 표지 낱말은 HEAD-1이다. "
TAIL = " 이 세션의 꼬리 표지 낱말은 TAIL-1이다."
MIDDLE_MARKERS = ((1900, "MID1900"), (2100, "MID2100"))
VOCABULARY = ("river stone window garden letter music table silver morning forest bridge paper candle harbor "
              "winter summer lantern market story travel mountain quiet orange button mirror thunder island pocket "
              "yellow circle basket feather engine corner blanket ribbon salt copper velvet meadow signal anchor").split()

parser = argparse.ArgumentParser(description="10,000자 경계용 글과 compaction을 일으킬 큰 파일을 만든다.")
parser.add_argument("--big-files-dir", help="이 폴더에 part1.txt~part6.txt를 만든다")
args = parser.parse_args()


def boundary_text(code_points, emoji_count=0):
    filler_length = code_points - len(HEAD) - len(TAIL) - emoji_count
    filler = list("가" * filler_length)
    for position, marker in MIDDLE_MARKERS:
        start = position - len(HEAD)
        filler[start:start + len(marker)] = list(marker)
    text = HEAD + "".join(filler) + "😀" * emoji_count + TAIL
    assert len(text) == code_points
    return text


payload_dir = os.path.join(ROOT, "payload")
os.makedirs(payload_dir, exist_ok=True)
for name, code_points, emoji_count in (("ko9999", 9999, 0), ("ko10000", 10000, 0), ("ko10001", 10001, 0), ("emoji10000", 10000, 10)):
    text = boundary_text(code_points, emoji_count)
    with open(os.path.join(payload_dir, name + ".txt"), "w", encoding="utf-8") as f:
        f.write(text)
    print(name, "code point", len(text), "UTF-16 unit", len(text.encode("utf-16-le")) // 2)

if args.big_files_dir:
    random.seed(7)
    os.makedirs(args.big_files_dir, exist_ok=True)
    for part in range(1, 7):
        lines = [" ".join(random.choice(VOCABULARY) for _ in range(10)) for _ in range(1800)]
        with open(os.path.join(args.big_files_dir, f"part{part}.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    print("part1.txt~part6.txt:", args.big_files_dir)
