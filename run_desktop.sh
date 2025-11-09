#!/usr/bin/env bash
# 一键在桌面环境运行 Kivy 版本（Linux）
# 依赖：python3, pip
# 可选：已创建 venv 并安装 desktop-requirements.txt

set -euo pipefail

# 进入仓库根
cd "$(dirname "$0")"

# 若存在 venv，则激活；否则忽略
if [ -f "venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi

# Kivy 在部分环境需要此后端
export KIVY_GL_BACKEND=sdl2

# 确保资源位于 android_kivy 目录
if [ ! -d android_kivy/BaseImages ]; then
  echo "[INFO] 复制 BaseImages 到 android_kivy/"
  cp -r BaseImages android_kivy/
fi
if [ ! -f android_kivy/font.ttf ] && [ -f font.ttf ]; then
  echo "[INFO] 复制 font.ttf 到 android_kivy/"
  cp font.ttf android_kivy/
fi

python android_kivy/main.py
