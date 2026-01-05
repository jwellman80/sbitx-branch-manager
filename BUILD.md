# Building Standalone Executable

## Overview

The sBitx Branch Manager can be packaged into a standalone executable that includes Python and all dependencies. This makes it easy to distribute to testers without requiring Python setup.

## Quick Build

```bash
./build_executable.sh
```

The executable will be created at: `dist/sBitx-Branch-Manager`

## Manual Build

If you prefer to build manually:

### 1. Install PyInstaller

```bash
pip3 install pyinstaller
```

### 2. Build the Executable

```bash
pyinstaller \
    --onefile \
    --windowed \
    --name "sBitx-Branch-Manager" \
    --add-data "config:config" \
    main.py
```

### 3. Find the Executable

The executable will be in `dist/sBitx-Branch-Manager`

## Build Options Explained

- `--onefile`: Creates a single executable file (easier to distribute)
- `--windowed`: Prevents console window from appearing (GUI only)
- `--name`: Sets the executable name
- `--add-data`: Includes the config directory in the bundle

## Running the Executable

```bash
# From the build directory
./dist/sBitx-Branch-Manager

# Or install system-wide
sudo cp dist/sBitx-Branch-Manager /usr/local/bin/
sbitx-branch-manager
```

## Desktop Integration

To add a desktop launcher:

```bash
# Copy the .desktop file
mkdir -p ~/.local/share/applications
cp sbitx-branch-manager.desktop ~/.local/share/applications/

# Update path in the .desktop file if needed
nano ~/.local/share/applications/sbitx-branch-manager.desktop
```

## Distribution

To distribute to other Raspberry Pi users:

1. **Build the executable** on a Raspberry Pi (ARM architecture)
2. **Share the executable file**: `dist/sBitx-Branch-Manager`
3. **Recipients need**:
   - Raspberry Pi OS (or compatible Linux)
   - Git installed
   - Build tools for sBitx (gcc, make, etc.)

**Note**: The executable is architecture-specific. Build on Raspberry Pi for Raspberry Pi users, build on x86_64 Linux for desktop Linux users.

## File Size

The standalone executable will be approximately:
- **15-25 MB** (includes Python interpreter and all libraries)

## Troubleshooting

### "Permission denied" error
```bash
chmod +x dist/sBitx-Branch-Manager
```

### Missing dependencies
If the executable fails to run, rebuild without `--onefile`:
```bash
pyinstaller --name "sBitx-Branch-Manager" main.py
# Creates dist/sBitx-Branch-Manager/ directory with all files
```

### PyInstaller not found
```bash
pip3 install --upgrade pyinstaller
```

## Advanced: One-Click Installer Script

Create a simple installer for end users:

```bash
#!/bin/bash
# install-sbitx-manager.sh

echo "Installing sBitx Branch Manager..."

# Copy executable
sudo cp sBitx-Branch-Manager /usr/local/bin/
sudo chmod +x /usr/local/bin/sBitx-Branch-Manager

# Create desktop entry
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/sbitx-branch-manager.desktop <<EOF
[Desktop Entry]
Name=sBitx Branch Manager
Comment=Switch between sBitx repositories and branches
Exec=/usr/local/bin/sBitx-Branch-Manager
Icon=applications-development
Terminal=true
Type=Application
Categories=Development;Utility;
EOF

echo "Installation complete!"
echo "Run from terminal: sBitx-Branch-Manager"
echo "Or find it in your applications menu"
```

## Updating

To update the application:
1. Get the new executable
2. Replace the old one:
   ```bash
   sudo cp sBitx-Branch-Manager /usr/local/bin/
   ```

Your configuration (repositories list) is stored separately in `~/.config/sbitx_branch_manager/` and won't be affected by updates.
