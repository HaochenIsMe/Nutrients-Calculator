[app]

# App metadata
title = 营养摄入计算器
package.name = nutrienttracker
package.domain = org.nutrienttracker
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,jsonl

# Entry point (Buildozer always looks for main.py)
# Version
version = 1.0

# Requirements — pure-Python only; no native extensions needed
requirements = python3==3.11.0,kivy==2.3.0,pillow

# Android target
android.minapi = 26
android.api = 33
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True

# Permissions — private data dir only (no external storage needed)
android.permissions = INTERNET

# Orientation
orientation = portrait

# Icons / presplash (optional; Kivy provides defaults)
# icon.filename = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/presplash.png


# Exclude files not needed in the APK
source.exclude_dirs = data,__pycache__,.claude,.buildozer,.git,.github
source.exclude_patterns = *.pyc,*.pyo,*.spec,*.md,*.jsonl

[buildozer]
log_level = 2
warn_on_root = 1
