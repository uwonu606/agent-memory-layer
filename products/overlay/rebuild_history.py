from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Mapping, Sequence

from claude_code import locate, place_for
from memory_journal import Journal, rebuild_history


def run(argv: Sequence[str], env: Mapping[str, str], cwd: Path) -> int:
    parser = argparse.ArgumentParser(
        prog="rebuild_history.py",
        description="기록 폴더의 events.jsonl과 versions/에서 history/를 다시 짓는다.",
    )
    parser.add_argument("--memory-dir", type=Path, help="기억 폴더. 주지 않으면 지금 폴더와 user settings에서 정한다")
    args = parser.parse_args(argv)
    place = place_for(args.memory_dir, env) if args.memory_dir else locate(cwd, env)
    rebuild_history(place.journal_dir)
    print(f"다시 지었다: {Journal(place.journal_dir).history_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:], os.environ, Path.cwd()))
