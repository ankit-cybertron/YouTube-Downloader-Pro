# Android APK Build Instructions
# Generated: 2026-01-24T12:27:48.978936

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
cd /Users/cybertron/MyProjects/yt-downloader-pro

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
- Debug: `/Users/cybertron/MyProjects/yt-downloader-pro/build/android/apk/debug/`
- Release: `/Users/cybertron/MyProjects/yt-downloader-pro/dist/`

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

