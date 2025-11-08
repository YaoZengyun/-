# Android/Kivy 离线版配置
# 注意：这里的路径使用相对当前模块的 POSIX 路径，打包到 APK 后也能正常寻址。
from pathlib import Path

ASSETS_DIR = Path(__file__).parent

# 字体文件
FONT_FILE = str(ASSETS_DIR / "font.ttf")

# 底图与遮罩
BASEIMAGE_MAPPING = {
    "#普通#": str(ASSETS_DIR / "BaseImages/base.png"),
    "#开心#": str(ASSETS_DIR / "BaseImages/开心.png"),
    "#生气#": str(ASSETS_DIR / "BaseImages/生气.png"),
    "#无语#": str(ASSETS_DIR / "BaseImages/无语.png"),
    "#脸红#": str(ASSETS_DIR / "BaseImages/脸红.png"),
    "#病娇#": str(ASSETS_DIR / "BaseImages/病娇.png"),
}

BASEIMAGE_FILE = str(ASSETS_DIR / "BaseImages/base.png")
BASE_OVERLAY_FILE = str(ASSETS_DIR / "BaseImages/base_overlay.png")
USE_BASE_OVERLAY = True

# 素描本可写区域（与原项目一致）
TEXT_BOX_TOPLEFT = (119, 450)
IMAGE_BOX_BOTTOMRIGHT = (119 + 279, 450 + 175)
