#!/usr/bin/env python3
"""
data/json_tools.py — JSON formatting and validation script
Pretty-prints, compacts, or validates JSON files.
"""

import argparse
import json
import sys
from pathlib import Path


def format_json(src: Path, dest: Path | None, indent: int) -> None:
    """Re-format src JSON with the given indent. Writes to dest or stdout."""
    data = json.loads(src.read_text(encoding="utf-8"))
    formatted = json.dumps(data, indent=indent, ensure_ascii=False)
    if dest is None:
        print(formatted)
    else:
        dest.write_text(formatted + "\n", encoding="utf-8")


def compact_json(src: Path, dest: Path | None) -> None:
    """Compact src JSON (no whitespace). Writes to dest or stdout."""
    data = json.loads(src.read_text(encoding="utf-8"))
    compacted = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    if dest is None:
        print(compacted)
    else:
        dest.write_text(compacted + "\n", encoding="utf-8")


def validate_json(src: Path) -> bool:
    """Return True if src is valid JSON, False otherwise."""
    try:
        json.loads(src.read_text(encoding="utf-8"))
        return True
    except json.JSONDecodeError:
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Format, compact, or validate JSON files."
    )
    parser.add_argument(
        "input",
        nargs="+",
        type=Path,
        help="Input JSON file(s) or director(ies).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file or directory (default: stdout).",
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print with indent=2 (default when no mode flag given).",
    )
    mode.add_argument(
        "--compact",
        action="store_true",
        help="Compact JSON with no extra whitespace.",
    )
    mode.add_argument(
        "--validate",
        action="store_true",
        help="Validate JSON syntax and report errors.",
    )

    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        metavar="N",
        help="Indentation spaces for --pretty (default: 2).",
    )
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Recurse into subdirectories.",
    )

    args = parser.parse_args()

    if args.indent < 0:
        parser.error("--indent must be 0 or greater")

    use_compact = args.compact
    use_validate = args.validate
    use_pretty = not use_compact and not use_validate

    files: list[Path] = []
    for inp in args.input:
        if inp.is_dir():
            glob = inp.rglob("*.json") if args.recursive else inp.glob("*.json")
            files.extend(glob)
        elif inp.is_file():
            if inp.suffix.lower() == ".json":
                files.append(inp)
            else:
                print(f"Skipping non-JSON file: {inp}", file=sys.stderr)
        else:
            print(f"Not found: {inp}", file=sys.stderr)

    if not files:
        print("No JSON files found.", file=sys.stderr)
        sys.exit(1)

    multi = len(files) > 1
    if args.output and multi and not use_validate:
        args.output.mkdir(parents=True, exist_ok=True)

    errors = 0
    invalid = 0

    for src in files:
        if use_validate:
            ok = validate_json(src)
            status = "OK" if ok else "INVALID"
            print(f"  {src}: {status}")
            if not ok:
                invalid += 1
            continue

        dest: Path | None = None
        if args.output:
            dest = (args.output / src.name) if multi else args.output

        try:
            if use_compact:
                compact_json(src, dest)
            else:
                format_json(src, dest, args.indent)
            if dest:
                print(f"  {src.name} → {dest}", file=sys.stderr)
        except Exception as e:
            print(f"  ERROR {src.name}: {e}", file=sys.stderr)
            errors += 1

    if use_validate:
        print(f"\nTotal: {len(files) - invalid} valid, {invalid} invalid")
    elif files:
        print(f"\nTotal: {len(files) - errors} ok, {errors} errors", file=sys.stderr)


if __name__ == "__main__":
    main()
