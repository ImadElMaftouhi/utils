#!/usr/bin/env python3
"""
data/csv_tools.py — CSV filtering and column selection script
Filters rows and selects columns from CSV files using simple expressions.
"""

import argparse
import csv
import operator
import re
import sys
from pathlib import Path


OPERATORS: dict[str, object] = {
    ">=": operator.ge,
    "<=": operator.le,
    "!=": operator.ne,
    "==": operator.eq,
    ">": operator.gt,
    "<": operator.lt,
}

EXPR_PATTERN = re.compile(r"^(.+?)\s*(>=|<=|!=|==|>|<)\s*(.+)$")


def parse_expr(expr: str) -> tuple[str, object, str]:
    """Parse "col>=value" → (col, op_func, value_str). Raises ValueError on bad syntax."""
    m = EXPR_PATTERN.match(expr)
    if not m:
        raise ValueError(f"Invalid filter expression: {expr!r}. Use: col>value, col==value, etc.")
    col, op_str, val = m.group(1).strip(), m.group(2), m.group(3).strip()
    return col, OPERATORS[op_str], val


def coerce(cell: str, ref: str) -> tuple[object, object]:
    """Try numeric coercion; fall back to string comparison."""
    try:
        return float(cell), float(ref)
    except ValueError:
        return cell, ref


def filter_rows(src: Path, dest: Path, expr: str, delimiter: str) -> tuple[int, int]:
    """Filter rows matching expr. Returns (input_rows, output_rows)."""
    col, op_func, ref = parse_expr(expr)

    with src.open(newline="", encoding="utf-8") as fin, dest.open(
        "w", newline="", encoding="utf-8"
    ) as fout:
        reader = csv.DictReader(fin, delimiter=delimiter)
        if reader.fieldnames is None:
            raise ValueError("CSV has no header row")
        if col not in reader.fieldnames:
            raise ValueError(f"Column {col!r} not found. Available: {list(reader.fieldnames)}")

        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames, delimiter=delimiter)
        writer.writeheader()

        in_count = 0
        out_count = 0
        for row in reader:
            in_count += 1
            cell, ref_val = coerce(row[col], ref)
            try:
                if op_func(cell, ref_val):
                    writer.writerow(row)
                    out_count += 1
            except TypeError:
                pass

    return in_count, out_count


def select_columns(src: Path, dest: Path, columns: list[str], delimiter: str) -> int:
    """Keep only the specified columns. Returns row count written."""
    with src.open(newline="", encoding="utf-8") as fin, dest.open(
        "w", newline="", encoding="utf-8"
    ) as fout:
        reader = csv.DictReader(fin, delimiter=delimiter)
        if reader.fieldnames is None:
            raise ValueError("CSV has no header row")

        missing = [c for c in columns if c not in reader.fieldnames]
        if missing:
            raise ValueError(f"Column(s) not found: {missing}. Available: {list(reader.fieldnames)}")

        writer = csv.DictWriter(fout, fieldnames=columns, delimiter=delimiter)
        writer.writeheader()

        count = 0
        for row in reader:
            writer.writerow({c: row[c] for c in columns})
            count += 1

    return count


def main():
    parser = argparse.ArgumentParser(
        description="Filter rows or select columns from CSV files."
    )
    parser.add_argument(
        "input",
        nargs="+",
        type=Path,
        help="Input CSV file(s) or director(ies).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Output file or directory.",
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--filter",
        metavar="EXPR",
        help="Filter rows by expression, e.g. 'age>30' or 'status==active'.",
    )
    mode.add_argument(
        "--columns",
        metavar="COLS",
        help="Comma-separated column names to keep, e.g. 'name,age,email'.",
    )

    parser.add_argument(
        "--delimiter",
        default=",",
        metavar="SEP",
        help="Field delimiter (default: comma).",
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

    col_list: list[str] | None = None
    if args.columns:
        col_list = [c.strip() for c in args.columns.split(",") if c.strip()]
        if not col_list:
            parser.error("--columns must specify at least one column name")

    files: list[Path] = []
    for inp in args.input:
        if inp.is_dir():
            glob = inp.rglob("*.csv") if args.recursive else inp.glob("*.csv")
            files.extend(glob)
        elif inp.is_file():
            if inp.suffix.lower() == ".csv":
                files.append(inp)
            else:
                print(f"Skipping non-CSV file: {inp}", file=sys.stderr)
        else:
            print(f"Not found: {inp}", file=sys.stderr)

    if not files:
        print("No CSV files found.", file=sys.stderr)
        sys.exit(1)

    multi = len(files) > 1
    if not args.dry_run:
        if multi:
            args.output.mkdir(parents=True, exist_ok=True)
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)

    errors = 0

    for src in files:
        dest = (args.output / src.name) if multi else args.output

        if args.dry_run:
            mode_label = f"filter={args.filter}" if args.filter else f"columns={args.columns}"
            print(f"[dry-run] {src} → {dest} ({mode_label})")
            continue

        try:
            if args.filter:
                in_rows, out_rows = filter_rows(src, dest, args.filter, args.delimiter)
                print(f"  {src.name}: {in_rows} rows → {out_rows} rows ({dest})")
            else:
                count = select_columns(src, dest, col_list, args.delimiter)
                print(f"  {src.name}: {count} rows, {len(col_list)} column(s) → {dest}")
        except Exception as e:
            print(f"  ERROR {src.name}: {e}", file=sys.stderr)
            errors += 1

    if not args.dry_run and files:
        print(f"\nTotal: {len(files) - errors} ok, {errors} errors")


if __name__ == "__main__":
    main()
