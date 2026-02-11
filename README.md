# Red-Spot Heatmap Video Processor

A Python project for generating heatmaps from video files by detecting and tracking red spots over time. This tool processes video frames to identify red pixels, removes persistent/hot pixels, and creates visual heatmap overlays.

## Features

- **Red pixel detection** using HSV color space (handles red wrapping around 0/180)
- **Persistent pixel removal** to filter out stuck/hot pixels
- **Multiple output formats**:
  - Standalone heatmap image
  - Heatmap overlay on representative frame
  - Transparent PNG heatmap layer
- **Batch processing** support for multiple video files
- **Configurable parameters** for tuning detection and visualization

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Process a single video file:
```bash
python main.py path/to/your/video.mov
```

### Process all .mov files in current directory:
```bash
python main.py --all
```

Or simply:
```bash
python main.py
```

### Output

All output files are saved to the `results_for_users/` directory. Each video gets its own subfolder:
- `results_for_users/{video_name}/heatmap.png` - Standalone heatmap visualization
- `results_for_users/{video_name}/overlay.png` - Heatmap overlaid on representative frame
- `results_for_users/{video_name}/transparent.png` - Transparent heatmap layer (RGBA)

## Configuration

Edit `config.py` to adjust processing parameters:

- **FRAME_STRIDE**: Process every Nth frame (1 = all frames)
- **Red detection thresholds**: HSV ranges for red color detection
- **PERSISTENT_FRAC_THRESHOLD**: Fraction threshold for removing stuck pixels
- **BLUR_SIGMA**: Gaussian blur strength for smoothing
- **COLORMAP**: Heatmap colormap (JET, HOT, PLASMA, VIRIDIS)
- **OVERLAY_ALPHA**: Overlay transparency (0-1)
- **THRESHOLD_PCT**: Minimum intensity to show in overlay (0-255)

## Project Structure

```
.
├── main.py              # Main entry point
├── video_processor.py   # Core video processing functions
├── config.py            # Configuration parameters
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── results_for_users/  # Output directory (created automatically)
```

## How It Works

1. **Video Reading**: Opens video file and reads frames
2. **Red Detection**: Converts each frame to HSV and detects red pixels using two bands (wraps around 0/180)
3. **Noise Reduction**: Applies morphological operations to clean up small speckles
4. **Accumulation**: Tracks how often each pixel is red across all frames
5. **Persistent Pixel Removal**: Removes pixels that are red in too many frames (likely stuck/hot pixels)
6. **Heatmap Generation**: Normalizes and applies colormap to create visualization
7. **Overlay Creation**: Blends heatmap with representative frame for context

## Notes

- The script processes videos frame by frame, which can be memory-intensive for large videos
- Adjust `FRAME_STRIDE` to speed up processing (at the cost of temporal resolution)
- Tune HSV thresholds in `config.py` if red detection is too sensitive or not sensitive enough

