# 📊 data

Utilities for parsing, transforming, and working with structured data formats.

## Scripts

| Script | Description |
|--------|-------------|
| `json_tools.py` | Format, validate, and query JSON files |
| `csv_tools.py` | Clean, filter, and transform CSV files |
| `converter.py` | Convert between JSON, CSV, YAML, and TOML |

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Pretty-print and validate JSON
python json_tools.py --input data.json --pretty

# Filter CSV rows
python csv_tools.py --input data.csv --filter "age>30" --output filtered.csv

# Convert JSON to CSV
python converter.py --input data.json --output data.csv
```

## Dependencies

```
pyyaml>=6.0
tomli>=2.0.0
```
