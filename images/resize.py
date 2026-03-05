#!/usr/bin/env python3
"""
images/resize.py — Image resize script
Supports exact dimensions and percentage scaling via CLI arguments.
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
RESAMPLE_FILTER = Image.LANCZOS  # change here to swap resampling filter globally


def resize_image(
    src: Path,
    dest: Path,
    width: int | None,
    height: int | None,
    scale: float | None,
    stretch: bool,
) -> tuple[tuple[int, int], tuple[int, int]]:
    """Resize a single image. Returns (original_wh, new_wh)."""
    with Image.open(src) as img:
        orig_w, orig_h = img.size
        exif = img.info.get("exif", b"")

        if scale is not None:
            new_w = round(orig_w * scale)
            new_h = round(orig_h * scale)
        elif width and height:
            if stretch:
                new_w, new_h = width, height
            else:
                ratio = min(width / orig_w, height / orig_h)
                new_w = round(orig_w * ratio)
                new_h = round(orig_h * ratio)
        elif width:
            new_w = width
            new_h = round(orig_h * (width / orig_w))
        else:  # height only
            new_h = height
            new_w = round(orig_w * (height / orig_h))

        resized = img.resize((new_w, new_h), RESAMPLE_FILTER)

        ext = src.suffix.lower()
        if ext in (".jpg", ".jpeg"):
            resized.save(dest, exif=exif)
        else:
            resized.save(dest)

    return (orig_w, orig_h), (new_w, new_h)


def main():
    parser = argparse.ArgumentParser(
        description="Resize JPEG, PNG, and WebP images to an output directory."
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
        help="Output directory for resized images.",
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--scale",
        type=float,
        metavar="PERCENT",
        help="Scale factor as a percentage (e.g. 50 for 50%%).",
    )
    mode.add_argument(
        "--width",
        type=int,
        metavar="PX",
        help="Target width in pixels. Height scales proportionally unless --height is also set.",
    )

    parser.add_argument(
        "--height",
        type=int,
        metavar="PX",
        help="Target height in pixels. Width scales proportionally unless --width is also set.",
    )
    parser.add_argument(
        "--stretch",
        action="store_true",
        help="When both --width and --height are set, stretch to exact dimensions instead of fitting within bounds.",
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

    # Validate
    if args.scale is not None and args.scale <= 0:
        parser.error("--scale must be greater than 0")
    if args.width is not None and args.width <= 0:
        parser.error("--width must be greater than 0")
    if args.height is not None and args.height <= 0:
        parser.error("--height must be greater than 0")
    if args.stretch and not (args.width and args.height):
        parser.error("--stretch requires both --width and --height")
    if args.scale is not None and args.height is not None:
        parser.error("--height cannot be used with --scale")

    # --height without --width is valid as a standalone mode; expose it clearly
    # (argparse only makes --width/--scale mutually exclusive, so --height alone needs a check)
    if args.width is None and args.scale is None and args.height is None:
        parser.error("provide --scale, --width, --height, or a combination of --width/--height")

    scale = args.scale / 100 if args.scale is not None else None

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

    errors = 0

    for src in files:
        dest = args.output / src.name

        if args.dry_run:
            print(f"[dry-run] {src} → {dest}")
            continue

        try:
            (orig_w, orig_h), (new_w, new_h) = resize_image(
                src, dest,
                args.width,
                args.height,
                scale,
                args.stretch,
            )
            print(f"  {src.name}: {orig_w}x{orig_h} → {new_w}x{new_h}")
        except Exception as e:
            print(f"  ERROR {src.name}: {e}", file=sys.stderr)
            errors += 1

    if not args.dry_run and files:
        ok = len(files) - errors
        print(f"\nTotal: {ok} ok, {errors} errors")


if __name__ == "__main__":
    main()
