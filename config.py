"""
Configuration for red-spot heatmap processing.

Values are loaded from config.json located next to this file (or next to the
executable when running as a bundled app).  If config.json is missing or a key
is absent, the hard-coded defaults below are used instead.
"""

import json
import sys
import numpy as np
from pathlib import Path

# Locate config.json next to the exe (frozen) or next to this script (dev).
if getattr(sys, 'frozen', False):
    _BASE = Path(sys.executable).parent
else:
    _BASE = Path(__file__).parent

_CONFIG_FILE = _BASE / 'config.json'

_cfg = {}
if _CONFIG_FILE.exists():
    try:
        with open(_CONFIG_FILE, 'r') as _f:
            _cfg = json.load(_f)
    except Exception as _e:
        print(f"Warning: could not read {_CONFIG_FILE}: {_e}. Using defaults.")


def _get(key, default):
    return _cfg.get(key, default)


# === Video Processing ===
FRAME_STRIDE: int = _get('frame_stride', 1)

# === Red Detection (HSV) ===
# H in [0..179], S,V in [0..255]
_red = _cfg.get('red_detection', {})
LOWER_RED_1 = np.array(_red.get('lower_red_1', [0,   120, 80]),  dtype=np.uint8)
UPPER_RED_1 = np.array(_red.get('upper_red_1', [10,  255, 255]), dtype=np.uint8)
LOWER_RED_2 = np.array(_red.get('lower_red_2', [170, 120, 80]),  dtype=np.uint8)
UPPER_RED_2 = np.array(_red.get('upper_red_2', [179, 255, 255]), dtype=np.uint8)

# === Morphology (Noise Reduction) ===
KERNEL_SIZE: int = _cfg.get('morphology', {}).get('kernel_size', 3)

# === Persistent Red Pixel Removal ===
PERSISTENT_FRAC_THRESHOLD: float = _get('persistent_frac_threshold', 0.8)

# === Heatmap Visualization ===
BLUR_SIGMA: float = _get('blur_sigma', 2.0)
COLORMAP: str = _get('colormap', 'JET')

# === Overlay Settings ===
OVERLAY_ALPHA: float = _get('overlay_alpha', 0.55)
THRESHOLD_PCT: int = _get('threshold_pct', 180)

# === Output ===
OUTPUT_DIR: str = _get('output_dir', 'results_for_users')
