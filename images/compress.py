#!/usr/bin/env python3
"""
images/compress.py — Image compression script
Supports JPEG, PNG, and WebP with configurable quality via CLI arguments.
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow is required: pip install Pillow", file=sys.stderr)
    sys.exit(1)


SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp"}


def compress_image(
    src: Path,
    dest: Path,
    jpeg_quality: int,
    png_compression: int,
    webp_quality: int,
    lossless_webp: bool,
) -> tuple[int, int]:
    """Compress a single image. Returns (original_size, compressed_size)."""
    original_size = src.stat().st_size
    ext = src.suffix.lower()

    with Image.open(src) as img:
        # Preserve EXIF data where possible
        exif = img.info.get("exif", b"")

        if ext in (".jpg", ".jpeg"):
            img.save(
                dest,
                format="JPEG",
                quality=jpeg_quality,
                optimize=True,
                exif=exif,
            )
        elif ext == ".png":
            img.save(
                dest,
                format="PNG",
                compress_level=png_compression,
                optimize=True,
            )
        elif ext == ".webp":
            img.save(
                dest,
                format="WEBP",
                quality=webp_quality,
                lossless=lossless_webp,
                method=6,  # slowest/best compression method
            )

    compressed_size = dest.stat().st_size
    return original_size, compressed_size


def format_bytes(b: int) -> str:
    if b < 1024:
        return f"{b} B"
    elif b < 1024 ** 2:
        return f"{b / 1024:.1f} KB"
    return f"{b / 1024 ** 2:.1f} MB"


def main():
    parser = argparse.ArgumentParser(
        description="Compress JPEG, PNG, and WebP images to an output directory."
    )
    parser.add_argument(
        "input",
        nargs="+",
        type=Path,
        help="Input image file(s) or director(ies).",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        required=True,
        help="Output directory for compressed images.",
    )
    parser.add_argument(
        "--jpeg-quality",
        type=int,
        default=85,
        metavar="1-95",
        help="JPEG quality (1-95, default: 85).",
    )
    parser.add_argument(
        "--png-compression",
        type=int,
        default=6,
        metavar="0-9",
        help="PNG compression level (0=none, 9=max, default: 6).",
    )
    parser.add_argument(
        "--webp-quality",
        type=int,
        default=80,
        metavar="1-100",
        help="WebP quality (1-100, default: 80). Ignored if --webp-lossless.",
    )
    parser.add_argument(
        "--webp-lossless",
        action="store_true",
        help="Use lossless WebP compression.",
    )
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Recurse into subdirectories.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without writing files.",
    )

    args = parser.parse_args()

    # Validate ranges
    if not (1 <= args.jpeg_quality <= 95):
        parser.error("--jpeg-quality must be between 1 and 95")
    if not (0 <= args.png_compression <= 9):
        parser.error("--png-compression must be between 0 and 9")
    if not (1 <= args.webp_quality <= 100):
        parser.error("--webp-quality must be between 1 and 100")

    # Collect input files
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
        print("No supported image files found.", file=sys.stderr)
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
            orig, comp = compress_image(
                src, dest,
                args.jpeg_quality,
                args.png_compression,
                args.webp_quality,
                args.webp_lossless,
            )
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