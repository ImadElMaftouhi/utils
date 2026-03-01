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

def compress_image()->None:
    pass