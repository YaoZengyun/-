# 离线单 APK 方案（Kivy）

本目录提供一个基于 Kivy + Pillow 的离线实现，将原项目的图片与文字绘制逻辑直接在 Android 设备端运行，不再需要 FastAPI 后端，也不依赖 Windows 特有的键盘/剪贴板功能。

## 目录简介

- `config_mobile.py` 离线版配置（与原 `config.py` 对应，路径改为 POSIX）
- `main.py` Kivy 应用入口，生成图片并预览、保存
- `buildozer.spec` 打包配置（使用 Buildozer 生成 APK）

## 准备资源

请将仓库根目录的以下文件复制到本目录：

```
BaseImages/            # 整个文件夹
font.ttf               # 字体文件
```

复制后结构示例：

```
android_kivy/
  BaseImages/
    base.png
    base_overlay.png
    开心.png
    生气.png
    ...
  font.ttf
  main.py
  config_mobile.py
  buildozer.spec
```

## 功能说明

1. 输入文本，自动在指定区域自适应字号绘制；【】或 [] 内文字会变成紫色（同原项目）。
2. 支持关键词（#开心# 等）切换底图。
3. 点击“生成图片”即可预览；“保存 PNG”保存到应用的 `user_data_dir` 下（可通过 ADB 或文件浏览器访问）。
4. 逻辑复用原库 `text_fit_draw.py`，保持效果一致。

## 打包步骤（Ubuntu / WSL 推荐）

```bash
# 1. 系统依赖（示例，因发行版而异）
sudo apt update
sudo apt install -y python3-pip git openjdk-17-jdk pkg-config \
    libSDL2-dev libffi-dev libblas-dev liblapack-dev libjpeg-dev libz-dev

# 2. 安装 buildozer 与 cython
pip install --upgrade buildozer cython

# 3. 进入目录（确保资源已复制）
cd android_kivy

# 4. 构建调试 APK（第一次会自动下载 Android SDK/NDK，耗时较长）
buildozer android debug

# 5. 生成 APK 路径：bin/AnanSketchbook-1.0.0-debug.apk
#   用手机 USB 连接后：
adb install -r bin/AnanSketchbook-1.0.0-debug.apk
```

### 常见问题

| 问题 | 解决 |
|------|------|
| 缺少依赖或编译失败 | 检查是否安装所有系统库与 JDK，重试 `buildozer android debug` |
| Pillow 编译失败 | 安装额外的 `libtiff5-dev libfreetype6-dev liblcms2-dev` 等依赖 |
| APK 安装后闪退 | 使用 `adb logcat` 查看崩溃日志，多为资源未复制或路径错误 |
| 需要发布 Release | 使用 `buildozer android release` 并按文档签名 |

## 后续扩展建议

- 添加图片贴入功能：使用 `image_fit_paste.paste_image_auto`，增加图片选择（可集成 plyer 或自定义文件选择器）。
- 保存到系统图库：请求写入权限并复制到公有目录。
- 增加差分底图管理界面（动态扫描 BaseImages）。
- UI 美化：使用 KivyMD。

## 其他离线替代方案简述

| 方案 | 优点 | 缺点 |
|------|------|------|
| Kivy (当前) | 纯 Python 复用现有代码快 | UI 原生程度较弱，APK 体积略大 |
| Chaquopy | 可嵌入原生 Android，仍用 Python | 需 Java/Kotlin 项目与 Gradle 配置，集成复杂 |
| BeeWare | Python 到原生工具链 | 成熟度较低，生态小 |
| 全 JS (React Native Skia) | 只需 JS/TS，安装轻量 | 需重写算法，字体测量控制复杂 |

如需我继续提供 Chaquopy 集成示例或 React Native Skia 重写版本，请提出具体需求。

---
本目录即离线单 APK 方案的起点，确认能满足你的需求后可继续深度优化。 
