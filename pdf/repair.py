#!/usr/bin/env python3
"""
pdf/repair.py — PDF repair script
Recovers data from corrupt PDFs by opening with pikepdf (more lenient than pypdf)
and re-saving as a clean PDF.
"""

import argparse
import sys
from pathlib import Path

try:
    import pikepdf
except ImportError:
    print("pikepdf is required: pip install pikepdf", file=sys.stderr)
    sys.exit(1)


SUPPORTED_FORMATS = {".pdf"}


def repair_pdf(src: Path, dest: Path) -> tuple[int, int]:
    """Open src and re-save to dest, recovering what pikepdf can.
    Returns (original_size, repaired_size)."""
    original_size = src.stat().st_size
    with pikepdf.open(src) as pdf:
        pdf.save(dest)
    repaired_size = dest.stat().st_size
    return original_size, repaired_size


def format_bytes(b: int) -> str:
    if b < 1024:
        return f"{b} B"
    elif b < 1024**2:
        return f"{b / 1024:.1f} KB"
    return f"{b / 1024**2:.1f} MB"


def main():
    parser = argparse.ArgumentParser(
        description="Repair corrupt PDF files by re-saving via pikepdf."
    )
    parser.add_argument(
        "input",
        nargs="+",
        type=Path,
        help="Input PDF file(s) or director(ies).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Output directory for repaired PDFs.",
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
            files.extend(f for f in glob if f.suffix.lower() in SUPPORTED_FORMATS)
        elif inp.is_file():
            if inp.suffix.lower() in SUPPORTED_FORMATS:
                files.append(inp)
            else:
                print(f"Skipping unsupported file: {inp}", file=sys.stderr)
        else:
            print(f"Not found: {inp}", file=sys.stderr)

    if not files:
        print("No PDF files found.", file=sys.stderr)
        sys.exit(1)

    if not args.dry_run:
        args.output.mkdir(parents=True, exist_ok=True)

    total_original = 0
    total_repaired = 0
    errors = 0

    for src in files:
        dest = args.output / src.name

        if args.dry_run:
            print(f"[dry-run] {src} → {dest}")
            continue

        try:
            orig, rep = repair_pdf(src, dest)
            total_original += orig
            total_repaired += rep
            diff_pct = (rep / orig - 1) * 100 if orig else 0
            print(
                f"  {src.name}: {format_bytes(orig)} → {format_bytes(rep)}"
                f" ({diff_pct:+.1f}%)"
            )
        except Exception as e:
            print(f"  ERROR {src.name}: {e}", file=sys.stderr)
            errors += 1

    if not args.dry_run and files:
        diff_pct = (total_repaired / total_original - 1) * 100 if total_original else 0
        print(
            f"\nTotal: {format_bytes(total_original)} → {format_bytes(total_repaired)}"
            f" ({diff_pct:+.1f}%) | {len(files) - errors} ok, {errors} errors"
        )


if __name__ == "__main__":
    main()
