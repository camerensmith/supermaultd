# SupermaulTD Versioning System

This document explains how to manage versions and releases for SupermaulTD.

## 🏷️ Version Format

Versions follow semantic versioning with experimental suffixes:
- **Format**: `MAJOR.MINOR.PATCH-SUFFIX`
- **Example**: `0.3.2-experimental`

### Version Components
- **MAJOR**: Breaking changes, major rewrites
- **MINOR**: New features, significant improvements  
- **PATCH**: Bug fixes, small improvements
- **SUFFIX**: `experimental`, `beta`, `stable`, etc.

## 🚀 Quick Start

### Show Current Version
```bash
python version_manager.py show
```

### Update Version
```bash
# Increment patch version (0.3.2 -> 0.3.3)
python version_manager.py patch

# Increment minor version (0.3.2 -> 0.4.0)  
python version_manager.py minor

# Increment major version (0.3.2 -> 1.0.0)
python version_manager.py major

# Change suffix (0.3.2-experimental -> 0.3.2-beta)
python version_manager.py suffix beta
```

### Create Release
```bash
# Update version and create git tag (triggers GitHub Actions)
python version_manager.py release patch
```

## 🔧 Build Process

### Manual Build
```bash
# Build executable and create release package
python build.py
```

### Automated Build (GitHub Actions)
1. Create a git tag: `git tag v0.3.2-experimental`
2. Push the tag: `git push origin v0.3.2-experimental`
3. GitHub Actions will automatically build and create a release

## 📁 Generated Files

### Version Files
- `version.py` - Version definitions and utilities
- `version.json` - Machine-readable version info
- `RELEASE_NOTES.md` - Auto-generated release notes

### Build Outputs
- `SupermaulTD_Dist/` - Distribution folder with executable
- `releases/` - Release packages for GitHub
- `SupermaulTD_0.3.2_experimental.zip` - Ready-to-upload release

## 🎯 Release Workflow

### For Bug Fixes (Patch)
1. Fix the bug
2. Run: `python version_manager.py release patch`
3. GitHub Actions creates release automatically

### For New Features (Minor)
1. Add new features
2. Run: `python version_manager.py release minor`
3. GitHub Actions creates release automatically

### For Major Changes (Major)
1. Make breaking changes
2. Run: `python version_manager.py release major`
3. GitHub Actions creates release automatically

## 📝 Release Notes

Release notes are automatically generated in `RELEASE_NOTES.md` with:
- Bug fixes
- New features
- UI improvements
- Technical changes
- System requirements

## 🔄 GitHub Integration

### Automatic Releases
- Push a tag starting with `v` (e.g., `v0.3.2-experimental`)
- GitHub Actions builds the executable
- Creates a GitHub release with the zip file
- Uploads release notes as description

### Manual Releases
1. Run `python build.py`
2. Go to GitHub Releases page
3. Upload the zip file from `releases/` folder
4. Copy content from `RELEASE_NOTES.md` as description

## 🐛 Troubleshooting

### Version Not Updating
- Check if `version.py` is being imported correctly
- Ensure `update_version_file()` is called after changes

### Git Tag Issues
- Make sure you're in the git repository root
- Check if you have push permissions
- Verify the tag doesn't already exist

### Build Failures
- Check Python dependencies are installed
- Ensure PyInstaller is working
- Verify all asset files exist

## 📋 Current Version

Run `python version_manager.py show` to see the current version and build information.
