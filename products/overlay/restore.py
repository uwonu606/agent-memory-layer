from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

from claude_code import locate, place_for
from memory_journal import Journal, RestoreError, restore


def run(argv: Sequence[str], env: Mapping[str, str], cwd: Path) -> int:
    parser = argparse.ArgumentParser(
        prog="restore.py",
        description="기록에 남은 기억의 판 하나를 기억 폴더로 되돌린다. 판의 번호는 기록 폴더의 history/<기억 파일 이름>에 있다.",
    )
    parser.add_argument("file", help="기억 파일 이름. 예: commit-unit.md")
    parser.add_argument("version", type=int, help="되돌릴 판의 번호")
    parser.add_argument("--memory-dir", type=Path, help="기억 폴더. 주지 않으면 지금 폴더와 user settings에서 정한다")
    args = parser.parse_args(argv)
    place = place_for(args.memory_dir, env) if args.memory_dir else locate(cwd, env)
    try:
        event = restore(place.memory_dir, place.journal_dir, args.file, args.version, datetime.now(timezone.utc))
    except RestoreError as error:
        print(f"되돌리지 못했다. {error}", file=sys.stderr)
        return 1
    history = Journal(place.journal_dir).history_dir / args.file
    if event is None:
        print(f"그대로 두었다. {args.file}의 지금 내용이 판 {args.version}의 내용과 같다. 내력: {history}")
    else:
        print(f"되돌렸다. {args.file}의 내용을 판 {args.version}의 내용으로 바꾸고 새 판 {event.version}으로 남겼다. 내력: {history}")
    return 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:], os.environ, Path.cwd()))
