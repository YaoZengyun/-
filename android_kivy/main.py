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
import re
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
from kivy.uix.togglebutton import ToggleButton
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
        ToggleButton:
            id: tb_replace
            text: '自定义图做底图: 开' if self.state=='down' else '自定义图做底图: 关'
            on_state: root.on_toggle_replace(self.state=='down')
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
        Button:
            text: '分享微信'
            on_release: root.on_share_wechat()
            font_name: root.app_font
        Button:
            text: '分享QQ'
            on_release: root.on_share_qq()
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

        # 延迟注册辅助功能广播：放到 on_kv_post 之后，避免过早触发导致启动阶段崩溃
        self._acc_registered = False

    def _register_accessibility_receiver(self):
        try:
            from jnius import autoclass, PythonJavaClass, java_method
        except Exception as e:
            print(f"无法加载 pyjnius，辅助功能广播监听未启用: {e}")
            return

        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity
        IntentFilter = autoclass('android.content.IntentFilter')
        filter = IntentFilter('org.anan.sketchbook.ACCESS_SENT_TEXT')

        class Receiver(PythonJavaClass):
            __javainterfaces__ = ['android/content/BroadcastReceiver']
            __javacontext__ = 'app'

            @java_method('(Landroid/content/Context;Landroid/content/Intent;)V')
            def onReceive(self, context, intent):
                try:
                    text = intent.getStringExtra('text')
                    src_pkg = intent.getStringExtra('package')
                    if text:
                        print(f"[Accessibility] 收到来自 {src_pkg} 的文本: {text}")
                        # 更新输入框并生成图片，然后尝试自动分享
                        self_ref = self_py_ref()
                        if self_ref is None:
                            return
                        ti = self_ref.ids.get('ti')
                        if ti:
                            ti.text = text
                        self_ref.on_generate()
                        # 可选：自动分享到对应 App
                        if src_pkg == 'com.tencent.mm':
                            self_ref.on_share_wechat()
                        elif src_pkg == 'com.tencent.mobileqq':
                            self_ref.on_share_qq()
                except Exception as e:
                    print(f"广播处理失败: {e}")

        # 保留对 Root 实例的弱引用，避免闭包循环
        import weakref
        self_py_ref = weakref.ref(self)
        recv = Receiver()
        activity.registerReceiver(recv, filter)
        print("辅助功能广播接收器已注册。")

    def on_kv_post(self, base_widget):
        # 动态生成差分关键词按钮
        kwbox = self.ids.kwbox
        for kw in BASEIMAGE_MAPPING.keys():
            btn = Button(text=kw, size_hint=(None, None), height=dp(40), width=dp(90))
            try:
                # 强制按钮使用中文字体，避免乱码
                btn.font_name = self.app_font or btn.font_name
            except Exception:
                pass
            btn.bind(on_release=lambda inst, k=kw: self.insert_keyword(k))
            kwbox.add_widget(btn)

        # 在 KV 构建完成后再注册广播，降低启动崩溃风险
        if not getattr(self, '_acc_registered', False):
            try:
                self._register_accessibility_receiver()
                self._acc_registered = True
            except Exception as e:
                print(f"辅助功能广播注册失败: {e}")

    def insert_keyword(self, kw: str):
        ti: TextInput = self.ids.ti
        ti.text = (ti.text or "") + kw

    def _pick_base_image(self, text: str) -> tuple[str, str]:
        """解析文本中的底图标记，支持 '#开心#' 或 '##开心##' 等格式。"""
        base = BASEIMAGE_FILE
        cleaned = text or ""
        tokens = re.findall(r"#+([^#]+)#+", cleaned)
        norm = [t.strip() for t in tokens if t.strip()]
        chosen = None
        for k, v in BASEIMAGE_MAPPING.items():
            inner = k.strip('#').strip()
            if inner in norm or k in cleaned:
                chosen = (k, v)
                break
        if chosen:
            _, base = chosen
            cleaned = re.sub(r"#+([^#]+)#+", "", cleaned)
            for k in BASEIMAGE_MAPPING.keys():
                cleaned = cleaned.replace(k, "")
            cleaned = cleaned.strip()
        return base, cleaned

    def on_generate(self):
        if not self.active:
            print("已终止：请先点击‘启动’再生成。")
            return

        text = (self.ids.ti.text or "").strip()
        base_image_file, cleaned = self._pick_base_image(text)
        overlay = BASE_OVERLAY_FILE if USE_BASE_OVERLAY else None

        try:
            if self._custom_image is not None and getattr(self, 'replace_base', False):
                png = draw_text_auto(
                    image_source=self._custom_image,
                    image_overlay=overlay,
                    top_left=TEXT_BOX_TOPLEFT,
                    bottom_right=IMAGE_BOX_BOTTOMRIGHT,
                    text=cleaned,
                    color=(0, 0, 0),
                    max_font_height=64,
                    font_path=FONT_FILE,
                )
            elif self._custom_image is not None:
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

    # --- Share helpers ---
    def _share_last_png(self, package: str | None):
        if not self._last_png:
            print("没有可分享的图片，请先生成。")
            return
        try:
            from jnius import autoclass, cast
        except Exception as e:
            print(f"分享失败（缺少 pyjnius/Android 环境）: {e}")
            return

        # 1) 将图片写入到媒体库，获取 content:// Uri
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity
        MediaStore = autoclass('android.provider.MediaStore')
        ContentValues = autoclass('android.content.ContentValues')
        String = autoclass('java.lang.String')
        resolver = activity.getContentResolver()

        values = ContentValues()
        values.put(String('title'), String('anan_sketchbook.png'))
        values.put(String('mime_type'), String('image/png'))
        images_uri = MediaStore.Images.Media.EXTERNAL_CONTENT_URI
        out_uri = resolver.insert(images_uri, values)
        if out_uri is None:
            print("无法写入媒体库，改为仅保存到应用目录后分享。")
            out = Path(App.get_running_app().user_data_dir) / "share.png"
            out.write_bytes(self._last_png)
            # 尝试使用 file:// 可能在高版本失败
            try:
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')
                File = autoclass('java.io.File')
                intent = Intent(Intent.ACTION_SEND)
                intent.setType('image/png')
                file_uri = Uri.fromFile(File(str(out)))
                intent.putExtra(Intent.EXTRA_STREAM, cast('android.os.Parcelable', file_uri))
                intent.addFlags(1)  # FLAG_GRANT_READ_URI_PERMISSION
                if package:
                    intent.setPackage(package)
                activity.startActivity(intent)
            except Exception as e:
                print(f"分享失败: {e}")
            return

        # 写入字节到 Uri 的输出流
        try:
            output_stream = resolver.openOutputStream(out_uri)
            # 将 python bytes 拆块写入 Java OutputStream
            chunk = 4096
            data = self._last_png
            # jnius 对于 Python bytes 支持 write(bytearray)
            from array import array
            idx = 0
            while idx < len(data):
                part = data[idx: idx + chunk]
                ba = bytearray(part)
                output_stream.write(ba)
                idx += chunk
            output_stream.flush()
            output_stream.close()
        except Exception as e:
            print(f"写入媒体库失败: {e}")

        # 2) 发送分享 Intent（尝试直达指定包名，否则弹系统分享面板）
        try:
            Intent = autoclass('android.content.Intent')
            intent = Intent(Intent.ACTION_SEND)
            intent.setType('image/png')
            intent.putExtra(Intent.EXTRA_STREAM, out_uri)
            # 需要授予读取权限
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            if package:
                intent.setPackage(package)
                try:
                    activity.startActivity(intent)
                    return
                except Exception:
                    # 如果目标 app 不可用，回退到 chooser
                    pass
            chooser = Intent.createChooser(intent, String('分享图片'))
            activity.startActivity(chooser)
        except Exception as e:
            print(f"启动分享失败: {e}")

    def on_share_wechat(self):
        # com.tencent.mm 为微信包名
        self._share_last_png('com.tencent.mm')

    def on_share_qq(self):
        # com.tencent.mobileqq 为 QQ 包名
        self._share_last_png('com.tencent.mobileqq')

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
