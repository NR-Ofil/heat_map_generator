# Building Executables

## Video Processor App

### Quick Build (Windows)

1. Install PyInstaller (if not already installed):
```bash
pip install pyinstaller
```

2. Run the build script:
```bash
python build_exe.py
```

Or simply double-click `build_exe.bat`

### Manual Build

```bash
pyinstaller --name=VideoProcessor --onefile --windowed --add-data "config.py;." --add-data "video_processor.py;." video_processor_app.py
```

### Output

The executable will be created in the `dist` folder as `VideoProcessor.exe`

---

## Heatmap Viewer App

### Quick Build (Windows)

1. Install PyInstaller (if not already installed):
```bash
pip install pyinstaller
```

2. Run the build script:
```bash
python build_viewer_exe.py
```

Or simply double-click `build_viewer_exe.bat`

### Manual Build

```bash
pyinstaller --name=HeatmapViewer --onefile --windowed --add-data "config.py;." --add-data "video_processor.py;." heatmap_viewer.py
```

### Output

The executable will be created in the `dist` folder as `HeatmapViewer.exe`

## Notes

- The `--onefile` option creates a single executable file (larger but easier to distribute)
- The `--windowed` option hides the console window (for GUI apps)
- All dependencies are bundled into the executable
- The executable is self-contained and can be run on Windows machines without Python installed

## Alternative: Build with Console (for debugging)

If you want to see console output for debugging, remove `--windowed`:

```bash
pyinstaller --name=VideoProcessor --onefile --add-data "config.py;." --add-data "video_processor.py;." video_processor_app.py
```

## Including Additional Files

If you need to include other files (like icons, data files, etc.), add them to the `datas` list in `build_exe.py`:

```python
datas = [
    ("config.py", "."),
    ("video_processor.py", "."),
    ("icon.ico", "."),  # Example: add icon file
]
```

