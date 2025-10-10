#!/usr/bin/env python3
"""
Version management utility for SupermaulTD
Usage:
    python version_manager.py patch    # 0.3.2 -> 0.3.3
    python version_manager.py minor    # 0.3.2 -> 0.4.0
    python version_manager.py major    # 0.3.2 -> 1.0.0
    python version_manager.py suffix beta  # 0.3.2-experimental -> 0.3.2-beta
    python version_manager.py show     # Show current version
"""

import sys
import subprocess
from version import (
    get_version, get_version_info, 
    increment_patch, increment_minor, increment_major, 
    set_suffix, update_version_file
)

def show_version():
    """Display current version information."""
    info = get_version_info()
    print(f"SupermaulTD Version: {info['version']}")
    print(f"Build Date: {info['build_date']}")
    print(f"Components: {info['major']}.{info['minor']}.{info['patch']}-{info['suffix']}")

def update_version(version_type, suffix=None):
    """Update version based on type."""
    if version_type == 'patch':
        new_version = increment_patch()
        print(f"✅ Incremented patch version: {new_version}")
    elif version_type == 'minor':
        new_version = increment_minor()
        print(f"✅ Incremented minor version: {new_version}")
    elif version_type == 'major':
        new_version = increment_major()
        print(f"✅ Incremented major version: {new_version}")
    elif version_type == 'suffix' and suffix:
        new_version = set_suffix(suffix)
        print(f"✅ Updated suffix: {new_version}")
    else:
        print(f"❌ Invalid version type: {version_type}")
        return False
    
    # Update the version file
    update_version_file()
    print(f"📝 Updated version.py")
    
    return True

def create_git_tag():
    """Create a git tag for the current version."""
    version = get_version()
    tag_name = f"v{version}"
    
    try:
        # Check if tag already exists
        result = subprocess.run(['git', 'tag', '-l', tag_name], 
                              capture_output=True, text=True, check=True)
        if tag_name in result.stdout:
            print(f"⚠️  Tag {tag_name} already exists")
            return False
        
        # Create and push tag
        subprocess.run(['git', 'add', 'version.py'], check=True)
        subprocess.run(['git', 'commit', '-m', f'Bump version to {version}'], check=True)
        subprocess.run(['git', 'tag', '-a', tag_name, '-m', f'Release {version}'], check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        subprocess.run(['git', 'push', 'origin', tag_name], check=True)
        
        print(f"✅ Created and pushed tag: {tag_name}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git error: {e}")
        return False

def main():
    """Main version management function."""
    if len(sys.argv) < 2:
        print("Usage: python version_manager.py <command> [options]")
        print("Commands:")
        print("  show                    - Show current version")
        print("  patch                   - Increment patch version (0.3.2 -> 0.3.3)")
        print("  minor                   - Increment minor version (0.3.2 -> 0.4.0)")
        print("  major                   - Increment major version (0.3.2 -> 1.0.0)")
        print("  suffix <name>           - Set version suffix (e.g., 'beta', 'stable')")
        print("  release patch           - Update version and create git tag")
        print("  release minor           - Update version and create git tag")
        print("  release major           - Update version and create git tag")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'show':
        show_version()
    
    elif command in ['patch', 'minor', 'major']:
        if update_version(command):
            print(f"\n🎯 Next steps:")
            print(f"  1. Test your changes")
            print(f"  2. Run: python version_manager.py release {command}")
            print(f"  3. Or manually: git add . && git commit -m 'Bump version' && git push")
    
    elif command == 'suffix':
        if len(sys.argv) < 3:
            print("❌ Please specify a suffix name")
            print("Usage: python version_manager.py suffix <name>")
            return
        
        suffix = sys.argv[2]
        if update_version('suffix', suffix):
            print(f"\n🎯 Next steps:")
            print(f"  1. Test your changes")
            print(f"  2. Run: python version_manager.py release patch")
    
    elif command == 'release':
        if len(sys.argv) < 3:
            print("❌ Please specify version type")
            print("Usage: python version_manager.py release <patch|minor|major>")
            return
        
        version_type = sys.argv[2]
        if update_version(version_type):
            if create_git_tag():
                print(f"\n🚀 Release process complete!")
                print(f"   GitHub Actions will now build and create a release")
            else:
                print(f"\n⚠️  Version updated but git tag creation failed")
                print(f"   You can manually create the tag and push")
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python version_manager.py' for usage information")

if __name__ == '__main__':
    main()
