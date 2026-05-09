#!/usr/bin/env python3
"""
pdf/compress.py — PDF compression script
Reduces PDF file size using pikepdf (QPDF backend) with configurable compression levels.
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

COMPRESSION_LEVELS = {
    "screen": dict(compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate),
    "ebook": dict(compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate),
    "printer": dict(compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate),
    "prepress": dict(compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate),
}


def compress_pdf(src: Path, dest: Path, level: str) -> tuple[int, int]:
    """Compress a single PDF. Returns (original_size, compressed_size)."""
    original_size = src.stat().st_size

    with pikepdf.open(src) as pdf:
        save_opts = COMPRESSION_LEVELS[level]
        pdf.save(dest, **save_opts)

    compressed_size = dest.stat().st_size
    return original_size, compressed_size


def format_bytes(b: int) -> str:
    if b < 1024:
        return f"{b} B"
    elif b < 1024**2:
        return f"{b / 1024:.1f} KB"
    return f"{b / 1024**2:.1f} MB"


def main():
    parser = argparse.ArgumentParser(
        description="Compress PDF files using pikepdf (QPDF backend)."
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
        help="Output directory for compressed PDFs.",
    )
    parser.add_argument(
        "--level",
        choices=["screen", "ebook", "printer", "prepress"],
        default="ebook",
        help="Compression level (default: ebook).",
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
    total_compressed = 0
    errors = 0

    for src in files:
        dest = args.output / src.name

        if args.dry_run:
            print(f"[dry-run] {src} → {dest}")
            continue

        try:
            orig, comp = compress_pdf(src, dest, args.level)
            total_original += orig
            total_compressed += comp
            savings_pct = (1 - comp / orig) * 100 if orig else 0
            print(
                f"  {src.name}: {format_bytes(orig)} → {format_bytes(comp)}"
                f" ({savings_pct:+.1f}%)"
            )
        except Exception as e:
            print(f"  ERROR {src.name}: {e}", file=sys.stderr)
            errors += 1

    if not args.dry_run and files:
        total_savings = (1 - total_compressed / total_original) * 100 if total_original else 0
        print(
            f"\nTotal: {format_bytes(total_original)} → {format_bytes(total_compressed)}"
            f" ({total_savings:+.1f}%) | {len(files) - errors} ok, {errors} errors"
        )


if __name__ == "__main__":
    main()
