#!/usr/bin/env python3
"""
Build script for SupermaulTD game distribution.
This script creates a distributable executable using PyInstaller.
"""

import os
import sys
import subprocess
import shutil
import platform
import json
import zipfile
from pathlib import Path
from datetime import datetime
from version import get_version, get_version_info, update_version_file

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{'='*50}")
    print(f"🔄 {description}")
    print(f"{'='*50}")
    print(f"Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✅ Success!")
        if result.stdout:
            print("Output:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stdout:
            print("Output:", e.stdout)
        if e.stderr:
            print("Error:", e.stderr)
        return False

def clean_build_dirs():
    """Clean previous build artifacts."""
    print("\n🧹 Cleaning previous build artifacts...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['*.spec']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  Removed {dir_name}/")
    
    # Clean .spec files
    for spec_file in Path('.').glob('*.spec'):
        spec_file.unlink()
        print(f"  Removed {spec_file}")

def check_dependencies():
    """Check if required dependencies are installed."""
    print("\n🔍 Checking dependencies...")
    
    required_packages = ['pygame', 'pygame_gui', 'pyinstaller', 'pymunk']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        
        install_cmd = f"{sys.executable} -m pip install {' '.join(missing_packages)}"
        if not run_command(install_cmd, "Installing missing packages"):
            print("❌ Failed to install missing packages. Please install them manually:")
            print(f"   {sys.executable} -m pip install {' '.join(missing_packages)}")
            return False
    
    return True

def create_spec_file():
    """Create a PyInstaller spec file for better control."""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('data', 'data'),
        ('theme.json', '.'),
    ],
    hiddenimports=[
        'pygame_gui',
        'pymunk',
        'entities',
        'scenes', 
        'ui',
        'utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SupermaulTD',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one
)
'''
    
    with open('SupermaulTD.spec', 'w') as f:
        f.write(spec_content)
    
    print("✅ Created SupermaulTD.spec file")

def build_executable():
    """Build the executable using PyInstaller."""
    print("\n🔨 Building executable...")
    
    # Use the spec file for better control
    build_cmd = f"{sys.executable} -m PyInstaller SupermaulTD.spec --clean"
    
    if not run_command(build_cmd, "Building executable with PyInstaller"):
        print("❌ Build failed!")
        return False
    
    return True

def create_distribution_package():
    """Create a clean distribution package."""
    print("\n📦 Creating distribution package...")
    
    dist_dir = Path('dist')
    if not dist_dir.exists():
        print("❌ Dist directory not found!")
        return False
    
    # Find the executable
    exe_files = list(dist_dir.glob('SupermaulTD.exe'))
    if not exe_files:
        print("❌ Executable not found in dist directory!")
        return False
    
    exe_path = exe_files[0]
    
    # Create a clean distribution folder
    package_dir = Path('SupermaulTD_Dist')
    if package_dir.exists():
        shutil.rmtree(package_dir)
    
    package_dir.mkdir()
    
    # Copy executable
    shutil.copy2(exe_path, package_dir / 'SupermaulTD.exe')
    print(f"  ✅ Copied {exe_path.name}")
    
    # Copy assets and data directories
    for dir_name in ['assets', 'data']:
        if os.path.exists(dir_name):
            shutil.copytree(dir_name, package_dir / dir_name)
            print(f"  ✅ Copied {dir_name}/")
    
    # Copy theme.json if it exists
    if os.path.exists('theme.json'):
        shutil.copy2('theme.json', package_dir / 'theme.json')
        print("  ✅ Copied theme.json")
    
    # Create a README for the distribution
    readme_content = """# SupermaulTD

A tower defense game built with Python and Pygame.

## How to Run

1. Double-click `SupermaulTD.exe` to start the game
2. Use the mouse to interact with the game interface
3. Select races and place towers to defend against waves of enemies

## System Requirements

- Windows 10 or later
- No additional software required (all dependencies included)

## Controls

- Mouse: Navigate menus and place towers
- ESC: Exit game
- Left Click: Select and place towers
- Right Click: Cancel tower placement

Enjoy the game!

---
Built with Python, Pygame, and PyInstaller
"""
    
    with open(package_dir / 'README.txt', 'w') as f:
        f.write(readme_content)
    
    print("  ✅ Created README.txt")
    
    print(f"\n🎉 Distribution package created: {package_dir}")
    print(f"   Size: {get_folder_size(package_dir):.1f} MB")
    
    return True

def get_folder_size(folder_path):
    """Get the size of a folder in MB."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if os.path.exists(filepath):
                total_size += os.path.getsize(filepath)
    return total_size / (1024 * 1024)  # Convert to MB

def update_version_info():
    """Update version information and create version files."""
    print("\n📝 Updating version information...")
    
    version_info = get_version_info()
    print(f"  Current version: {version_info['version']}")
    print(f"  Build date: {version_info['build_date']}")
    
    # Create version.json for GitHub releases
    version_data = {
        "version": version_info['version'],
        "build_date": version_info['build_date'],
        "build_timestamp": version_info['build_timestamp'],
        "platform": platform.system(),
        "python_version": sys.version.split()[0],
        "changelog": {
            "v0.3.2-experimental": [
                "Fixed Vortex Monument placement bug",
                "Fixed limited tower placement issues", 
                "Added visual feedback for tower limits",
                "Updated tower selector UI with count display",
                "Enhanced placement validation system"
            ]
        }
    }
    
    with open('version.json', 'w') as f:
        json.dump(version_data, f, indent=2)
    
    print("  ✅ Created version.json")
    
    # Update version in main.py if it exists
    if os.path.exists('main.py'):
        with open('main.py', 'r') as f:
            content = f.read()
        
        # Add version display if not already present
        if 'version' not in content.lower():
            version_import = "from version import get_version\n"
            version_display = f'    print(f"SupermaulTD v{get_version()}")\n'
            
            # Add import at the top
            if 'from version import' not in content:
                lines = content.split('\n')
                import_line = 0
                for i, line in enumerate(lines):
                    if line.startswith('import ') or line.startswith('from '):
                        import_line = i + 1
                    elif line.strip() == '':
                        continue
                    else:
                        break
                lines.insert(import_line, version_import)
                content = '\n'.join(lines)
            
            # Add version display in main function
            if 'def main():' in content and 'print(f"SupermaulTD v' not in content:
                content = content.replace(
                    'def main():',
                    f'def main():\n    print(f"SupermaulTD v{get_version()}")\n    print("=" * 50)'
                )
        
        with open('main.py', 'w') as f:
            f.write(content)
    
    return version_info

def create_github_release_notes():
    """Create release notes for GitHub."""
    version_info = get_version_info()
    version = version_info['version']
    
    release_notes = f"""# SupermaulTD {version}

## 🎮 Game Updates

### 🐛 Bug Fixes
- **Fixed Vortex Monument placement bug** - Limited towers now place correctly
- **Fixed tower limit enforcement** - Proper validation prevents placement when limit reached
- **Fixed missing return statement** - Tower placement logic now works as intended

### ✨ New Features  
- **Visual feedback for tower limits** - Red floating text when limit reached
- **Enhanced tower selector UI** - Shows current count vs limit (e.g., "Vortex Monument (2/5)")
- **Success placement feedback** - Green floating text confirms successful placement
- **Improved placement validation** - Better error handling and user feedback

### 🎨 UI Improvements
- Tower selector buttons now display limit counts
- Floating text effects for placement feedback
- Better visual indicators for limited towers

## 🔧 Technical Changes
- Enhanced tower placement validation system
- Improved error handling in placement logic
- Added comprehensive debug system (removed in final build)
- Updated build pipeline with versioning

## 📋 System Requirements
- Windows 10 or later
- No additional software required (all dependencies included)

## 🚀 How to Play
1. Double-click `SupermaulTD.exe` to start
2. Select your race(s) in the main menu
3. Place towers to defend against enemy waves
4. Limited towers (like Vortex Monument) have a maximum count of 5

---
**Build Date:** {version_info['build_date']}  
**Platform:** {platform.system()}  
**Python Version:** {sys.version.split()[0]}

Enjoy the game! 🎯
"""
    
    with open('RELEASE_NOTES.md', 'w') as f:
        f.write(release_notes)
    
    print("  ✅ Created RELEASE_NOTES.md")
    return release_notes

def create_release_package(version_info):
    """Create a release package for GitHub."""
    print("\n📦 Creating release package...")
    
    version = version_info['version']
    package_name = f"SupermaulTD_{version.replace('-', '_')}"
    
    # Create release directory
    release_dir = Path('releases')
    release_dir.mkdir(exist_ok=True)
    
    package_dir = release_dir / package_name
    if package_dir.exists():
        shutil.rmtree(package_dir)
    
    package_dir.mkdir()
    
    # Copy distribution files
    dist_dir = Path('SupermaulTD_Dist')
    if dist_dir.exists():
        for item in dist_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, package_dir / item.name)
            else:
                shutil.copytree(item, package_dir / item.name)
        print(f"  ✅ Copied distribution files")
    
    # Copy additional files
    additional_files = [
        'README.md',
        'RELEASE_NOTES.md', 
        'version.json',
        'requirements.txt'
    ]
    
    for file_name in additional_files:
        if os.path.exists(file_name):
            shutil.copy2(file_name, package_dir / file_name)
            print(f"  ✅ Copied {file_name}")
    
    # Create zip file
    zip_path = release_dir / f"{package_name}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_path = os.path.relpath(file_path, package_dir)
                zipf.write(file_path, arc_path)
    
    print(f"  ✅ Created {zip_path.name}")
    print(f"  📁 Release package: {package_dir}")
    print(f"  📦 Zip file: {zip_path}")
    
    return zip_path

def main():
    """Main build process."""
    print("🚀 SupermaulTD Build Script")
    print("=" * 50)
    
    # Check if we're on Windows (PyInstaller works best on Windows for Windows exes)
    if platform.system() != 'Windows':
        print("⚠️  Warning: This script is optimized for Windows builds.")
        print("   Building on other platforms may require adjustments.")
    
    # Step 1: Update version information
    version_info = update_version_info()
    
    # Step 2: Clean previous builds
    clean_build_dirs()
    
    # Step 3: Check dependencies
    if not check_dependencies():
        print("❌ Dependency check failed. Exiting.")
        return False
    
    # Step 4: Create spec file
    create_spec_file()
    
    # Step 5: Build executable
    if not build_executable():
        print("❌ Build failed. Exiting.")
        return False
    
    # Step 6: Create distribution package
    if not create_distribution_package():
        print("❌ Distribution package creation failed.")
        return False
    
    # Step 7: Create GitHub release notes
    create_github_release_notes()
    
    # Step 8: Create release package
    zip_path = create_release_package(version_info)
    
    print("\n" + "=" * 50)
    print("🎉 BUILD COMPLETE!")
    print("=" * 50)
    print(f"Version: {version_info['version']}")
    print(f"Build Date: {version_info['build_date']}")
    print("\n📁 Files created:")
    print(f"  • Distribution folder: SupermaulTD_Dist/")
    print(f"  • Release package: {zip_path}")
    print(f"  • Release notes: RELEASE_NOTES.md")
    print(f"  • Version info: version.json")
    print("\n🚀 Ready for GitHub release!")
    print("\nNext steps:")
    print("  1. Test the executable")
    print("  2. Commit changes to git")
    print("  3. Create GitHub release with the zip file")
    print("  4. Upload RELEASE_NOTES.md as release description")
    
    return True

if __name__ == '__main__':
    success = main()
    if not success:
        sys.exit(1)
