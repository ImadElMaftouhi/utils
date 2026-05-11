"""Tests for the data module (json_tools, csv_tools, converter)."""

import csv
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestJsonTools:
    def test_format_json_pretty(self, sample_json: Path, tmp_path: Path):
        from data.json_tools import format_json

        dest = tmp_path / "pretty.json"
        format_json(sample_json, dest, indent=2)
        assert dest.exists()
        loaded = json.loads(dest.read_text())
        assert loaded["name"] == "Alice"

    def test_format_json_stdout(self, sample_json: Path, capsys):
        from data.json_tools import format_json

        format_json(sample_json, None, indent=2)
        out = capsys.readouterr().out
        assert "Alice" in out

    def test_compact_json(self, sample_json: Path, tmp_path: Path):
        from data.json_tools import compact_json

        dest = tmp_path / "compact.json"
        compact_json(sample_json, dest)
        content = dest.read_text()
        assert " " not in content.split('"name"')[0].split("{")[1]

    def test_validate_json_valid(self, sample_json: Path):
        from data.json_tools import validate_json

        assert validate_json(sample_json) is True

    def test_validate_json_invalid(self, tmp_path: Path):
        from data.json_tools import validate_json

        bad = tmp_path / "bad.json"
        bad.write_text("{invalid json}", encoding="utf-8")
        assert validate_json(bad) is False


class TestCsvTools:
    def test_filter_rows_greater_than(self, sample_csv: Path, tmp_path: Path):
        from data.csv_tools import filter_rows

        dest = tmp_path / "filtered.csv"
        in_rows, out_rows = filter_rows(sample_csv, dest, "age>28", ",")
        assert in_rows == 3
        assert out_rows == 2  # Alice (30) and Carol (35)

    def test_filter_rows_equal(self, sample_csv: Path, tmp_path: Path):
        from data.csv_tools import filter_rows

        dest = tmp_path / "filtered.csv"
        in_rows, out_rows = filter_rows(sample_csv, dest, "city==Paris", ",")
        assert out_rows == 2  # Alice and Carol

    def test_filter_invalid_expr(self, sample_csv: Path, tmp_path: Path):
        from data.csv_tools import filter_rows

        dest = tmp_path / "out.csv"
        with pytest.raises(ValueError, match="Invalid filter"):
            filter_rows(sample_csv, dest, "no_operator", ",")

    def test_filter_missing_column(self, sample_csv: Path, tmp_path: Path):
        from data.csv_tools import filter_rows

        dest = tmp_path / "out.csv"
        with pytest.raises(ValueError, match="not found"):
            filter_rows(sample_csv, dest, "salary>1000", ",")

    def test_select_columns(self, sample_csv: Path, tmp_path: Path):
        from data.csv_tools import select_columns

        dest = tmp_path / "selected.csv"
        count = select_columns(sample_csv, dest, ["name", "city"], ",")
        assert count == 3
        with dest.open(newline="") as fh:
            reader = csv.DictReader(fh)
            assert reader.fieldnames == ["name", "city"]

    def test_select_missing_column(self, sample_csv: Path, tmp_path: Path):
        from data.csv_tools import select_columns

        dest = tmp_path / "out.csv"
        with pytest.raises(ValueError, match="not found"):
            select_columns(sample_csv, dest, ["nonexistent"], ",")


class TestConverter:
    def test_json_to_csv(self, tmp_path: Path):
        from data.converter import convert

        src = tmp_path / "data.json"
        src.write_text(json.dumps([{"a": 1, "b": 2}, {"a": 3, "b": 4}]), encoding="utf-8")
        dest = tmp_path / "data.csv"
        convert(src, dest)
        with dest.open(newline="") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["a"] == "1"

    def test_csv_to_json(self, sample_csv: Path, tmp_path: Path):
        from data.converter import convert

        dest = tmp_path / "data.json"
        convert(sample_csv, dest)
        data = json.loads(dest.read_text())
        assert isinstance(data, list)
        assert len(data) == 3
        assert data[0]["name"] == "Alice"

    def test_unsupported_format_raises(self, tmp_path: Path):
        from data.converter import load_file

        src = tmp_path / "file.xml"
        src.write_text("<root/>")
        with pytest.raises(ValueError, match="Unsupported format"):
            load_file(src)

    def test_json_roundtrip(self, sample_json: Path, tmp_path: Path):
        from data.converter import convert, load_file

        dest = tmp_path / "copy.json"
        convert(sample_json, dest)
        original = load_file(sample_json)
        copy = load_file(dest)
        assert original == copy
