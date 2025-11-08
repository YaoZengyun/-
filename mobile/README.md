# 移动端示例 (Expo React Native)

该目录提供最小的 Expo 前端示例代码片段，演示如何调用后端 `api.py` 的 `/generate` 接口并显示返回的图片。

## 目录结构
- `App.js` 主入口（需放入 Expo 项目中）

由于完整 Expo 初始化需要运行 `npx create-expo-app`, 这里仅给出核心代码，你可以：

```powershell
npx create-expo-app sketchbook-mobile
cd sketchbook-mobile
# 将本目录下的 App.js 覆盖新项目中的 App.js
```

然后安装依赖（仅 fetch 即可，无需额外包）。

## 后端地址配置
将 `API_BASE` 改成你电脑在局域网中的 IP（例如 192.168.x.x），确保手机和电脑在同一网络，且防火墙允许 8000 端口访问。

## 功能说明
- 输入文本，点击“生成图片”
- 支持关键词自动切换底图（与后端一致）
- 显示生成结果 PNG（base64）

## 后续可扩展
- 加入图片选择（expo-image-picker）并传 base64 到 `image_base64`
- 进度/错误提示/缓存最近结果
- 保存到相册（expo-media-library）

---
