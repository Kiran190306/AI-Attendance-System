# AI Attendance App - Android Build Instructions

## Project Overview
This folder contains a lightweight Android WebView app that loads:
`https://ai-attendance-system-vi47.onrender.com`

The app includes:
- `MainActivity` with a `WebView`
- JavaScript enabled in `WebView`
- page loading indicator
- back-button support
- simple splash screen

## Build Instructions

### Option 1: Android Studio
1. Open Android Studio.
2. Select **Open** and choose the `android_app` folder.
3. Allow Android Studio to sync Gradle and resolve dependencies.
4. Connect an Android device or start an emulator.
5. Select **Build > Build Bundle(s) / APK(s) > Build APK(s)**.
6. After the build completes, click **Locate** to find the generated APK.

### Option 2: Command Line (with Gradle)
1. Open a terminal in the `android_app` folder.
2. Run:
   - `gradle assembleDebug`  
   or if you have a Gradle wrapper installed:
   - `./gradlew assembleDebug`
3. Locate the APK in:
   - `app/build/outputs/apk/debug/app-debug.apk`

## Notes
- If the Android SDK path is not configured, set `sdk.dir` in `local.properties`.
- The app uses package name `com.example.aiattendance`.
- Change the URL in `MainActivity.java` if you want to load a different endpoint.

## Customization
- To update the splash screen text or style, edit `activity_splash.xml` and `splash_background.xml`.
- To change the app name, update `app/src/main/res/values/strings.xml`.
