#!/bin/bash
# Build script for creating standalone sBitx Branch Manager executable

echo "=== sBitx Branch Manager - Build Executable ==="
echo ""

# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "PyInstaller not found. Installing..."
    pip3 install pyinstaller
    echo ""
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist
rm -f *.spec

# Build the executable
echo "Building executable..."
pyinstaller \
    --onefile \
    --windowed \
    --name "sBitx-Branch-Manager" \
    --add-data "config:config" \
    --hidden-import "tkinter" \
    --hidden-import "queue" \
    --hidden-import "threading" \
    main.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=== Build Successful! ==="
    echo ""
    echo "Executable location: dist/sBitx-Branch-Manager"
    echo "Size: $(du -h dist/sBitx-Branch-Manager | cut -f1)"
    echo ""
    echo "To run: ./dist/sBitx-Branch-Manager"
    echo "To install system-wide: sudo cp dist/sBitx-Branch-Manager /usr/local/bin/"
    echo ""
else
    echo ""
    echo "=== Build Failed ==="
    exit 1
fi
