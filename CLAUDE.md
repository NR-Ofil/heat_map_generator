# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
pip install -r requirements.txt
```

Dependencies: `opencv-python-headless`, `numpy`, `Pillow`, `pyinstaller`. Tkinter is part of the Python standard library.

## Running the Applications

**CLI batch processor** (processes video files → saves PNG outputs directly):
```bash
python main.py path/to/video.mov       # single video
python main.py --all                   # all supported videos in current directory
python main.py                         # same as --all
```
Supported formats: `.mov`, `.mp4`, `.avi`, `.mkv`, `.webm`. Outputs go to `results_for_users/{video_name}/` as `heatmap.png`, `overlay.png`, `transparent.png`.

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

## Building Executables

```bash
python build_exe.py          # builds dist/VideoProcessor.exe
python build_viewer_exe.py   # builds dist/HeatmapViewer.exe
```

Distribute `config.json` alongside the `.exe` files so users can tune parameters without rebuilding. See [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) for manual PyInstaller commands.

## Architecture

### Core pipeline (`video_processor.py`)

All processing flows through four functions in sequence:
1. `process_video()` — reads frames at `FRAME_STRIDE` intervals, applies HSV red detection, accumulates detections into a float32 2D array (`acc`)
2. `remove_persistent_pixels()` — zeros out pixels red in ≥`PERSISTENT_FRAC_THRESHOLD` of frames (stuck/hot pixels)
3. `create_heatmap()` — normalizes the accumulator, applies Gaussian blur, maps through a colormap → returns `(heatmap_bgr, acc_u8)`
4. `create_overlay()` — blends heatmap onto a representative frame, masked to `THRESHOLD_PCT`

Red detection uses two HSV bands (`LOWER_RED_1`/`UPPER_RED_1` and `LOWER_RED_2`/`UPPER_RED_2`) because red wraps around hue=0/180 in OpenCV's HSV space.

### Two workflows, one core

**CLI workflow** (`main.py`): runs the full pipeline end-to-end and writes PNG files directly.

**GUI workflow** (`video_processor_app.py` → `heatmap_viewer.py`): splits at the accumulator. `video_processor_app.py` saves `{name}_matrix.npy` (accumulator after persistent-pixel removal) and `{name}_frame.npy` (user-selected representative frame). `heatmap_viewer.py` loads these and runs colormap/overlay interactively with sliders.

The "Open Heatmap Viewer" button in `video_processor_app.py` opens `heatmap_viewer.MainApp` as a `Toplevel` child window when running as a script, or launches `HeatmapViewer.exe` (expected next to the exe) when running frozen.

### Shared overlay widget (`overlay_gui.py`)

`OverlayGUI` is the interactive overlay panel used by both `heatmap_app.py` and `heatmap_viewer.py`. It takes `(root, matrix_file, frame_file, output_folder)` and handles all rendering and saving internally. Any change to overlay logic goes here only.

### Configuration (`config.py` + `config.json`)

`config.py` loads values from `config.json` (located next to the script or exe) and falls back to hard-coded defaults if the file is absent or a key is missing. The most impactful tunables:

- `frame_stride` — trade speed for temporal resolution
- `red_detection.*` — HSV thresholds for red detection sensitivity
- `persistent_frac_threshold` — fraction above which a pixel is treated as stuck/hot
- `blur_sigma`, `colormap`, `overlay_alpha`, `threshold_pct` — visualization parameters

The GUI apps read `config.COLORMAP` at render time, so changing `colormap` in `config.json` and restarting affects all overlay windows.
