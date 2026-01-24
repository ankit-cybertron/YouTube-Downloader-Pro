#!/usr/bin/env python3
"""
Android APK Build Script for YouTube Downloader Pro

This script helps build an Android APK from the PySide6 mobile application.
It handles all the necessary setup and configuration.

Requirements:
- Python 3.10+
- PySide6 (pip install PySide6)
- Java JDK 17+ (JAVA_HOME must be set)
- Android SDK (ANDROID_SDK_ROOT must be set)
- Android NDK (will be auto-downloaded if not present)

Usage:
    python scripts/build_android.py [--debug] [--release] [--check-only]

Author: Cybertron
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path
from datetime import datetime


# ============================================================================
# CONFIGURATION
# ============================================================================

APP_NAME = "YT Downloader Pro"
PACKAGE_NAME = "com.cybertron.ytdownloaderpro"
VERSION = "1.0.0"
VERSION_CODE = 1

# Minimum Android API level (Android 8.0 Oreo)
MIN_SDK_VERSION = 26
# Target Android API level (Android 14)
TARGET_SDK_VERSION = 34

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
SRC_DIR = PROJECT_ROOT / "src"
MOBILE_DIR = SRC_DIR / "mobile"
ANDROID_DIR = PROJECT_ROOT / "android"
ASSETS_DIR = PROJECT_ROOT / "assets"
BUILD_DIR = PROJECT_ROOT / "build" / "android"
DIST_DIR = PROJECT_ROOT / "dist"

# Entry point for mobile app
MAIN_MODULE = "src.mobile.main"
MAIN_SCRIPT = MOBILE_DIR / "main.py"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_step(step_num, text):
    """Print a step indicator."""
    print(f"\n[{step_num}] {text}")


def print_success(text):
    """Print success message."""
    print(f"   ✓ {text}")


def print_error(text):
    """Print error message."""
    print(f"   ✗ {text}")


def print_warning(text):
    """Print warning message."""
    print(f"   ⚠ {text}")


def run_command(cmd, cwd=None, check=True):
    """Run a shell command and return the result."""
    print(f"   Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True,
            shell=isinstance(cmd, str)
        )
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {e.stderr}")
        raise


def check_command_exists(cmd):
    """Check if a command exists in PATH."""
    return shutil.which(cmd) is not None


# ============================================================================
# ENVIRONMENT CHECKS
# ============================================================================

def check_python():
    """Check Python version."""
    print_step(1, "Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python 3.10+ required, found {version.major}.{version.minor}")
        return False


def check_java():
    """Check Java JDK installation."""
    print_step(2, "Checking Java JDK...")
    
    java_home = os.environ.get("JAVA_HOME")
    if not java_home:
        print_error("JAVA_HOME environment variable not set")
        print("   Please install JDK 17+ and set JAVA_HOME")
        print("   macOS: brew install openjdk@17")
        print("   Then: export JAVA_HOME=/opt/homebrew/opt/openjdk@17")
        return False
    
    if not Path(java_home).exists():
        print_error(f"JAVA_HOME path does not exist: {java_home}")
        return False
    
    # Check Java version
    try:
        result = run_command(["java", "-version"], check=False)
        version_output = result.stderr or result.stdout
        print_success(f"JAVA_HOME: {java_home}")
        return True
    except Exception as e:
        print_error(f"Failed to run java: {e}")
        return False


def check_android_sdk():
    """Check Android SDK installation."""
    print_step(3, "Checking Android SDK...")
    
    android_sdk = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
    if not android_sdk:
        print_error("ANDROID_SDK_ROOT environment variable not set")
        print("   Please install Android SDK and set ANDROID_SDK_ROOT")
        print("   Download: https://developer.android.com/studio#command-tools")
        print("   Then: export ANDROID_SDK_ROOT=/path/to/android/sdk")
        return False
    
    sdk_path = Path(android_sdk)
    if not sdk_path.exists():
        print_error(f"Android SDK path does not exist: {android_sdk}")
        return False
    
    # Check for essential SDK components
    build_tools = sdk_path / "build-tools"
    platforms = sdk_path / "platforms"
    
    if not build_tools.exists() or not list(build_tools.glob("*")):
        print_warning("Android build-tools not found")
        print("   Run: sdkmanager 'build-tools;34.0.0'")
    
    if not platforms.exists() or not list(platforms.glob("*")):
        print_warning("Android platforms not found")
        print("   Run: sdkmanager 'platforms;android-34'")
    
    print_success(f"ANDROID_SDK_ROOT: {android_sdk}")
    return True


def check_pyside6():
    """Check PySide6 installation."""
    print_step(4, "Checking PySide6...")
    
    try:
        import PySide6
        from PySide6 import __version__ as pyside_version
        print_success(f"PySide6 {pyside_version}")
        
        # Check if pyside6-deploy is available
        if check_command_exists("pyside6-deploy"):
            print_success("pyside6-deploy found")
            return True
        else:
            print_error("pyside6-deploy not found in PATH")
            print("   Make sure PySide6 is installed: pip install PySide6")
            return False
            
    except ImportError:
        print_error("PySide6 not installed")
        print("   Install with: pip install PySide6")
        return False


def check_project_structure():
    """Check project structure is correct."""
    print_step(5, "Checking project structure...")
    
    required_files = [
        MAIN_SCRIPT,
        SRC_DIR / "core" / "worker.py",
        SRC_DIR / "core" / "utils.py",
        MOBILE_DIR / "ui" / "mobile_window.py",
    ]
    
    missing = []
    for f in required_files:
        if f.exists():
            print_success(f"Found: {f.relative_to(PROJECT_ROOT)}")
        else:
            print_error(f"Missing: {f.relative_to(PROJECT_ROOT)}")
            missing.append(f)
    
    return len(missing) == 0


def check_all():
    """Run all environment checks."""
    print_header("Environment Checks")
    
    checks = [
        check_python(),
        check_java(),
        check_android_sdk(),
        check_pyside6(),
        check_project_structure(),
    ]
    
    if all(checks):
        print("\n" + "=" * 60)
        print("   All checks passed! Ready to build.")
        print("=" * 60)
        return True
    else:
        print("\n" + "=" * 60)
        print("   Some checks failed. Please fix the issues above.")
        print("=" * 60)
        return False


# ============================================================================
# BUILD FUNCTIONS
# ============================================================================

def create_pysidedeploy_spec():
    """Create or update pysidedeploy.spec file."""
    print_step(1, "Creating pysidedeploy.spec...")
    
    spec_content = f"""# This file is generated by build_android.py
