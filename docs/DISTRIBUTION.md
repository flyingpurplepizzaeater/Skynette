# Distribution Guide

Guide for building and distributing Skynette executables and installers.

## Quick Start

```bash
# Build for current platform
python scripts/build.py

# Build for specific platform
python scripts/build.py --platform windows
python scripts/build.py --platform macos
python scripts/build.py --platform linux

# Build all platforms
python scripts/build.py --all
```

## Prerequisites

### All Platforms
- Python 3.11+
- PyInstaller: `pip install pyinstaller`
- Project dependencies: `pip install -e ".[dev]"`

### Windows
- UPX (optional, for compression)
- NSIS or Inno Setup (for installer)

### macOS
- Xcode Command Line Tools
- create-dmg (optional): `brew install create-dmg`

### Linux
- AppImage tools: `apt-get install appimage-builder`

## Building Executables

### Using PyInstaller Directly

```bash
# Build single-file executable
pyinstaller skynette.spec --clean

# Output in dist/Skynette
```

### Using Build Script

```bash
# Automated build with tests
python scripts/build.py

# Skip tests
python scripts/build.py --skip-tests
```

## Platform-Specific Instructions

### Windows

**Executable**: `dist/Skynette.exe`

**Create Installer** (TODO):
1. Install NSIS or Inno Setup
2. Run installer script
3. Output: `Skynette-Setup.exe`

### macOS

**App Bundle**: `dist/Skynette.app`

**Create DMG** (TODO):
```bash
create-dmg \
  --volname "Skynette" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --app-drop-link 600 185 \
  "Skynette.dmg" \
  "dist/Skynette.app"
```

### Linux

**Executable**: `dist/Skynette`

**Create AppImage** (TODO):
```bash
appimage-builder --recipe AppImageBuilder.yml
```

## Automated Releases

### GitHub Actions

Releases are automated via `.github/workflows/release.yml`:

1. **Create a tag**:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

2. **Workflow builds**:
   - Windows executable
   - macOS app bundle
   - Linux executable

3. **Creates GitHub Release** with all artifacts

### Manual Release

```bash
# Build all platforms
python scripts/build.py --all

# Create GitHub release
gh release create v0.1.0 \
  dist/Skynette.exe#Windows \
  dist/Skynette.app#macOS \
  dist/Skynette#Linux \
  --title "Skynette v0.1.0" \
  --notes "Release notes here"
```

## Version Management

Version is defined in `pyproject.toml`:

```toml
[project]
name = "skynette"
version = "0.1.0"
```

Update version:
1. Edit `pyproject.toml`
2. Commit: `git commit -m "Bump version to 0.2.0"`
3. Tag: `git tag v0.2.0`
4. Push: `git push --tags`

## Troubleshooting

### ImportError in built executable

Add missing module to `hiddenimports` in `skynette.spec`:

```python
hiddenimports = [
    'missing_module',
    ...
]
```

### Large executable size

1. Exclude unnecessary packages in `skynette.spec`
2. Use UPX compression: `--upx-dir=/path/to/upx`
3. Build with `--strip`

### macOS code signing

```bash
codesign --deep --force --sign "Developer ID" dist/Skynette.app
```

## Best Practices

1. **Test executables** on clean systems
2. **Include README** in distributions
3. **Version everything** consistently
4. **Sign executables** for Windows/macOS
5. **Provide checksums** (SHA256)

## Future Enhancements

- [ ] Windows MSI installer
- [ ] macOS DMG creation
- [ ] Linux AppImage/Snap/Flatpak
- [ ] Auto-update system
- [ ] Code signing automation
- [ ] Notarization for macOS

---

**Last Updated**: 2026-01-10
