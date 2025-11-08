# 安安的素描本聊天框

本项目是一个将你在一个文本输入框中的文字或图片写到安安的素描本上的项目

## AI声明

本项目90%的代码由AI生成

## 部署

本项目只支持windows

现在字体文件和安安图片已经内置于项目中, 无需再额外置入DLC.

其中`font.ttf`为字体文件, 可以自由修改成其他字体, 本项目不拥有字体版权, 仅做引用.

底图存储于`BaseImages`目录中, 其中`base.png`为安安拿素描本的照片, `base_overlay.png`为透明底的安安袖子, 用于防止文字和图片覆盖在袖子上方. 如果分辨率不一样的安安图片, 需要修改`config.py`的 `TEXT_BOX_TOPLEFT` 和 `IMAGE_BOX_BOTTOMRIGHT`, 定义文本框的大小.

依赖库安装: `pip install -r requirements.txt `

## 使用

使用文本编辑器打开`config.py`即可看到方便修改的参数, 可以设置热键, 图片路径, 字体路径, 指定的应用, 表情差分关键词等

运行`main.py`即可开始监听回车, 在指定应用中按下回车会自动拦截按键, 生成图片后自动发送 (自动发送功能可以在`config.py`中关闭).

特殊的, 在文本中输入\[\]或者【】, 被包裹的字符会变成紫色.

输入文本框中的图片也可以被直接绘制在素描本上.

输入`#普通#`, `#开心#`, `#生气#`, `#无语#`, `#脸红#`, `#病娇#`可以切换标签差分, 一次切换一直有效. 可以通过修改`BASEIMAGE_MAPPING`来增加更多查分

如果发送失败等可以尝试适当增大`main.py`第10行的`DELAY`

## 其他分支

- [支援MacOS的分支](https://github.com/Sheyiyuan/Anan-s-Sketchbook-Chat-Box/)

## 移动端方案（推荐）：后端 API + 移动前端

本仓库已新增 `api.py`，将文字/图片绘制能力通过 HTTP 接口暴露，便于移动端（如 React Native/Expo、Flutter 或任意 WebView/PWA）调用。

### 启动后端 API（Windows PowerShell）

1. 安装依赖（只需一次）：
	 ```powershell
	 pip install -r requirements.txt
	 ```
2. 启动服务（默认端口 8000）：
	 ```powershell
	 python api.py
	 ```
3. 打开浏览器访问 http://127.0.0.1:8000/ 验证；也可访问 http://127.0.0.1:8000/bases 查看可用底图映射。

### 接口说明

- GET `/bases`：返回默认底图与映射表。
- POST `/generate`：根据文本或图片生成新图，返回 base64 PNG。

请求（JSON）：
```json
{
	"text": "你好【安安】",
	"image_base64": null,
	"base_key": "#开心#",
	"use_overlay": true
}
```

说明：
- `text` 与 `image_base64` 至少提供一个。两者同时提供时优先使用 `image_base64`（图片贴入）。
- 如果不提供 `base_key`，且 `text` 中包含 `BASEIMAGE_MAPPING` 的关键词（如 `#开心#`），会自动切换底图并移除关键词。
- 返回字段 `image_base64` 为 `data:image/png;base64,......` 可直接用于 `<Image>` 或 RN 的 `Image` 组件。

### 移动端前端（建议）

建议使用 Expo（React Native）快速实现：在移动端输入文字或选择图片，调用 `/generate` 获取图片后展示或保存。你可以在任意项目中直接使用如下请求示例：

```js
async function generateFromText(text) {
	const res = await fetch("http://<你的电脑IP>:8000/generate", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ text })
	});
	const data = await res.json();
	return data.image_base64; // data:image/png;base64,...
}
```

如需我在本仓库下新增最小的 Expo 示例工程（`mobile/` 目录），请告诉我你的偏好（Expo/Flutter/uni-app 等）与目标平台（Android/iOS）。