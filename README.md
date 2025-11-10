# 安安的素描本聊天框

将输入框中的文字或图片“贴”到安安的素描本上，支持自动换底图、括号着色、高度自适应排版、以及（Windows 端）自动截获快捷键、剪贴板图片贴入等功能。现已补充移动端与离线 APK 打包方案。

## AI 声明

本项目 90% 代码由 AI 协助生成与重构，人工主要负责需求描述与测试调优。

## 目录结构速览

```
api.py                # FastAPI 后端（可被移动端或其他客户端调用）
main.py               # Windows 热键版本（依赖 keyboard/pywin32）
android_main.py       # Kivy 安卓入口（离线本地生成，不依赖后端）
image_fit_paste.py    # 图片自适应粘贴算法
text_fit_draw.py      # 文本自适应排版 + 括号着色逻辑
config.py             # 配置：底图、坐标、字体、热键等
BaseImages/           # 底图与遮挡图层
mobile/               # 简易 React Native 示例（走后端接口）
buildozer.spec        # 安卓打包配置（Kivy/Buildozer）
font.ttf              # 字体文件（请确认版权许可后再分发）
```

## 功能要点

- 文本模式：自动计算最大可用字体大小，支持括号 [ ] / 【 】 内文字着色。
- 图片模式：剪贴板图像（Windows）或用户选择图片（安卓）按 contain 规则缩放粘贴。
- 底图切换：在文本中出现映射关键词（如 `#开心#`）自动更换底图并移除关键词。
- 置顶遮挡：`BASE_OVERLAY_FILE` 可用于模拟前景遮挡效果。
- 安卓离线：无需网络，直接在设备上生成 PNG 可保存或分享。

## Windows 部署与使用（main.py）

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 运行：
   ```bash
   python main.py
   ```
3. 在允许的进程（例如 QQ、微信）焦点窗口中按下配置的热键（默认 Enter）→ 自动截获文本/图片 → 生成并复制图片 → 自动粘贴与发送（取决于配置）。

关键配置位于 `config.py`：

- `HOTKEY` / `BLOCK_HOTKEY`：生成触发与是否阻塞原按键。
- `BASEIMAGE_MAPPING`：关键词到底图文件映射，可自行扩展。
- `TEXT_BOX_TOPLEFT` / `IMAGE_BOX_BOTTOMRIGHT`：文本/图片绘制区域。
- `FONT_FILE`：字体文件路径（确保包含中文与符号）。

出现生成延迟或剪贴板异常时，可增大 `DELAY`。

## FastAPI 后端（api.py）

适用于移动端前后端分离或局域网访问：

1. 安装依赖：同上。
2. 启动：
   ```bash
   python api.py
   ```
3. 测试：访问 `http://127.0.0.1:8000/` 或调用接口：
   - `GET /bases` 列出可用底图。
   - `POST /generate` 根据文本或图片生成 PNG（返回 base64）。

示例请求：
```json
{
  "text": "你好【安安】#开心#",
  "image_base64": null,
  "base_key": null,
  "use_overlay": true
}
```

移动端（React Native/Expo）调用示例见 `mobile/App.js`。

## 安卓离线 APK（Kivy + Buildozer）

`android_main.py` 提供一个最小 Kivy UI：

- 文本输入框与“生成”按钮。
- 关键词按钮快速插入 `#开心#` 等。
- 可选择自定义图片作为内容贴入。
- 保存生成结果为 PNG。

### 1. 开发机（Linux 推荐）准备

```bash
pip install buildozer
sudo apt-get install -y git python3-pip openjdk-17-jdk unzip
buildozer init            # 若已存在 buildozer.spec 可跳过
```

本仓库已附带 `buildozer.spec`，其中 `requirements` 仅包含 `python3,kivy,pillow`，避免引入 Windows 专属库。

### 2. 本地调试

```bash
python android_main.py   # 使用桌面窗口验证 UI 与生成逻辑
```

### 3. 打包 APK

```bash
buildozer -v android debug
```

生成的 APK 位于 `bin/` 目录，可直接安装到手机（需允许未知来源应用）。第一次构建会下载 NDK/SDK，耗时较长。

### 4. 常见问题

- 字体不显示中文：确认 `font.ttf` 覆盖并在安卓端可被加载；若失败可替换为 NotoSansCJK。 
- 图片路径分隔符：原配置使用反斜杠，代码中已自动标准化为跨平台路径。 
- 构建失败（Cython 版本）：当前不依赖 Cython；如后续增加扩展，请在 `buildozer.spec` 中 pin 版本。 

## React Native 示例（mobile/）

`mobile/App.js` 展示如何通过后端接口生成图片。若需纯离线（无后端），可将 `text_fit_draw.py` 与 `image_fit_paste.py` 逻辑迁移到 JS（Canvas 或 Skia），目前未内置。

## 括号着色规则

在文本中：
- `[]` 或 `【】` 以及其中内容全部使用紫色（可在 `draw_text_auto` 中调整）。
- 支持跨行延续：若一行开启括号但未关闭，下一行继续使用着色。

## 扩展与后续规划

- Accessibility / 自动发送（安卓）：当前示例未集成，可后续通过 `pyjnius` + 自定义 Service 实现。
- 纯前端实现：以 RN Skia 或 Web Canvas 重写绘制算法，免除 Python 运行时。 
- GitHub Actions 远程自动打包：可新增工作流使用 Docker 化 Buildozer 镜像输出 APK Artifact。

## 版权与素材声明

请确保底图与字体素材在你的分发范围内具备合法授权。本仓库不对第三方字体与图片的版权负责。

## 许可证

（可根据需要补充：MIT / Apache-2.0 / 仅自用 等）

欢迎提交 Issue 与 PR 改进跨平台兼容与移动端体验。
