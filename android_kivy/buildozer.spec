[app]
title = AnanSketchbook
package.name = anan_sketchbook
package.domain = org.example
source.dir = .
source.include_exts = py,png,ttf,kv,md
version = 1.0.0
requirements = python3,kivy,pillow,plyer,cython,setuptools,six
orientation = portrait

# 包含资源
include_patterns = BaseImages/*, font.ttf

# 最低与目标 API（按需调整）
android.api = 33
android.minapi = 21

# 权限可按需添加
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,READ_MEDIA_IMAGES

# Use official defaults for python-for-android (online build on GitHub Actions)
# p4a.url = https://gitclone.com/github.com/kivy/python-for-android.git
# p4a.branch = develop
# p4a.local_recipes = local_recipes

[buildozer]
log_level = 2
warn_on_root = 0
exit_on_error = 1
