"""Tests for the files module (rename, organize, convert)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRename:
    def test_build_new_name_counter(self):
        from files.rename import build_new_name

        result = build_new_name("photo_{n}", "img001", ".jpg", n=3, padding=3)
        assert result == "photo_003.jpg"

    def test_build_new_name_original_name(self):
        from files.rename import build_new_name

        result = build_new_name("{name}_copy", "photo", ".png", n=1, padding=0)
        assert result == "photo_copy.png"

    def test_build_new_name_no_padding(self):
        from files.rename import build_new_name

        result = build_new_name("file_{n}", "x", ".txt", n=7, padding=0)
        assert result == "file_7.txt"

    def test_rename_dry_run_no_changes(self, tmp_path: Path):
        from files.rename import rename_files

        src = tmp_path / "test.txt"
        src.write_text("hello")
        rename_files([src], pattern="renamed_{n}", start=1, padding=3, output_dir=None, dry_run=True)
        assert src.exists()  # original untouched

    def test_rename_in_place(self, tmp_path: Path):
        from files.rename import rename_files

        src = tmp_path / "old.txt"
        src.write_text("content")
        rename_files([src], pattern="new_{n}", start=1, padding=0, output_dir=None, dry_run=False)
        assert (tmp_path / "new_1.txt").exists()
        assert not src.exists()

    def test_rename_to_output_dir(self, tmp_path: Path):
        from files.rename import rename_files

        src = tmp_path / "a.txt"
        src.write_text("data")
        out = tmp_path / "renamed"
        rename_files([src], pattern="{name}_v2", start=1, padding=0, output_dir=out, dry_run=False)
        assert (out / "a_v2.txt").exists()


class TestOrganize:
    def test_organize_by_extension(self, tmp_path: Path):
        from files.organize import organize_by_extension

        (tmp_path / "a.jpg").write_bytes(b"")
        (tmp_path / "b.png").write_bytes(b"")
        (tmp_path / "c.jpg").write_bytes(b"")
        out = tmp_path / "organized"
        files = [tmp_path / "a.jpg", tmp_path / "b.png", tmp_path / "c.jpg"]
        groups = organize_by_extension(files, out, dry_run=False)
        assert "jpg" in groups
        assert "png" in groups
        assert (out / "jpg" / "a.jpg").exists()
        assert (out / "png" / "b.png").exists()

    def test_organize_by_extension_dry_run(self, tmp_path: Path):
        from files.organize import organize_by_extension

        src = tmp_path / "test.txt"
        src.write_text("hi")
        out = tmp_path / "out"
        organize_by_extension([src], out, dry_run=True)
        assert not out.exists()  # nothing created

    def test_classify_file_images(self):
        from files.organize import classify_file

        assert classify_file(Path("photo.jpg")) == "images"
        assert classify_file(Path("photo.PNG")) == "images"

    def test_classify_file_unknown(self):
        from files.organize import classify_file

        assert classify_file(Path("mystery.xyz")) == "other"


class TestConvert:
    def test_normalize_lf(self, tmp_path: Path):
        from files.convert import normalize_line_endings

        src = tmp_path / "crlf.txt"
        src.write_bytes(b"line1\r\nline2\r\n")
        dest = tmp_path / "lf.txt"
        normalize_line_endings(src, dest, "lf")
        assert dest.read_bytes() == b"line1\nline2\n"

    def test_normalize_crlf(self, tmp_path: Path):
        from files.convert import normalize_line_endings

        src = tmp_path / "lf.txt"
        src.write_bytes(b"line1\nline2\n")
        dest = tmp_path / "crlf.txt"
        normalize_line_endings(src, dest, "crlf")
        assert dest.read_bytes() == b"line1\r\nline2\r\n"

    def test_encoding_conversion(self, tmp_path: Path):
        from files.convert import convert_encoding

        src = tmp_path / "latin.txt"
        src.write_bytes("café".encode("latin-1"))
        dest = tmp_path / "utf8.txt"
        convert_encoding(src, dest, from_enc="latin-1", to_enc="utf-8")
        assert dest.read_text(encoding="utf-8") == "café"
