#!/usr/bin/env python3
"""
data/converter.py — Data format conversion script
Converts between JSON, CSV, YAML, and TOML. Format inferred from file extensions.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

try:
    import yaml

    _YAML_AVAILABLE = True
except ImportError:
    yaml = None
    _YAML_AVAILABLE = False

if sys.version_info >= (3, 11):
    import tomllib

    _TOMLLIB_AVAILABLE = True
else:
    try:
        import tomli as tomllib

        _TOMLLIB_AVAILABLE = True
    except ImportError:
        tomllib = None
        _TOMLLIB_AVAILABLE = False

try:
    import tomli_w

    _TOMLI_W_AVAILABLE = True
except ImportError:
    tomli_w = None
    _TOMLI_W_AVAILABLE = False


SUPPORTED_FORMATS = {".json", ".csv", ".yaml", ".yml", ".toml"}

FORMAT_ALIASES = {".yml": "yaml", ".yaml": "yaml", ".json": "json", ".csv": "csv", ".toml": "toml"}


def _ext_to_fmt(path: Path) -> str:
    ext = path.suffix.lower()
    if ext not in FORMAT_ALIASES:
        raise ValueError(f"Unsupported format: {ext!r}. Supported: {sorted(SUPPORTED_FORMATS)}")
    return FORMAT_ALIASES[ext]


def load_file(src: Path, fmt: str | None = None) -> object:
    """Load src into a Python object. fmt overrides extension inference."""
    fmt = fmt or _ext_to_fmt(src)

    if fmt == "json":
        return json.loads(src.read_text(encoding="utf-8"))

    if fmt == "csv":
        with src.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            return list(reader)

    if fmt == "yaml":
        if not _YAML_AVAILABLE:
            print("pyyaml is required: pip install pyyaml", file=sys.stderr)
            sys.exit(1)
        return yaml.safe_load(src.read_text(encoding="utf-8"))

    if fmt == "toml":
        if not _TOMLLIB_AVAILABLE:
            print("tomli is required (Python <3.11): pip install tomli", file=sys.stderr)
            sys.exit(1)
        return tomllib.loads(src.read_text(encoding="utf-8"))

    raise ValueError(f"Unknown format: {fmt!r}")


def dump_file(data: object, dest: Path, fmt: str | None = None) -> None:
    """Write data to dest. fmt overrides extension inference."""
    fmt = fmt or _ext_to_fmt(dest)

    if fmt == "json":
        dest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return

    if fmt == "csv":
        if not isinstance(data, list) or not data:
            raise ValueError("CSV output requires a non-empty list of dicts")
        if not isinstance(data[0], dict):
            raise ValueError("CSV output requires a list of dicts (each row must be a dict)")
        with dest.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(data[0].keys()))
            writer.writeheader()
            writer.writerows(data)
        return

    if fmt == "yaml":
        if not _YAML_AVAILABLE:
            print("pyyaml is required: pip install pyyaml", file=sys.stderr)
            sys.exit(1)
        dest.write_text(yaml.dump(data, allow_unicode=True, default_flow_style=False), encoding="utf-8")
        return

    if fmt == "toml":
        if not _TOMLI_W_AVAILABLE:
            print("tomli-w is required: pip install tomli-w", file=sys.stderr)
            sys.exit(1)
        if not isinstance(data, dict):
            raise ValueError("TOML output requires a dict at the top level")
        dest.write_bytes(tomli_w.dumps(data).encode())
        return

    raise ValueError(f"Unknown format: {fmt!r}")


def convert(src: Path, dest: Path, from_fmt: str | None = None, to_fmt: str | None = None) -> None:
    """Load src and write to dest, converting between formats."""
    data = load_file(src, from_fmt)
    dump_file(data, dest, to_fmt)


def main():
    parser = argparse.ArgumentParser(
        description="Convert between JSON, CSV, YAML, and TOML formats."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Input file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Output file (format inferred from extension).",
    )
    parser.add_argument(
        "--from-format",
        metavar="FMT",
        choices=["json", "csv", "yaml", "toml"],
        help="Override source format detection.",
    )
    parser.add_argument(
        "--to-format",
        metavar="FMT",
        choices=["json", "csv", "yaml", "toml"],
        help="Override destination format detection.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without writing files.",
    )

    args = parser.parse_args()

    if not args.input.is_file():
        print(f"Not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    from_fmt = args.from_format or FORMAT_ALIASES.get(args.input.suffix.lower())
    to_fmt = args.to_format or FORMAT_ALIASES.get(args.output.suffix.lower())

    if not from_fmt:
        print(f"Cannot infer source format from {args.input.suffix!r}. Use --from-format.", file=sys.stderr)
        sys.exit(1)
    if not to_fmt:
        print(f"Cannot infer target format from {args.output.suffix!r}. Use --to-format.", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print(f"[dry-run] {args.input} ({from_fmt}) → {args.output} ({to_fmt})")
        sys.exit(0)

    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        convert(args.input, args.output, from_fmt, to_fmt)
        print(f"  {args.input.name} ({from_fmt}) → {args.output} ({to_fmt})")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
