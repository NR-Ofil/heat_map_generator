@echo off
echo Building Heatmap Viewer executable...
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

REM Run the build script
python build_viewer_exe.py

pause

