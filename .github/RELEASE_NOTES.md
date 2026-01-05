# Creating a Release

## Automated Builds

When you create a release on GitHub, the CI/CD pipeline will automatically:

1. Build executables for both x86_64 and ARM64 (Raspberry Pi)
2. Upload them as release assets
3. Make them available for download

## Steps to Create a Release

### 1. Tag the Release

```bash
# Create and push a version tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

### 2. Create Release on GitHub

1. Go to your repository on GitHub
2. Click "Releases" → "Create a new release"
3. Select the tag you just created (v1.0.0)
4. Fill in release title and description
5. Click "Publish release"

### 3. Wait for Builds

The GitHub Actions will automatically:
- Build `sBitx-Branch-Manager-x86_64-linux` (for desktop Linux)
- Build `sBitx-Branch-Manager-arm64-linux` (for Raspberry Pi)
- Attach both to the release

### 4. Downloads

Users can download the appropriate version:
- **Raspberry Pi users**: Download `sBitx-Branch-Manager-arm64-linux`
- **Desktop Linux users**: Download `sBitx-Branch-Manager-x86_64-linux`

## Manual Build (Alternative)

If you prefer to build manually on a Raspberry Pi:

```bash
./build_executable.sh
```

This ensures the executable is built natively for the exact architecture.

## Version Numbering

Follow semantic versioning:
- `v1.0.0` - Major release
- `v1.1.0` - Minor release (new features)
- `v1.0.1` - Patch release (bug fixes)

## Release Checklist

- [ ] All tests pass
- [ ] Update version in code if needed
- [ ] Update CHANGELOG.md
- [ ] Create git tag
- [ ] Push tag to GitHub
- [ ] Create release on GitHub
- [ ] Verify artifacts are uploaded
- [ ] Test downloaded executables
