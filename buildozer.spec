[app]

# (str) Title of your application
title = FoodAI Dataset Builder

# (str) Package name
package.name = foodai_dataset_builder

# (str) Package domain (needed for android/ios packaging)
package.domain = org.foodai

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,jpeg,json,kv,txt,md

# (list) List of inclusions using pattern matching
source.include_patterns = assets/*,FoodAI_Dataset/*

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
# Use the PyPI release of KivyMD to avoid GitHub fetch failures during CI builds.
# Downgraded Pillow from 10.4.0 to 9.5.0 to fix patch compatibility issues with python-for-android
requirements = python3,kivy==2.3.1,kivymd==2.0.1.dev0,Pillow==9.5.0

# (str) Supported orientation (one of landscape, sensor, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash of the application
presplash.filename = %(source.dir)s/assets/icons/icon.png

# (string) Icon of the application
icon.filename = %(source.dir)s/assets/icons/icon.png

# (list) Permissions
android.permissions = CAMERA, INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# (int) Target Android API, should be as high as possible.
android.api = 31

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (str) Android SDK version to use
android.sdk = 33

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (bool) If True, then skip trying to update the Android sdk
android.skip_update = False

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a

# (bool) If True, then automatically accept SDK license
android.accept_sdk_license = True

# (str) Boot image for Android
android.bootclasspath =

# (str) The Android entry point, default is ok for Kivy-based app
# android.entrypoint = org.kivy.android.PythonActivity

[buildozer]
log_level = 2
