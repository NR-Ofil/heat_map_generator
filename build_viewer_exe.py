"""
Build script to create executable from heatmap_viewer.py
Run: python build_viewer_exe.py
"""

import PyInstaller.__main__
import sys
from pathlib import Path

# Define the main script
main_script = "heatmap_viewer.py"

# Additional data files to include
datas = [
    ("config.py", "."),
    ("video_processor.py", "."),
]

# Hidden imports (modules that PyInstaller might not detect automatically)
hiddenimports = [
    "cv2",
    "numpy",
    "PIL",
    "tkinter",
    "tkinter.ttk",
    "tkinter.filedialog",
    "tkinter.messagebox",
]

# PyInstaller options
options = [
    main_script,
    "--name=HeatmapViewer",
    "--onefile",  # Create a single executable file
    "--windowed",  # No console window (GUI app)
    "--icon=NONE",  # You can add an icon file later if needed
    "--clean",  # Clean cache before building
]

# Add data files
for src, dst in datas:
    options.extend(["--add-data", f"{src};{dst}"])

# Add hidden imports
for imp in hiddenimports:
    options.extend(["--hidden-import", imp])

print("Building Heatmap Viewer executable...")
print(f"Command: pyinstaller {' '.join(options)}")
print()

# Run PyInstaller
PyInstaller.__main__.run(options)

print()
print("Build complete! Check the 'dist' folder for HeatmapViewer.exe")

