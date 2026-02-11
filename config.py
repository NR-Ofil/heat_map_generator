"""
Configuration file for red-spot heatmap video processing.
Adjust these parameters to tune the detection and visualization.
"""

import numpy as np

# === Video Processing ===
# Sampling: process every Nth frame to speed up (1 = all frames)
FRAME_STRIDE = 1

# === Red Detection (HSV) Tuning ===
# H in [0..179], S,V in [0..255]
LOWER_RED_1 = np.array([0,   120, 80], dtype=np.uint8)
UPPER_RED_1 = np.array([10,  255, 255], dtype=np.uint8)
LOWER_RED_2 = np.array([170, 120, 80], dtype=np.uint8)
UPPER_RED_2 = np.array([179, 255, 255], dtype=np.uint8)

# === Morphology (Noise Reduction) ===
KERNEL_SIZE = 3

# === Persistent Red Pixel Removal ===
# If a pixel is red in >80% of processed frames, treat it as stuck/hot pixel and ignore it
PERSISTENT_FRAC_THRESHOLD = 0.8

# === Heatmap Visualization ===
# Gaussian blur sigma for smoothing
BLUR_SIGMA = 2.0

# Colormap type (options: JET, HOT, PLASMA, VIRIDIS, etc.)
COLORMAP = "JET"

# === Overlay Settings ===
OVERLAY_ALPHA = 0.55  # overlay strength (0..1)
THRESHOLD_PCT = 180   # threshold for showing only strong hotspots in overlay (0..255)

# === Output Settings ===
OUTPUT_DIR = "results_for_users"

