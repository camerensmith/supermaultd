#!/usr/bin/env python3
"""
Test script to verify the build process works correctly.
Run this after building to test the executable.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def test_executable():
    """Test if the built executable runs without crashing."""
    print("🧪 Testing built executable...")
    
    exe_path = Path("SupermaulTD_Distribution/SupermaulTD.exe")
    
    if not exe_path.exists():
        print("❌ Executable not found!")
        print(f"   Expected: {exe_path}")
        return False
    
    print(f"✅ Found executable: {exe_path}")
    
    # Test if executable starts (we'll kill it after a few seconds)
    try:
        print("🚀 Starting executable test...")
        process = subprocess.Popen([str(exe_path)], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # Let it run for 3 seconds
        time.sleep(3)
        
        # Check if it's still running (good sign)
        if process.poll() is None:
            print("✅ Executable started successfully!")
            process.terminate()
            process.wait()
            return True
        else:
            # Process ended, check for errors
            stdout, stderr = process.communicate()
            print("❌ Executable crashed immediately!")
            if stderr:
                print(f"Error: {stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to start executable: {e}")
        return False

def test_assets():
    """Test if all required assets are present."""
    print("\n📁 Testing asset files...")
    
    required_dirs = [
        "SupermaulTD_Distribution/assets",
        "SupermaulTD_Distribution/data"
    ]
    
    required_files = [
        "SupermaulTD_Distribution/SupermaulTD.exe",
        "SupermaulTD_Distribution/README.txt"
    ]
    
    all_good = True
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"  ✅ {dir_path}")
        else:
            print(f"  ❌ {dir_path} (missing)")
            all_good = False
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} (missing)")
            all_good = False
    
    return all_good

def get_package_size():
    """Get the size of the distribution package."""
    dist_dir = Path("SupermaulTD_Distribution")
    if not dist_dir.exists():
        return 0
    
    total_size = 0
    for file_path in dist_dir.rglob("*"):
        if file_path.is_file():
            total_size += file_path.stat().st_size
    
    return total_size / (1024 * 1024)  # MB

def main():
    """Run all tests."""
    print("🧪 SupermaulTD Build Test Suite")
    print("=" * 40)
    
    # Test 1: Check if distribution exists
    if not os.path.exists("SupermaulTD_Distribution"):
        print("❌ Distribution folder not found!")
        print("   Run the build script first: python build.py")
        return False
    
    # Test 2: Check assets
    assets_ok = test_assets()
    
    # Test 3: Test executable (optional - might be slow)
    print("\n⚠️  Executable test will start the game for 3 seconds...")
    response = input("Run executable test? (y/N): ").lower().strip()
    
    exe_ok = True
    if response == 'y':
        exe_ok = test_executable()
    else:
        print("⏭️  Skipping executable test")
    
    # Test 4: Package size
    size_mb = get_package_size()
    print(f"\n📦 Package size: {size_mb:.1f} MB")
    
    # Results
    print("\n" + "=" * 40)
    print("📊 TEST RESULTS")
    print("=" * 40)
    
    if assets_ok and exe_ok:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Your build is ready for distribution!")
        print(f"📁 Distribution folder: SupermaulTD_Distribution/")
        print(f"📦 Size: {size_mb:.1f} MB")
        return True
    else:
        print("❌ SOME TESTS FAILED!")
        if not assets_ok:
            print("   - Asset files missing")
        if not exe_ok:
            print("   - Executable test failed")
        print("   Check the build process and try again.")
        return False

if __name__ == '__main__':
    success = main()
    if not success:
        sys.exit(1)
