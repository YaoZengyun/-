[app]
title = AnanSketchbook
package.name = anan_sketchbook
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,jpeg,ttf,kv,md,xml,atlas
version = 1.0.0
requirements = python3,kivy,pillow,plyer,pyjnius,android
orientation = portrait

# 包含资源
include_patterns = BaseImages/*, font.ttf

# 最低与目标 API（按需调整）
android.api = 33
android.minapi = 21
android.archs = arm64-v8a

# 权限可按需添加
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,READ_MEDIA_IMAGES

# 使用 gitclone 镜像以避免直接访问 github 失败
p4a.url = https://gitclone.com/github.com/kivy/python-for-android.git
p4a.branch = develop
# 如需本地自定义配方，可启用：
# p4a.local_recipes = local_recipes

[buildozer]
log_level = 2
warn_on_root = 0
exit_on_error = 1

# Include native Android sources/resources and manifest additions
android.add_src = java
android.add_res = res
android.add_manifest_xml = manifest_additions.xml
 