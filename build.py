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
from pathlib import Path

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
    # Ensure hooks directory exists and write a runtime hook that imports numpy first
    hooks_dir = Path('hooks')
    hooks_dir.mkdir(exist_ok=True)
    runtime_hook_path = hooks_dir / 'runtime_numpy_first.py'
    runtime_hook_path.write_text('''# PyInstaller runtime hook: import numpy before pygame to avoid dispatcher tracer issues\nimport os\n# Prefer bundled OpenBLAS/MKL and avoid stray site packages\nos.environ.pop("PYTHONPATH", None)\ntry:\n    import numpy  # noqa: F401\nexcept Exception as _e:\n    pass\n''')

    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules, collect_data_files, copy_metadata

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('data', 'data'),
        ('theme.json', '.'),
    ] + collect_data_files('numpy', include_py_files=True) + copy_metadata('numpy'),
    hiddenimports=(
        collect_submodules('numpy')
        + [
            'pygame_gui',
            'pymunk',
            'entities',
            'scenes',
            'ui',
            'utils',
        ]
    ),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['hooks/runtime_numpy_first.py'],
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
    upx=False,
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

def main():
    """Main build process."""
    print("🚀 SupermaulTD Build Script")
    print("=" * 50)
    
    # Check if we're on Windows (PyInstaller works best on Windows for Windows exes)
    if platform.system() != 'Windows':
        print("⚠️  Warning: This script is optimized for Windows builds.")
        print("   Building on other platforms may require adjustments.")
    
    # Step 1: Clean previous builds
    clean_build_dirs()
    
    # Step 2: Check dependencies
    if not check_dependencies():
        print("❌ Dependency check failed. Exiting.")
        return False
    
    # Step 3: Create spec file
    create_spec_file()
    
    # Step 4: Build executable
    if not build_executable():
        print("❌ Build failed. Exiting.")
        return False
    
    # Step 5: Create distribution package
    if not create_distribution_package():
        print("❌ Distribution package creation failed.")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 BUILD COMPLETE!")
    print("=" * 50)
    print("Your game is ready for distribution!")
    print("📁 Distribution folder: SupermaulTD_Distribution/")
    print("🎮 Executable: SupermaulTD_Distribution/SupermaulTD.exe")
    print("\nYou can now:")
    print("  • Test the executable")
    print("  • Zip the distribution folder")
    print("  • Share with others!")
    
    return True

if __name__ == '__main__':
    success = main()
    if not success:
        sys.exit(1)
