"""
Version management for SupermaulTD
"""
import os
import re
from datetime import datetime

# Current version - update this when releasing
VERSION = "0.3.2-experimental"
BUILD_DATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Version components
VERSION_MAJOR = 0
VERSION_MINOR = 3
VERSION_PATCH = 2
VERSION_SUFFIX = "experimental"

def get_version():
    """Get the current version string"""
    return VERSION

def get_version_info():
    """Get detailed version information"""
    return {
        "version": VERSION,
        "major": VERSION_MAJOR,
        "minor": VERSION_MINOR,
        "patch": VERSION_PATCH,
        "suffix": VERSION_SUFFIX,
        "build_date": BUILD_DATE,
        "build_timestamp": datetime.now().isoformat()
    }

def increment_patch():
    """Increment patch version (0.3.2 -> 0.3.3)"""
    global VERSION, VERSION_PATCH
    VERSION_PATCH += 1
    VERSION = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}-{VERSION_SUFFIX}"
    return VERSION

def increment_minor():
    """Increment minor version (0.3.2 -> 0.4.0)"""
    global VERSION, VERSION_MINOR, VERSION_PATCH
    VERSION_MINOR += 1
    VERSION_PATCH = 0
    VERSION = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}-{VERSION_SUFFIX}"
    return VERSION

def increment_major():
    """Increment major version (0.3.2 -> 1.0.0)"""
    global VERSION, VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH
    VERSION_MAJOR += 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0
    VERSION = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}-{VERSION_SUFFIX}"
    return VERSION

def set_suffix(suffix):
    """Set version suffix (e.g., 'experimental', 'beta', 'stable')"""
    global VERSION, VERSION_SUFFIX
    VERSION_SUFFIX = suffix
    VERSION = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}-{VERSION_SUFFIX}"
    return VERSION

def update_version_file():
    """Update this file with the current version"""
    file_path = __file__
    
    # Read current file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Update version line
    content = re.sub(
        r'VERSION = "[^"]*"',
        f'VERSION = "{VERSION}"',
        content
    )
    
    # Update individual components
    content = re.sub(
        r'VERSION_MAJOR = \d+',
        f'VERSION_MAJOR = {VERSION_MAJOR}',
        content
    )
    content = re.sub(
        r'VERSION_MINOR = \d+',
        f'VERSION_MINOR = {VERSION_MINOR}',
        content
    )
    content = re.sub(
        r'VERSION_PATCH = \d+',
        f'VERSION_PATCH = {VERSION_PATCH}',
        content
    )
    content = re.sub(
        r'VERSION_SUFFIX = "[^"]*"',
        f'VERSION_SUFFIX = "{VERSION_SUFFIX}"',
        content
    )
    
    # Write back to file
    with open(file_path, 'w') as f:
        f.write(content)

def create_version_header():
    """Create a version header for C++/other languages if needed"""
    return f"""/*
 * SupermaulTD Version Information
 * Generated on {BUILD_DATE}
 */

#ifndef VERSION_H
#define VERSION_H

#define VERSION_STRING "{VERSION}"
#define VERSION_MAJOR {VERSION_MAJOR}
#define VERSION_MINOR {VERSION_MINOR}
#define VERSION_PATCH {VERSION_PATCH}
#define VERSION_SUFFIX "{VERSION_SUFFIX}"
#define BUILD_DATE "{BUILD_DATE}"

#endif // VERSION_H
"""

if __name__ == "__main__":
    print(f"SupermaulTD Version: {get_version()}")
    print(f"Build Date: {BUILD_DATE}")
    print(f"Version Info: {get_version_info()}")
