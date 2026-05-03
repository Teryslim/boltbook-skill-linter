"""CLI entrypoint: lint one-file skills against R001–R004 rules."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .rules import ALL_RULES


def _gather_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        if p.is_dir():
            files.extend(sorted(p.glob("**/*.md")))
        elif p.is_file():
            files.append(p)
        else:
            print(f"warning: {p} not found", file=sys.stderr)
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="skill-linter")
    parser.add_argument("paths", nargs="+", type=Path,
                        help="files or directories to lint (recursive .md)")
    parser.add_argument("--rules", default="all",
                        help="comma-separated rule codes or 'all' (default: all)")
    parser.add_argument("--strict", action="store_true",
                        help="exit nonzero on any violation (CI mode)")
    args = parser.parse_args(argv)

    rules = ALL_RULES
    if args.rules != "all":
        wanted = {c.strip() for c in args.rules.split(",")}
        rules = [r for r in ALL_RULES if r.code in wanted]
        if not rules:
            print(f"error: no rules matched {args.rules!r}", file=sys.stderr)
            return 2

    files = _gather_files(args.paths)
    if not files:
        print("no markdown files to lint", file=sys.stderr)
        return 0

    fail_count = 0
    for f in files:
        text = f.read_text(encoding="utf-8")
        for rule in rules:
            for v in rule.check(f, text):
                print(f"{v.path}:{v.line}: {v.code} {v.msg}")
                fail_count += 1

    if fail_count and args.strict:
        print(f"\n{fail_count} violation(s) — failing strict mode.", file=sys.stderr)
        return 1
    if fail_count:
        print(f"\n{fail_count} violation(s) (warning only — pass --strict for CI)",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
