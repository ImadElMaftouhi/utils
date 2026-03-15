# 📂 files

Utilities for general file manipulation, organization, and format conversion.

## Scripts

| Script | Description |
|--------|-------------|
| `rename.py` | Batch rename files with patterns or regex |
| `organize.py` | Sort files into folders by type or date |
| `convert.py` | Convert between text-based file formats |

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Batch rename files
python rename.py --dir ./photos --pattern "photo_{n}"

# Organize files by extension
python organize.py --dir ./downloads --by extension

# Convert CSV to JSON
python convert.py --input data.csv --output data.json
```

## Dependencies

```
# No external dependencies required for most scripts
```
