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
import json
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
from kivy.clock import Clock
from kivy.uix.popup import Popup

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
        height: dp(54)
        do_scroll_y: False
        BoxLayout:
            id: kwbox
            size_hint_x: None
            width: self.minimum_width
            height: dp(54)
            spacing: dp(6)
            padding: 0,0

    BoxLayout:
        size_hint_y: None
        height: dp(52)
        spacing: dp(8)
        Button:
            text: '启动'
            on_release: root.on_start_toggle(True)
            font_name: root.app_font
            text_size: self.size
            shorten: True
        Button:
            text: '停止'
            on_release: root.on_start_toggle(False)
            font_name: root.app_font
            text_size: self.size
            shorten: True
        Button:
            text: '选图'
            on_release: root.on_choose_image()
            font_name: root.app_font
            text_size: self.size
            shorten: True
        Button:
            text: '清图'
            on_release: root.on_clear_image()
            font_name: root.app_font
            text_size: self.size
            shorten: True
        ToggleButton:
            id: tb_replace
            text: '做底图(开)' if self.state=='down' else '做底图(关)'
            on_state: root.on_toggle_replace(self.state=='down')
            font_name: root.app_font
            text_size: self.size
            shorten: True

    BoxLayout:
        size_hint_y: None
        height: dp(52)
        spacing: dp(8)
        Button:
            text: '生成'
            on_release: root.on_generate()
            font_name: root.app_font
            text_size: self.size
            shorten: True
        Button:
            text: '保存'
            on_release: root.on_save()
            font_name: root.app_font
            text_size: self.size
            shorten: True
        Button:
            text: '发微信'
            on_release: root.on_share_wechat()
            font_name: root.app_font
            text_size: self.size
            shorten: True
        Button:
            text: '发QQ'
            on_release: root.on_share_qq()
            font_name: root.app_font
            text_size: self.size
            shorten: True

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
        self._acc_receiver = None
        self.replace_base = False

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
        self._acc_receiver = recv  # 保持引用，避免被 GC
        print("辅助功能广播接收器已注册。")

    def on_kv_post(self, base_widget):
        # Android 动态权限弹窗（首次启动提示，一键授权；桌面环境自动跳过）
        self._maybe_show_permission_prompt()

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

    def on_toggle_replace(self, is_on: bool):
        self.replace_base = is_on
        # 可以更新提示
        state = "开" if is_on else "关"
        self.custom_image_hint = f"(自定义图做底图：{state})"

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
            import threading
            from jnius import autoclass, cast, PythonJavaClass, java_method
        except Exception as e:
            print(f"分享失败（缺少 pyjnius/Android 环境）: {e}")
            return

        # 在后台线程中执行写入媒体库，避免卡死 UI
        def worker():
            try:
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
                    File = autoclass('java.io.File')
                    Uri = autoclass('android.net.Uri')
                    file_uri = Uri.fromFile(File(str(out)))
                    intent = _build_intent(file_uri)
                    _start_intent_on_ui(activity, intent)
                    return

                # 写入图片数据
                try:
                    output_stream = resolver.openOutputStream(out_uri)
                    chunk = 4096
                    data = self._last_png
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

                # 构建分享 Intent 并在 UI 线程启动
                intent = _build_intent(out_uri)
                _start_intent_on_ui(activity, intent)
            except Exception as e:
                print(f"分享流程异常: {e}")

        def _build_intent(stream_uri):
            Intent = autoclass('android.content.Intent')
            intent = Intent(Intent.ACTION_SEND)
            intent.setType('image/png')
            intent.putExtra(Intent.EXTRA_STREAM, stream_uri)
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            if package:
                intent.setPackage(package)
            return intent

        def _start_intent_on_ui(activity, intent):
            class Runnable(PythonJavaClass):
                __javainterfaces__ = ['java/lang/Runnable']
                __javacontext__ = 'app'
                def __init__(self, _intent):
                    super().__init__()
                    self._intent = _intent
                @java_method('()V')
                def run(self):
                    try:
                        # 若目标包不可用，则回退 chooser
                        activity.startActivity(self._intent)
                    except Exception:
                        Intent = autoclass('android.content.Intent')
                        String = autoclass('java.lang.String')
                        chooser = Intent.createChooser(self._intent, String('分享图片'))
                        activity.startActivity(chooser)

            try:
                activity.runOnUiThread(Runnable(intent))
            except Exception as e:
                print(f"UI 线程启动失败: {e}")

        threading.Thread(target=worker, daemon=True).start()
        # 上面的后台线程已经完成写入与分享，这里直接返回，避免重复执行导致双重插入或 UI 线程错误
        return

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

    def _request_runtime_permissions(self):
        """Android 6+ 需要在运行时动态申请外部存储/媒体库权限。桌面忽略。"""
        try:
            from jnius import autoclass
            from android.permissions import request_permissions, Permission
        except Exception:
            return

        try:
            Build = autoclass('android.os.Build')
            VERSION = autoclass('android.os.Build$VERSION')
            sdk_int = VERSION.SDK_INT
            perms = []
            if sdk_int >= 33:  # Android 13+ 使用 READ_MEDIA_IMAGES
                perms = [Permission.READ_MEDIA_IMAGES]
            else:
                perms = [Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE]
            if perms:
                try:
                    # 支持回调：授予后提示一次
                    def _cb(perm, results):
                        print(f"权限结果: {list(zip(perm, results))}")
                    request_permissions(perms, _cb)
                except TypeError:
                    request_permissions(perms)
        except Exception as e:
            print(f"请求权限失败: {e}")

    def _maybe_show_permission_prompt(self):
        """首次启动弹窗，说明并引导授权所需权限与可选辅助功能。"""
        try:
            # 非 Android 直接跳过
            import jnius  # noqa: F401
        except Exception:
            return

        try:
            from kivy.app import App as _App
            flag_dir = Path(_App.get_running_app().user_data_dir)
        except Exception:
            return

        flag_dir.mkdir(parents=True, exist_ok=True)
        flag_file = flag_dir / "first_run_permissions.json"
        if flag_file.exists():
            # 已提示过，不再重复
            return

        msg = (
            "为了保存/分享图片以及从相册选择自定义图片，需要授予‘读取媒体/存储’权限。\n\n"
            "若希望在微信/QQ 发送时自动生成并分享，还需在系统‘辅助功能’中启用本应用的服务（可选）。"
        )

        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(8))
        lbl = Label(text=msg, text_size=(dp(300), None), size_hint_y=None)
        # 让多行文本自适应高度
        def _resize_label(*_):
            lbl.texture_update()
            lbl.height = lbl.texture_size[1]
        Clock.schedule_once(_resize_label, 0)
        content.add_widget(lbl)

        btns = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        b_grant = Button(text='授予权限')
        b_access = Button(text='打开辅助功能')
        b_later = Button(text='以后再说')
        btns.add_widget(b_grant)
        btns.add_widget(b_access)
        btns.add_widget(b_later)
        content.add_widget(btns)

        popup = Popup(title='需要的权限', content=content, size_hint=(0.9, None))
        # 动态设置高度
        def _resize_popup(*_):
            total_h = sum(child.height for child in content.children) + dp(80)
            popup.height = max(dp(220), total_h)
        Clock.schedule_once(_resize_popup, 0)

        def _on_grant(_):
            self._request_runtime_permissions()
            # 标记已提示
            try:
                flag_file.write_text(json.dumps({"prompted": True}, ensure_ascii=False))
            except Exception:
                pass
            popup.dismiss()

        def _on_access(_):
            self._open_accessibility_settings()

        def _on_later(_):
            # 首次也写入，避免每次进入都弹，可在设置里再做入口（后续可加）
            try:
                flag_file.write_text(json.dumps({"prompted": True, "later": True}, ensure_ascii=False))
            except Exception:
                pass
            popup.dismiss()

        b_grant.bind(on_release=_on_grant)
        b_access.bind(on_release=_on_access)
        b_later.bind(on_release=_on_later)

        popup.open()

    def _open_accessibility_settings(self):
        """跳转到系统‘辅助功能’设置。桌面忽略。"""
        try:
            from jnius import autoclass
        except Exception:
            return
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            Intent = autoclass('android.content.Intent')
            Settings = autoclass('android.provider.Settings')
            intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
            activity.startActivity(intent)
        except Exception as e:
            print(f"无法打开辅助功能设置: {e}")


class AnanOfflineApp(App):
    def build(self):
        Builder.load_string(KV)
        return Root()


if __name__ == "__main__":
    AnanOfflineApp().run()