# Manual edits may be overwritten

[app]
title = {APP_NAME}
project_dir = {PROJECT_ROOT}
input_file = {MAIN_SCRIPT}
exec_directory = .
icon = {ASSETS_DIR / 'icon.png'}

[python]
python_path = {sys.executable}
packages = nuitka==2.3.2

[qt]
qml_files = 

[android]
wheel_pyside = 
wheel_shiboken = 
plugins = 
permissions = android.permission.INTERNET,android.permission.WRITE_EXTERNAL_STORAGE,android.permission.READ_EXTERNAL_STORAGE

[nuitka]
extra_args = --enable-plugin=pyside6

[buildozer]
mode = release
recipe_dir = 
jars_dir = 
ndk_path = 
sdk_path = {os.environ.get('ANDROID_SDK_ROOT', '')}
local_libs = 
arch = arm64-v8a

"""
    
    spec_path = PROJECT_ROOT / "pysidedeploy.spec"
    spec_path.write_text(spec_content)
    print_success(f"Created: {spec_path}")
    return spec_path


def create_android_manifest():
    """Create AndroidManifest.xml with necessary permissions."""
    print_step(2, "Creating Android configuration...")
    
    ANDROID_DIR.mkdir(parents=True, exist_ok=True)
    
    manifest_content = f"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{PACKAGE_NAME}"
    android:versionCode="{VERSION_CODE}"
    android:versionName="{VERSION}">
    
    <!-- Permissions required for the app -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" 
        android:maxSdkVersion="29" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE"
        android:maxSdkVersion="32" />
    <uses-permission android:name="android.permission.MANAGE_EXTERNAL_STORAGE" />
    
    <!-- SDK version requirements -->
    <uses-sdk 
        android:minSdkVersion="{MIN_SDK_VERSION}"
        android:targetSdkVersion="{TARGET_SDK_VERSION}" />
    
    <application
        android:label="{APP_NAME}"
        android:icon="@mipmap/ic_launcher"
        android:allowBackup="true"
        android:theme="@android:style/Theme.NoTitleBar"
        android:hardwareAccelerated="true"
        android:requestLegacyExternalStorage="true">
        
        <activity
            android:name="org.qtproject.qt.android.bindings.QtActivity"
            android:configChanges="orientation|uiMode|screenLayout|screenSize|smallestScreenSize|locale|fontScale|keyboard|keyboardHidden|navigation"
            android:label="{APP_NAME}"
            android:screenOrientation="portrait"
            android:exported="true">
            
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
            
            <!-- Handle YouTube URLs -->
            <intent-filter>
                <action android:name="android.intent.action.SEND" />
                <category android:name="android.intent.category.DEFAULT" />
                <data android:mimeType="text/plain" />
            </intent-filter>
        </activity>
        
        <!-- File provider for saving downloads -->
        <provider
            android:name="androidx.core.content.FileProvider"
            android:authorities="{PACKAGE_NAME}.fileprovider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/file_paths" />
        </provider>
    </application>
</manifest>
"""
    
    manifest_path = ANDROID_DIR / "AndroidManifest.xml"
    manifest_path.write_text(manifest_content)
    print_success(f"Created: {manifest_path}")
    
    # Create file_paths.xml for FileProvider
    xml_dir = ANDROID_DIR / "res" / "xml"
    xml_dir.mkdir(parents=True, exist_ok=True)
    
    file_paths_content = """<?xml version="1.0" encoding="utf-8"?>
<paths>
    <external-path name="downloads" path="Download/" />
    <external-files-path name="external_files" path="." />
    <cache-path name="cache" path="." />
</paths>
"""
    
    (xml_dir / "file_paths.xml").write_text(file_paths_content)
    print_success(f"Created: {xml_dir / 'file_paths.xml'}")


