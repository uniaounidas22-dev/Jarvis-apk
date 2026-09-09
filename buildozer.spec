[app]
title = Jarvis
package.name = jarvis
package.domain = org.jarvis.app
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 0.1
requirements = python3,kivy
orientation = portrait
fullscreen = 0

android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
