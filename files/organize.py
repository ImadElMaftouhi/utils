#!/usr/bin/env python3
"""
files/organize.py — File organization script
Sorts files into subdirectories by category, extension, or date.
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path


CATEGORY_MAP: dict[str, set[str]] = {
    "images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".avif", ".tiff", ".svg"},
    "documents": {".pdf", ".doc", ".docx", ".odt", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".md", ".rst"},
    "audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"},
    "video": {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm"},
    "archives": {".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar"},
    "code": {".py", ".js", ".ts", ".html", ".css", ".json", ".yaml", ".yml", ".toml", ".sh", ".rs", ".go", ".c", ".cpp", ".h"},
    "data": {".csv", ".tsv", ".jsonl", ".parquet", ".db", ".sqlite"},
}


def classify_file(src: Path) -> str:
    """Return the category folder name for src based on its extension."""
    ext = src.suffix.lower()
    for category, extensions in CATEGORY_MAP.items():
        if ext in extensions:
            return category
    return "other"


def organize_by_extension(files: list[Path], dest_dir: Path, dry_run: bool) -> dict[str, list[Path]]:
    """Move files into dest_dir/<ext>/ subfolders. Returns mapping of ext → moved files."""
    groups: dict[str, list[Path]] = {}
    for src in files:
        folder = src.suffix.lower().lstrip(".") or "no_ext"
        groups.setdefault(folder, []).append(src)

    for folder, group in groups.items():
        target = dest_dir / folder
        if not dry_run:
            target.mkdir(parents=True, exist_ok=True)
        for src in group:
            dest = target / src.name
            if dry_run:
                print(f"[dry-run] {src} → {dest}")
            else:
                shutil.move(str(src), dest)
                print(f"  {src.name} → {folder}/")

    return groups


def organize_by_category(files: list[Path], dest_dir: Path, dry_run: bool) -> dict[str, list[Path]]:
    """Move files into dest_dir/<category>/ subfolders. Returns mapping of category → files."""
    groups: dict[str, list[Path]] = {}
    for src in files:
        cat = classify_file(src)
        groups.setdefault(cat, []).append(src)

    for cat, group in groups.items():
        target = dest_dir / cat
        if not dry_run:
            target.mkdir(parents=True, exist_ok=True)
        for src in group:
            dest = target / src.name
            if dry_run:
                print(f"[dry-run] {src} → {dest}")
            else:
                shutil.move(str(src), dest)
                print(f"  {src.name} → {cat}/")

    return groups


def organize_by_date(files: list[Path], dest_dir: Path, dry_run: bool) -> dict[str, list[Path]]:
    """Move files into dest_dir/YYYY-MM/ subfolders based on mtime. Returns mapping."""
    groups: dict[str, list[Path]] = {}
    for src in files:
        mtime = datetime.fromtimestamp(src.stat().st_mtime)
        folder = mtime.strftime("%Y-%m")
        groups.setdefault(folder, []).append(src)

    for folder, group in groups.items():
        target = dest_dir / folder
        if not dry_run:
            target.mkdir(parents=True, exist_ok=True)
        for src in group:
            dest = target / src.name
            if dry_run:
                print(f"[dry-run] {src} → {dest}")
            else:
                shutil.move(str(src), dest)
                print(f"  {src.name} → {folder}/")

    return groups


def organize_by_year(files: list[Path], dest_dir: Path, dry_run: bool) -> dict[str, list[Path]]:
    """Move files into dest_dir/YYYY/ subfolders based on mtime."""
    groups: dict[str, list[Path]] = {}
    for src in files:
        mtime = datetime.fromtimestamp(src.stat().st_mtime)
        folder = mtime.strftime("%Y")
        groups.setdefault(folder, []).append(src)

    for folder, group in groups.items():
        target = dest_dir / folder
        if not dry_run:
            target.mkdir(parents=True, exist_ok=True)
        for src in group:
            dest = target / src.name
            if dry_run:
                print(f"[dry-run] {src} → {dest}")
            else:
                shutil.move(str(src), dest)
                print(f"  {src.name} → {folder}/")

    return groups


def main():
    parser = argparse.ArgumentParser(
        description="Organize files into subdirectories by category, extension, or date."
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
        help="Destination root directory.",
    )
    parser.add_argument(
        "--by",
        choices=["category", "extension", "date", "year"],
        default="category",
        help="Grouping strategy (default: category).",
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
        help="Show what would be done without moving files.",
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

    organizers = {
        "category": organize_by_category,
        "extension": organize_by_extension,
        "date": organize_by_date,
        "year": organize_by_year,
    }

    groups = organizers[args.by](files, args.output, args.dry_run)

    if not args.dry_run:
        total_moved = sum(len(g) for g in groups.values())
        print(f"\nTotal: {total_moved} file(s) organized into {len(groups)} folder(s)")


if __name__ == "__main__":
    main()