def create_build_instructions():
    """Create detailed build instructions file."""
    print_step(3, "Creating build instructions...")
    
    instructions = f"""# Android APK Build Instructions
# Generated: {datetime.now().isoformat()}

## Prerequisites

1. **Java JDK 17+**
   ```bash
   # macOS
   brew install openjdk@17
   export JAVA_HOME=/opt/homebrew/opt/openjdk@17
   
   # Add to ~/.zshrc or ~/.bashrc for persistence
   echo 'export JAVA_HOME=/opt/homebrew/opt/openjdk@17' >> ~/.zshrc
   ```

2. **Android SDK Command Line Tools**
   - Download from: https://developer.android.com/studio#command-tools
   - Extract to ~/Android/cmdline-tools/latest/
   ```bash
   export ANDROID_SDK_ROOT=$HOME/Android
   export PATH=$PATH:$ANDROID_SDK_ROOT/cmdline-tools/latest/bin
   
   # Install required SDK packages
   sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"
   sdkmanager "ndk;25.2.9519653"
   ```

3. **Python Dependencies**
   ```bash
   pip install PySide6 yt-dlp
   ```

## Build Steps

### Option 1: Using pyside6-deploy (Recommended)

```bash
cd {PROJECT_ROOT}

# Run the build
pyside6-deploy --config pysidedeploy.spec

# The APK will be generated in the build folder
```

### Option 2: Using Buildozer (Alternative)

If pyside6-deploy doesn't work, try buildozer:

```bash
pip install buildozer cython

# Initialize buildozer
buildozer init

# Build APK
buildozer android debug  # For debug build
buildozer android release  # For release build
```

### Option 3: Manual Build with Qt for Android

1. Install Qt for Android via Qt Online Installer
2. Configure Qt Creator for Android development
3. Open the project and build

## Troubleshooting

### "JAVA_HOME not set"
```bash
export JAVA_HOME=$(/usr/libexec/java_home)  # macOS
```

### "Android SDK not found"
```bash
export ANDROID_SDK_ROOT=$HOME/Android
```

### "NDK not found"
```bash
sdkmanager "ndk;25.2.9519653"
export ANDROID_NDK_ROOT=$ANDROID_SDK_ROOT/ndk/25.2.9519653
```

### Build fails with memory error
```bash
export JAVA_OPTS="-Xmx4g"
```

## Output

After successful build, find your APK at:
- Debug: `{BUILD_DIR}/apk/debug/`
- Release: `{DIST_DIR}/`

## Installing on Device

```bash
# Enable USB debugging on your Android device
# Then run:
adb install -r path/to/your-app.apk
```

## Notes

- The first build may take 10-30 minutes as it downloads dependencies
- Release builds require signing - see Android documentation
- For Google Play, you'll need to sign with a production keystore

"""
    
    instructions_path = PROJECT_ROOT / "ANDROID_BUILD.md"
    instructions_path.write_text(instructions)
    print_success(f"Created: {instructions_path}")
    return instructions_path


