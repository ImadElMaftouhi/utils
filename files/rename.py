#!/usr/bin/env python3
"""
files/rename.py — Batch file rename script
Renames files using a pattern with tokens: {n}, {name}, {ext}, {date}.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path


def build_new_name(pattern: str, stem: str, ext: str, n: int, padding: int) -> str:
    """Substitute pattern tokens to produce a new filename string (without directory).

    Tokens:
      {n}    — zero-padded counter (width = padding; 0 means no padding)
      {name} — original filename stem
      {ext}  — original extension including the dot (e.g. ".jpg")
      {date} — current date as YYYY-MM-DD
    """
    counter = str(n).zfill(padding) if padding > 0 else str(n)
    today = datetime.now().strftime("%Y-%m-%d")
    result = (
        pattern.replace("{n}", counter)
        .replace("{name}", stem)
        .replace("{ext}", ext)
        .replace("{date}", today)
    )
    if not result.endswith(ext):
        result += ext
    return result


def rename_files(
    files: list[Path],
    pattern: str,
    start: int,
    padding: int,
    output_dir: Path | None,
    dry_run: bool,
) -> list[tuple[Path, Path]]:
    """Rename files according to pattern. Returns list of (src, dest) pairs."""
    pairs: list[tuple[Path, Path]] = []
    for i, src in enumerate(files):
        new_name = build_new_name(pattern, src.stem, src.suffix, start + i, padding)
        dest_dir = output_dir if output_dir is not None else src.parent
        dest = dest_dir / new_name
        pairs.append((src, dest))

    if dry_run:
        for src, dest in pairs:
            print(f"[dry-run] {src} → {dest}")
        return pairs

    errors = 0
    for src, dest in pairs:
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dest)
            print(f"  {src.name} → {dest.name}")
        except Exception as e:
            print(f"  ERROR {src.name}: {e}", file=sys.stderr)
            errors += 1

    print(f"\nTotal: {len(pairs) - errors} ok, {errors} errors")
    return pairs


def main():
    parser = argparse.ArgumentParser(
        description="Batch rename files using a pattern with tokens."
    )
    parser.add_argument(
        "input",
        nargs="+",
        type=Path,
        help="Input file(s) or director(ies).",
    )
    parser.add_argument(
        "--pattern",
        required=True,
        help="Filename pattern. Tokens: {n}, {name}, {ext}, {date}. E.g. 'photo_{n}'.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output directory (default: rename in-place).",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=1,
        help="Starting counter value for {n} (default: 1).",
    )
    parser.add_argument(
        "--padding",
        type=int,
        default=3,
        metavar="WIDTH",
        help="Zero-padding width for {n} (default: 3; 0 = no padding).",
    )
    parser.add_argument(
        "--filter",
        dest="glob_filter",
        metavar="PATTERN",
        help="Glob pattern to restrict files, e.g. '*.jpg'.",
    )
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Recurse into subdirectories.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without writing files.",
    )

    args = parser.parse_args()

    if args.padding < 0:
        parser.error("--padding must be 0 or greater")

    files: list[Path] = []
    for inp in args.input:
        if inp.is_dir():
            pattern = args.glob_filter or "*"
            glob = inp.rglob(pattern) if args.recursive else inp.glob(pattern)
            files.extend(f for f in glob if f.is_file())
        elif inp.is_file():
            files.append(inp)
        else:
            print(f"Not found: {inp}", file=sys.stderr)

    if not files:
        print("No files found.", file=sys.stderr)
        sys.exit(1)

    rename_files(files, args.pattern, args.start, args.padding, args.output, args.dry_run)


if __name__ == "__main__":
    main()
