# GitHub Actions CI/CD

This directory contains automated workflows for the sBitx Branch Manager.

## Workflows

### 1. `test.yml` - Automated Testing
**Triggers:** Every push and pull request

**What it does:**
- Tests Python module imports
- Validates repository model functionality
- Tests config manager operations
- Runs basic code quality checks

**Status:** [![Tests](../../actions/workflows/test.yml/badge.svg)](../../actions/workflows/test.yml)

### 2. `build-executable.yml` - x86_64 Build
**Triggers:** Pushes to main/master, pull requests, releases

**What it does:**
- Builds standalone executable for x86_64 Linux
- Uses PyInstaller to bundle Python + dependencies
- Uploads artifact to GitHub Actions
- Attaches to releases automatically

**Output:** `sBitx-Branch-Manager-x86_64-linux`

**Use case:** Desktop Linux testing, development

### 3. `build-arm.yml` - ARM64 Build (Raspberry Pi)
**Triggers:** Pushes to main/master, version tags, releases

**What it does:**
- Builds standalone executable for ARM64 (Raspberry Pi)
- Uses QEMU emulation for cross-compilation
- Uploads artifact to GitHub Actions
- Attaches to releases automatically

**Output:** `sBitx-Branch-Manager-arm64-linux`

**Use case:** Raspberry Pi deployment, end users

## Downloading Builds

### From Actions Artifacts
1. Go to [Actions](../../actions) tab
2. Click on the latest successful workflow run
3. Download artifacts:
   - `sBitx-Branch-Manager-x86_64` (desktop Linux)
   - `sBitx-Branch-Manager-arm64` (Raspberry Pi)

**Note:** Artifacts are kept for 30 days

### From Releases
1. Go to [Releases](../../releases)
2. Download the appropriate version:
   - `sBitx-Branch-Manager-x86_64-linux` (desktop)
   - `sBitx-Branch-Manager-arm64-linux` (Raspberry Pi)

**Note:** Release assets are permanent

## Creating a Release

See [RELEASE_NOTES.md](RELEASE_NOTES.md) for detailed release instructions.

**Quick version:**
```bash
# Tag and push
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# Create release on GitHub
# Executables will be built and attached automatically
```

## Architecture Notes

### x86_64 Build
- Fast to build (~2-3 minutes)
- Runs on standard GitHub Actions runners
- Good for testing during development

### ARM64 Build
- Slower to build (~10-15 minutes)
- Uses QEMU emulation
- Required for Raspberry Pi compatibility
- Production-ready for end users

### Building Locally
For best results on Raspberry Pi, build locally:
```bash
./build_executable.sh
```

This ensures native ARM compilation without emulation overhead.

## Troubleshooting

### Build fails with "tkinter not found"
- Check `--hidden-import` flags in PyInstaller command
- Ensure Python has tkinter support

### ARM build times out
- QEMU emulation is slow
- Consider using self-hosted ARM runner
- Or build manually on Raspberry Pi

### Executable won't run
- Ensure correct architecture (x86_64 vs ARM64)
- Check executable permissions: `chmod +x sBitx-Branch-Manager`
- Verify dependencies are bundled

## Maintenance

### Updating Python Version
Edit all workflow files and change:
```yaml
python-version: '3.11'
```

### Updating PyInstaller Options
Edit the `pyinstaller` command in build workflows to add/remove options.

### Adding New Dependencies
If you add external Python packages:
1. Add to `requirements.txt`
2. Update workflow to install them
3. Add `--hidden-import` if needed

## Security

### GitHub Secrets
The workflows use `GITHUB_TOKEN` (automatically provided) for:
- Uploading release assets
- Accessing repository

No additional secrets are required.

### Artifact Access
- Actions artifacts: Accessible to repository collaborators
- Release assets: Public downloads

## Status

Check workflow status:
- [All Workflows](../../actions)
- [Recent Builds](../../actions/workflows/build-executable.yml)
- [Test Results](../../actions/workflows/test.yml)
