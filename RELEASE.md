# Release Process

This document describes the process for creating and publishing releases of Skynette.

## Overview

Skynette uses automated GitHub Actions workflows to:
1. Build executables for Windows, macOS, and Linux
2. Create a Python package for PyPI
3. Create a GitHub Release with all artifacts
4. Publish to PyPI (for stable releases)

## Release Types

- **Stable Release**: `v1.0.0`, `v2.1.3` - Published to PyPI and GitHub
- **Pre-release**: `v1.0.0-alpha.1`, `v1.0.0-beta.2`, `v1.0.0-rc.1` - Published to GitHub only
- **Development**: `v1.0.0-dev.1` - Not automatically released

## Creating a Release

### Prerequisites

1. Ensure all tests pass on the main branch
2. Update `CHANGELOG.md` with release notes
3. Update version number in `pyproject.toml` if needed
4. Commit and push all changes

### Step 1: Create and Push a Git Tag

```bash
# Stable release
git tag -a v2.0.0 -m "Release version 2.0.0"

# Pre-release (alpha, beta, rc)
git tag -a v2.0.0-beta.1 -m "Release version 2.0.0-beta.1"

# Push the tag
git push origin v2.0.0
```

### Step 2: Wait for GitHub Actions

The release workflow will automatically:

1. **Build Windows executable** (~10-15 minutes)
   - Creates standalone Windows application
   - Output: `Skynette-Windows.zip`

2. **Build macOS app** (~10-15 minutes)
   - Creates macOS application bundle
   - Output: `Skynette-macOS.zip` and `Skynette.dmg` (if create-dmg is available)

3. **Build Linux packages** (~10-15 minutes)
   - Creates AppImage, .deb package, and tarball
   - Output: `Skynette-*.AppImage`, `skynette_*.deb`, `Skynette-Linux.tar.gz`

4. **Build PyPI package** (~2-3 minutes)
   - Creates wheel and source distribution
   - Output: `skynette-*.whl` and `skynette-*.tar.gz`

5. **Create GitHub Release** (~1-2 minutes)
   - Creates release with all artifacts
   - Generates release notes from commits
   - Adds SHA256 checksums for all files

6. **Publish to PyPI** (stable releases only, ~1-2 minutes)
   - Uploads wheel and source distribution to PyPI
   - Only runs for stable releases (not alpha/beta/rc)
   - Requires PyPI trusted publishing to be configured

### Step 3: Verify the Release

1. Check the [Releases](https://github.com/flyingpurplepizzaeater/Skynette/releases) page
2. Verify all artifacts are present:
   - ✅ Windows ZIP
   - ✅ macOS ZIP/DMG
   - ✅ Linux AppImage
   - ✅ Linux .deb
   - ✅ Linux tarball
   - ✅ SHA256SUMS.txt
3. For stable releases, verify on PyPI: https://pypi.org/project/skynette/
4. Test installation:
   ```bash
   pip install skynette==2.0.0
   skynette --version
   ```

## Manual Release (Alternative)

If you need to create a release manually:

### Build Executables

```bash
# Install build dependencies
pip install -e ".[dev]"
pip install pyinstaller

# Build for current platform
python build_all.py

# Or build for specific platform
python build_windows.py  # Windows
python build_macos.py    # macOS
python build_linux.py    # Linux
```

### Build PyPI Package

```bash
# Install build tools
pip install build twine

# Build package
python -m build

# Check package
twine check dist/*

# Upload to PyPI (requires credentials)
twine upload dist/*
```

### Create GitHub Release

1. Go to https://github.com/flyingpurplepizzaeater/Skynette/releases/new
2. Choose the tag you created
3. Add release title and description
4. Upload the artifacts
5. Mark as pre-release if applicable
6. Publish release

## PyPI Publishing Setup

To enable automatic PyPI publishing, you need to configure trusted publishing:

1. Go to https://pypi.org/manage/account/publishing/
2. Add a new publisher:
   - **PyPI Project Name**: `skynette`
   - **Owner**: `flyingpurplepizzaeater`
   - **Repository name**: `Skynette`
   - **Workflow name**: `release.yml`
   - **Environment name**: (leave empty)

3. The workflow uses OIDC (OpenID Connect) for secure publishing without API tokens

## Troubleshooting

### Build Failures

- **Windows**: Ensure PyInstaller is compatible with Python version
- **macOS**: May need to install create-dmg (`brew install create-dmg`)
- **Linux**: Ensure appimagetool is available and executable

### PyPI Upload Failures

- **Authentication Error**: Verify trusted publishing is configured correctly
- **Version Conflict**: Version already exists on PyPI (increment version)
- **Metadata Error**: Check `pyproject.toml` for invalid fields

### Missing Artifacts

- Check the GitHub Actions logs for build failures
- Some artifacts (DMG, AppImage) may be optional and skip on failure
- Ensure all platform builds succeeded

## Version Numbering

Skynette follows [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH** (e.g., `2.1.3`)
  - MAJOR: Breaking changes
  - MINOR: New features (backward compatible)
  - PATCH: Bug fixes (backward compatible)

- **Pre-release suffixes**:
  - `-alpha.N`: Early testing, unstable
  - `-beta.N`: Feature complete, testing
  - `-rc.N`: Release candidate, final testing

## Release Checklist

Before creating a release:

- [ ] All tests pass on main branch
- [ ] Update `CHANGELOG.md` with changes
- [ ] Update version in `pyproject.toml`
- [ ] Update version in README badges if needed
- [ ] Commit and push all changes
- [ ] Create and push git tag
- [ ] Wait for GitHub Actions to complete
- [ ] Verify all artifacts are available
- [ ] Test installation from PyPI (stable releases)
- [ ] Announce release (GitHub Discussions, Twitter, etc.)

## Post-Release

After a successful release:

1. Update documentation if needed
2. Announce in GitHub Discussions
3. Update website/blog with release announcement
4. Monitor issues for release-related bugs
5. Plan next release based on roadmap

## Support

For questions about the release process, contact the maintainers or open an issue.
