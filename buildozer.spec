[app]

# (str) Title of your application
title = Neon Snake

# (str) Package name
package.name = neonsnake

# (str) Package domain (needed for android packaging)
package.domain = org.vaibhavmishra

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,jpeg,wav,ico,json

# (str) Application versioning
version = 1.0.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,pygame-ce

# (str) Supported orientations (one of landscape, sensorLandscape, portrait or all)
orientation = landscape

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

# (list) Permissions
android.permissions = INTERNET,VIBRATE

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (str) Android NDK directory (if empty, it will be automatically downloaded)
#android.ndk_path =

# (str) Android SDK directory (if empty, it will be automatically downloaded)
#android.sdk_path =

# (str) ANT directory (if empty, it will be automatically downloaded)
#android.ant_path =

# (list) List of service to declare
#services =

# (str) Presplash of the application
#android.presplash_color = #050508

# (str) Icon of the application
icon.filename = assets/images/logo.png

# (list) Supported architectures
android.archs = arm64-v8a, armeabi-v7a

# (bool) Allow backup
android.allow_backup = 1

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
