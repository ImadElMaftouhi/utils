#!/usr/bin/env python3
"""
files/convert.py — Text file encoding and line-ending conversion script
Converts file encodings (e.g. latin-1 → utf-8) and normalizes line endings (LF/CRLF/CR).
"""

import argparse
import sys
from pathlib import Path


LINE_ENDINGS = {
    "lf": b"\n",
    "crlf": b"\r\n",
    "cr": b"\r",
}


def convert_encoding(src: Path, dest: Path, from_enc: str, to_enc: str) -> int:
    """Re-encode src from from_enc to to_enc, writing to dest. Returns byte count written."""
    content = src.read_text(encoding=from_enc)
    dest.write_text(content, encoding=to_enc)
    return dest.stat().st_size


def normalize_line_endings(src: Path, dest: Path, style: str) -> int:
    """Normalize line endings in src to style (lf|crlf|cr), writing to dest.
    Returns byte count written."""
    raw = src.read_bytes()
    # Normalize to LF first, then replace
    normalized = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    target = LINE_ENDINGS[style]
    if style != "lf":
        normalized = normalized.replace(b"\n", target)
    dest.write_bytes(normalized)
    return dest.stat().st_size


def main():
    parser = argparse.ArgumentParser(
        description="Convert file encodings or normalize line endings."
    )
    parser.add_argument(
        "input",
        nargs="+",
        type=Path,
        help="Input file(s) or director(ies).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Output directory for converted files.",
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--to-encoding",
        metavar="ENC",
        help="Target encoding (e.g. utf-8, latin-1, utf-16). Requires --from-encoding.",
    )
    mode.add_argument(
        "--line-endings",
        choices=["lf", "crlf", "cr"],
        help="Normalize line endings to this style.",
    )

    parser.add_argument(
        "--from-encoding",
        metavar="ENC",
        default="utf-8",
        help="Source encoding for --to-encoding (default: utf-8).",
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

    files: list[Path] = []
    for inp in args.input:
        if inp.is_dir():
            glob = inp.rglob("*") if args.recursive else inp.glob("*")
            files.extend(f for f in glob if f.is_file())
        elif inp.is_file():
            files.append(inp)
        else:
            print(f"Not found: {inp}", file=sys.stderr)

    if not files:
        print("No files found.", file=sys.stderr)
        sys.exit(1)

    if not args.dry_run:
        args.output.mkdir(parents=True, exist_ok=True)

    errors = 0

    for src in files:
        dest = args.output / src.name

        if args.dry_run:
            mode_label = (
                f"{args.from_encoding} → {args.to_encoding}"
                if args.to_encoding
                else f"line-endings → {args.line_endings}"
            )
            print(f"[dry-run] {src} → {dest} ({mode_label})")
            continue

        try:
            if args.to_encoding:
                size = convert_encoding(src, dest, args.from_encoding, args.to_encoding)
                print(f"  {src.name}: {args.from_encoding} → {args.to_encoding} ({size} bytes)")
            else:
                size = normalize_line_endings(src, dest, args.line_endings)
                print(f"  {src.name}: → {args.line_endings.upper()} ({size} bytes)")
        except Exception as e:
            print(f"  ERROR {src.name}: {e}", file=sys.stderr)
            errors += 1

    if not args.dry_run and files:
        print(f"\nTotal: {len(files) - errors} ok, {errors} errors")


if __name__ == "__main__":
    main()
