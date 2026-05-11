"""Shared test fixtures for the utils test suite."""

import csv
import io
import json
from pathlib import Path

import pytest


@pytest.fixture()
def sample_jpeg(tmp_path: Path) -> Path:
    pytest.importorskip("PIL", reason="Pillow required for image fixtures")
    from PIL import Image

    img = Image.new("RGB", (100, 100), color=(128, 64, 32))
    path = tmp_path / "sample.jpg"
    img.save(path, format="JPEG", quality=85)
    return path


@pytest.fixture()
def sample_png(tmp_path: Path) -> Path:
    pytest.importorskip("PIL", reason="Pillow required for image fixtures")
    from PIL import Image

    img = Image.new("RGBA", (100, 100), color=(0, 128, 255, 200))
    path = tmp_path / "sample.png"
    img.save(path, format="PNG")
    return path


@pytest.fixture()
def sample_pdf(tmp_path: Path) -> Path:
    pytest.importorskip("pypdf", reason="pypdf required for PDF fixtures")
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    path = tmp_path / "sample.pdf"
    with open(path, "wb") as fh:
        writer.write(fh)
    return path


@pytest.fixture()
def sample_pdf_multi(tmp_path: Path) -> Path:
    pytest.importorskip("pypdf", reason="pypdf required for PDF fixtures")
    from pypdf import PdfWriter

    writer = PdfWriter()
    for _ in range(5):
        writer.add_blank_page(width=612, height=792)
    path = tmp_path / "multi.pdf"
    with open(path, "wb") as fh:
        writer.write(fh)
    return path


@pytest.fixture()
def sample_csv(tmp_path: Path) -> Path:
    path = tmp_path / "sample.csv"
    rows = [
        {"name": "Alice", "age": "30", "city": "Paris"},
        {"name": "Bob", "age": "25", "city": "London"},
        {"name": "Carol", "age": "35", "city": "Paris"},
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["name", "age", "city"])
        writer.writeheader()
        writer.writerows(rows)
    return path


@pytest.fixture()
def sample_json(tmp_path: Path) -> Path:
    path = tmp_path / "sample.json"
    data = {"name": "Alice", "age": 30, "tags": ["python", "utils"]}
    path.write_text(json.dumps(data), encoding="utf-8")
    return path
