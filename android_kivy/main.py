"""Kivy 离线版：在 Android 上直接生成素描本图片（单 APK，无需后端）。

使用已有的 `text_fit_draw.py` 与 `image_fit_paste.py` 算法，结合 Kivy UI。
依赖：kivy, pillow

打包：
  1. 安装 buildozer (Ubuntu 推荐)：
       sudo apt update && sudo apt install -y python3-pip git
       pip install --upgrade buildozer cython
       sudo apt install -y openjdk-17-jdk pkg-config libSDL2-dev libffi-dev libblas-dev liblapack-dev libjpeg-dev libz-dev
  2. 在本目录 `android_kivy/` 下执行：
       buildozer android debug
  3. 生成的 APK 位于 bin/ 目录。

注意：请先把根目录下的 `BaseImages/` 文件夹与 `font.ttf` 复制到本目录，使路径与 `config_mobile.py` 一致：
  android_kivy/BaseImages/*
  android_kivy/font.ttf

后续可扩展：
  - 添加选择图片贴入（调用 paste_image_auto）
  - 增加保存到图库权限
  - 增加差分按钮滚动容器
"""

from io import BytesIO
from pathlib import Path

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.core.image import Image as CoreImage
from kivy.core.text import LabelBase
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.metrics import dp

from config_mobile import (
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

try:
    from plyer import filechooser
except Exception:
    filechooser = None

KV = """
<Root>:
    orientation: 'vertical'
    padding: dp(12)
    spacing: dp(8)
    # 统一指定中文字体，避免 Android 默认字体缺失导致乱码
    # root.app_font 在 Root.__init__ 中设定为注册的字体名

    Label:
        text: '安安的素描本 (离线 APK)'
        font_size: '20sp'
        size_hint_y: None
        height: self.texture_size[1] + dp(6)
        font_name: root.app_font

    TextInput:
        id: ti
        hint_text: '输入文字，含 #开心# 等关键词切换底图；使用【】括号变紫色'
        size_hint_y: None
        height: dp(120)
        multiline: True
        font_name: root.app_font

    ScrollView:
        size_hint_y: None
        height: dp(50)
        do_scroll_y: False
        BoxLayout:
            id: kwbox
            size_hint_x: None
            width: self.minimum_width
            height: dp(50)
            spacing: dp(8)
            padding: 0,0

    BoxLayout:
        size_hint_y: None
        height: dp(44)
        spacing: dp(8)
        Button:
            text: '启动'
            on_release: root.on_start_toggle(True)
            font_name: root.app_font
        Button:
            text: '终止'
            on_release: root.on_start_toggle(False)
            font_name: root.app_font
        Button:
            text: '选择自定义图片'
            on_release: root.on_choose_image()
            font_name: root.app_font
        Button:
            text: '清除自定义图片'
            on_release: root.on_clear_image()
            font_name: root.app_font

    BoxLayout:
        size_hint_y: None
        height: dp(44)
        spacing: dp(8)
        Button:
            text: '生成图片'
            on_release: root.on_generate()
            font_name: root.app_font
        Button:
            text: '保存 PNG'
            on_release: root.on_save()
            font_name: root.app_font

    Image:
        id: preview
        source: root.preview_source
        allow_stretch: True
        keep_ratio: True
        size_hint_y: 1

    Label:
        text: root.custom_image_hint
        size_hint_y: None
        height: self.texture_size[1] + dp(6)
        font_name: root.app_font
"""


class Root(BoxLayout):
    preview_source = StringProperty("")
    custom_image_hint = StringProperty("(当前未选择自定义图片，使用文字生成)")
    active = BooleanProperty(True)
    _last_png = b""
    _custom_image = None  # PIL Image or None
    app_font = StringProperty("AppFont")  # 注册字体的内部名称

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 在应用启动前注册字体，确保中文/全角括号显示正常
        font_path = Path(__file__).parent / "font.ttf"
        if font_path.exists():
            try:
                LabelBase.register(name="AppFont", fn_regular=str(font_path))
            except Exception as e:
                print(f"字体注册失败，退回默认字体: {e}")
                self.app_font = ""  # 空则使用默认
        else:
            print("font.ttf 未找到，界面可能出现乱码。")
            self.app_font = ""

    def on_kv_post(self, base_widget):
        # 动态生成差分关键词按钮
        kwbox = self.ids.kwbox
        for kw in BASEIMAGE_MAPPING.keys():
            btn = Button(text=kw, size_hint=(None, None), height=dp(40), width=dp(90))
            btn.bind(on_release=lambda inst, k=kw: self.insert_keyword(k))
            kwbox.add_widget(btn)

    def insert_keyword(self, kw: str):
        ti: TextInput = self.ids.ti
        ti.text = (ti.text or "") + kw

    def _pick_base_image(self, text: str) -> tuple[str, str]:
        base = BASEIMAGE_FILE
        cleaned = text
        for k, v in BASEIMAGE_MAPPING.items():
            if k in cleaned:
                base = v
                cleaned = cleaned.replace(k, "").strip()
                break
        return base, cleaned

    def on_generate(self):
        if not self.active:
            print("已终止：请先点击‘启动’再生成。")
            return

        text = (self.ids.ti.text or "").strip()
        base_image_file, cleaned = self._pick_base_image(text)
        overlay = BASE_OVERLAY_FILE if USE_BASE_OVERLAY else None

        try:
            if self._custom_image is not None:
                # 自定义图片贴入
                png = paste_image_auto(
                    image_source=base_image_file,
                    image_overlay=overlay,
                    top_left=TEXT_BOX_TOPLEFT,
                    bottom_right=IMAGE_BOX_BOTTOMRIGHT,
                    content_image=self._custom_image,
                    align="center",
                    valign="middle",
                    padding=12,
                    allow_upscale=True,
                    keep_alpha=True,
                )
            else:
                # 文本绘制
                png = draw_text_auto(
                    image_source=base_image_file,
                    image_overlay=overlay,
                    top_left=TEXT_BOX_TOPLEFT,
                    bottom_right=IMAGE_BOX_BOTTOMRIGHT,
                    text=cleaned,
                    color=(0, 0, 0),
                    max_font_height=64,
                    font_path=FONT_FILE,
                )
        except Exception as e:
            from kivy.logger import Logger
            Logger.exception(f"生成失败: {e}")
            return

        self._last_png = png
        data = BytesIO(png)
        ci = CoreImage(data, ext="png")
        self.ids.preview.texture = ci.texture

    def on_save(self):
        if not self._last_png:
            return
        out = Path(App.get_running_app().user_data_dir) / "output.png"
        out.write_bytes(self._last_png)
        print(f"Saved: {out}")

    def on_start_toggle(self, flag: bool):
        self.active = flag
        print(f"active = {self.active}")

    def on_choose_image(self):
        if filechooser is None:
            print("未安装 plyer，无法选择文件。")
            return

        def _cb(selection):
            try:
                if not selection:
                    return
                path = selection[0]
                from PIL import Image as PILImage
                img = PILImage.open(path).convert("RGBA")
                self._custom_image = img
                self.custom_image_hint = f"(已选择自定义图片：{Path(path).name})"
            except Exception as e:
                from kivy.logger import Logger
                Logger.exception(f"选择图片失败: {e}")

        try:
            filechooser.open_file(title="选择自定义图片", filters=["*.png", "*.jpg", "*.jpeg"], on_selection=_cb)
        except TypeError:
            # 某些平台不支持回调式，尝试直接返回列表
            sel = filechooser.open_file(title="选择自定义图片", filters=["*.png", "*.jpg", "*.jpeg"])
            _cb(sel)

    def on_clear_image(self):
        self._custom_image = None
        self.custom_image_hint = "(当前未选择自定义图片，使用文字生成)"


class AnanOfflineApp(App):
    def build(self):
        Builder.load_string(KV)
        return Root()


if __name__ == "__main__":
    AnanOfflineApp().run()
