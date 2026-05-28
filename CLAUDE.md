# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
pip install -r requirements.txt
```

Dependencies: `opencv-python-headless`, `numpy`, `Pillow`, `pyinstaller`. Tkinter is used for all GUIs and is part of the Python standard library.

## Running the Applications

**CLI batch processor** (processes `.mov` files → saves PNG outputs):
```bash
python main.py path/to/video.mov       # single video
python main.py --all                   # all .mov files in current directory
python main.py                         # same as --all
```
Outputs go to `results_for_users/{video_name}/` as `heatmap.png`, `overlay.png`, `transparent.png`.

**GUI workflow — Step 1: Video Processor** (processes video → saves `.npy` intermediates):
```bash
python video_processor_app.py
```

**GUI workflow — Step 2: Heatmap Viewer** (loads `.npy` files → interactive overlay tuning):
```bash
python heatmap_viewer.py
```

**All-in-one GUI** (combines processing and viewing in one app):
```bash
python heatmap_app.py
```

**Legacy scripts** (hardcoded folder paths, for reference only):
```bash
python process1_integration.py   # generates cumulative_matrix.npy + representative_frame.npy
python process2_gui_overlay.py   # opens interactive overlay GUI
```

## Building Executables

```bash
python build_exe.py          # builds dist/VideoProcessor.exe
python build_viewer_exe.py   # builds dist/HeatmapViewer.exe
```

See [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) for manual PyInstaller commands and options.

## Architecture

### Core pipeline (`video_processor.py`)

All processing flows through four functions in sequence:
1. `process_video()` — reads frames at `FRAME_STRIDE` intervals, applies HSV red detection, accumulates detections into a float32 2D array (`acc`)
2. `remove_persistent_pixels()` — zeros out pixels that are red in ≥`PERSISTENT_FRAC_THRESHOLD` of frames (stuck/hot pixels)
3. `create_heatmap()` — normalizes the accumulator, applies Gaussian blur, maps through a colormap → returns `(heatmap_bgr, acc_u8)`
4. `create_overlay()` — blends heatmap onto a representative frame, masked to `THRESHOLD_PCT`

Red detection uses two HSV bands (`LOWER_RED_1`/`UPPER_RED_1` and `LOWER_RED_2`/`UPPER_RED_2`) because red wraps around hue=0/180 in OpenCV's HSV space.

### Two workflows, one core

**CLI workflow** (`main.py`): runs the full pipeline end-to-end and writes PNG files directly.

**GUI workflow** (`video_processor_app.py` → `heatmap_viewer.py`): splits the pipeline at the accumulator. `video_processor_app.py` saves `{name}_matrix.npy` (the accumulator after persistent-pixel removal) and `{name}_frame.npy` (the user-selected representative frame). `heatmap_viewer.py` loads these `.npy` files and runs colormap/overlay interactively with sliders.

The interactive overlay GUI (`OverlayGUI` class) adds two controls beyond `config.py` defaults: min/max threshold sliders and dynamic range (percentile-based) sliders. The `OverlayGUI` class is nearly identical across `heatmap_app.py`, `heatmap_viewer.py`, and `process2_gui_overlay.py` — keep them in sync when changing overlay logic.

### Configuration (`config.py`)

All tunables live here. The most impactful ones:
- `FRAME_STRIDE` — trade speed for temporal resolution
- `LOWER_RED_*` / `UPPER_RED_*` — HSV thresholds for red detection sensitivity
- `PERSISTENT_FRAC_THRESHOLD` — fraction above which a pixel is treated as stuck/hot
- `BLUR_SIGMA`, `COLORMAP`, `OVERLAY_ALPHA`, `THRESHOLD_PCT` — visualization parameters

The GUI apps read `config.COLORMAP` at render time, so changing it in `config.py` affects all open GUI windows after the next overlay update.