def build_apk(debug=True):
    """Attempt to build the APK."""
    print_header("Building APK")
    
    # Create necessary files
    spec_path = create_pysidedeploy_spec()
    create_android_manifest()
    create_build_instructions()
    
    # Create build directory
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    
    print_step(4, "Running pyside6-deploy...")
    print("\n" + "-" * 60)
    print("NOTE: The actual APK build requires Android SDK/NDK setup.")
    print("If this fails, follow the instructions in ANDROID_BUILD.md")
    print("-" * 60 + "\n")
    
    try:
        # Try to run pyside6-deploy
        mode = "debug" if debug else "release"
        cmd = [
            "pyside6-deploy",
            "--config", str(spec_path),
            # "-c" if not debug else ""  # Add -c for release/compressed
        ]
        
        result = run_command(cmd, cwd=PROJECT_ROOT, check=False)
        
        if result.returncode == 0:
            print_success("APK build completed!")
            print(f"\n   Output directory: {BUILD_DIR}")
        else:
            print_warning("pyside6-deploy returned non-zero exit code")
            print("   Check the output above for errors")
            print("   You may need to build manually - see ANDROID_BUILD.md")
            
    except Exception as e:
        print_error(f"Build failed: {e}")
        print("\nTo build manually, follow the instructions in ANDROID_BUILD.md")
        return False
    
    return True


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Build Android APK for YouTube Downloader Pro"
    )
    parser.add_argument(
        "--check-only", 
        action="store_true",
        help="Only run environment checks, don't build"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=True,
        help="Build debug APK (default)"
    )
    parser.add_argument(
        "--release",
        action="store_true",
        help="Build release APK"
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("  YouTube Downloader Pro - Android APK Builder")
    print(f"  Version {VERSION}")
    print("=" * 60)
    
    # Run checks
    if not check_all():
        sys.exit(1)
    
    if args.check_only:
        sys.exit(0)
    
    # Build
    debug = not args.release
    if build_apk(debug=debug):
        print("\n" + "=" * 60)
        print("  Build process completed!")
        print("  Check ANDROID_BUILD.md for manual build instructions")
        print("=" * 60 + "\n")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
