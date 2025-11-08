[app]
title = AnanSketchbook
package.name = anan_sketchbook
package.domain = org.example
source.dir = .
source.include_exts = py,png,ttf,kv,md
version = 1.0.0
requirements = python3,kivy,pillow,plyer
orientation = portrait

# 包含资源
include_patterns = BaseImages/*, font.ttf

# 最低与目标 API（按需调整）
android.api = 33
android.minapi = 21

# 权限可按需添加
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,READ_MEDIA_IMAGES

# Use mirror for python-for-android to avoid GitHub connectivity issues
p4a.url = https://gitclone.com/github.com/kivy/python-for-android.git
p4a.branch = develop
p4a.local_recipes = /home/qmqaq/Anan-s-Sketchbook-Chat-Box-main/android_kivy/local_recipes

[buildozer]
log_level = 2
warn_on_root = 1
