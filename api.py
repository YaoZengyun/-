"""
FastAPI 后端服务：将现有的文字/图片绘制能力通过 HTTP 暴露为接口，便于移动端调用。

- POST /generate  按文本或图片生成素描本图片，返回 base64 PNG
- GET  /bases      列出可用的底图映射（来自 config.BASEIMAGE_MAPPING）

说明：
- 该服务不依赖 Windows 特定能力（不使用键盘/剪贴板/Win32），可跨平台运行。
- 默认遵循 config.py 中的坐标、字体、覆盖层、底图等配置。
"""
from __future__ import annotations

import base64
from io import BytesIO
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from PIL import Image

from config import (
    FONT_FILE,
    BASEIMAGE_MAPPING,
    BASEIMAGE_FILE,
    TEXT_BOX_TOPLEFT,
    IMAGE_BOX_BOTTOMRIGHT,
    BASE_OVERLAY_FILE,
    USE_BASE_OVERLAY,
)
from text_fit_draw import draw_text_auto
from image_fit_paste import paste_image_auto


app = FastAPI(title="Anan Sketchbook API", version="1.0.0")

# CORS：默认允许所有来源，开发联调更方便；生产环境建议收紧
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    text: Optional[str] = Field(None, description="要绘制的文本；若提供，则按自适应字号绘制")
    image_base64: Optional[str] = Field(
        None,
        description="要贴入的图片，base64（data URL 或纯 base64 都可）。若提供，则按 contain 规则贴入",
    )
    base_key: Optional[str] = Field(
        None,
        description="可选：指定底图映射键（例如 '#开心#'）；若留空，将使用默认底图，且会在 text 中自动识别切换关键词",
    )
    use_overlay: Optional[bool] = Field(
        None,
        description="是否叠加遮挡层；默认遵循 config.USE_BASE_OVERLAY",
    )


class GenerateResponse(BaseModel):
    image_base64: str
    width: int
    height: int
    used_base: str


def _strip_data_url(b64: str) -> str:
    """移除 data URL 头部。如 'data:image/png;base64,xxxx' -> 'xxxx'"""
    if "," in b64:
        return b64.split(",", 1)[1]
    return b64


@app.get("/bases")
def list_bases():
    return {
        "default": BASEIMAGE_FILE,
        "mapping": BASEIMAGE_MAPPING,
    }


@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    text = (req.text or "").strip()
    image_b64 = req.image_base64

    if not text and not image_b64:
        raise HTTPException(status_code=400, detail="必须提供 text 或 image_base64 之一")

    # 选择底图
    base_image_file = BASEIMAGE_FILE
    if req.base_key and req.base_key in BASEIMAGE_MAPPING:
        base_image_file = BASEIMAGE_MAPPING[req.base_key]
    else:
        # 若未显式指定 base_key，则在文本中识别切换关键词（同 main.py 逻辑）
        for keyword, img_file in BASEIMAGE_MAPPING.items():
            if keyword in text:
                base_image_file = img_file
                text = text.replace(keyword, "").strip()
                break

    overlay_file = BASE_OVERLAY_FILE if (req.use_overlay if req.use_overlay is not None else USE_BASE_OVERLAY) else None

    try:
        if image_b64:
            # 图片贴入模式
            raw = base64.b64decode(_strip_data_url(image_b64))
            with BytesIO(raw) as bio:
                content_img = Image.open(bio).convert("RGBA")
            png_bytes = paste_image_auto(
                image_source=base_image_file,
                image_overlay=overlay_file,
                top_left=TEXT_BOX_TOPLEFT,
                bottom_right=IMAGE_BOX_BOTTOMRIGHT,
                content_image=content_img,
                align="center",
                valign="middle",
                padding=12,
                allow_upscale=True,
                keep_alpha=True,
            )
        else:
            # 文本绘制模式
            png_bytes = draw_text_auto(
                image_source=base_image_file,
                image_overlay=overlay_file,
                top_left=TEXT_BOX_TOPLEFT,
                bottom_right=IMAGE_BOX_BOTTOMRIGHT,
                text=text,
                color=(0, 0, 0),
                max_font_height=64,
                font_path=FONT_FILE,
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {e}")

    # 返回 base64
    with BytesIO(png_bytes) as bio:
        img = Image.open(BytesIO(png_bytes))
        w, h = img.size
    return GenerateResponse(
        image_base64="data:image/png;base64," + base64.b64encode(png_bytes).decode("utf-8"),
        width=w,
        height=h,
        used_base=base_image_file,
    )


@app.get("/")
def root():
    return {"ok": True, "service": "Anan Sketchbook API", "endpoints": ["GET /bases", "POST /generate"]}


# 允许 `python api.py` 直接启动开发服务器
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
