import os, threading
from kivy.clock import mainthread, Clock
from kivy.core.clipboard import Clipboard
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.tab import MDTabsBase, MDTabs
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivy.uix.image import AsyncImage
from kivy.uix.scrollview import ScrollView
from utils import detect_platform
from media_parser import parse_yt_dlp_metadata, parse_whatsapp_status_media
from downloader import download_file
from history import load_history, save_history_entry
from progressbar import AnimatedProgressBar

PLATFORMS = ['instagram', 'youtube', 'x', 'tiktok', 'whatsapp']
CLIP_POLL_SECS = 2


class PlatformTab(MDBoxLayout, MDTabsBase):
    def __init__(self, platform, **kwargs):
        super().__init__(orientation='vertical', spacing=12, padding=12, **kwargs)
        self.platform = platform
        self.dialog = None
        self.setup_ui()

    def setup_ui(self):
        self.linkfield = MDTextField(
            hint_text=f"{self.platform.capitalize()} link / status",
            size_hint_y=None,
            height=dp(48),
            mode="rectangle",
        )

        btn_row = MDBoxLayout(size_hint_y=None, height=dp(48), spacing=8)
        btn_paste = MDRaisedButton(text="PASTE", on_release=self.on_paste)
        btn_download = MDRaisedButton(text="DOWNLOAD", md_bg_color=(0, 0.5, 0, 1), on_release=self.on_download)
        btn_row.add_widget(btn_paste)
        btn_row.add_widget(btn_download)

        self.progress = AnimatedProgressBar(size_hint_y=None, height=4)
        self.progress.reset()

        self.history_label = MDLabel(
            text="History",
            bold=True,
            halign="left",
            size_hint_y=None,
            height=dp(30)
        )
        self.no_media_label = MDLabel(
            text="No downloaded media",
            halign="center",
            theme_text_color="Hint",
            size_hint_y=None,
            height=dp(40)
        )

        self.history_container = MDBoxLayout(orientation='vertical', size_hint_y=None, spacing=8, padding=(0, 8))
        self.history_container.bind(minimum_height=self.history_container.setter("height"))
        self.history_container.add_widget(self.no_media_label)

        scroll = ScrollView()
        scroll.add_widget(self.history_container)

        self.add_widget(self.linkfield)
        self.add_widget(btn_row)
        self.add_widget(self.progress)
        self.add_widget(self.history_label)
        self.add_widget(scroll)

        self.load_history()

    def on_paste(self, *_):
        self.linkfield.text = Clipboard.paste().strip()

    def on_download(self, *_):
        text = self.linkfield.text.strip()
        if not text and self.platform != 'whatsapp':
            self.show_error("Please paste a link first")
            return
        threading.Thread(target=self.download_flow, args=(text), daemon=True).start()

    def download_flow(self, text):
        self.progress.reset()
        items = []
        try:
            if self.platform == 'whatsapp':
                res = parse_whatsapp_status_media()
                items = res['media']
            else:
                res = parse_yt_dlp_metadata(text)
                if 'error' in res:
                    return self.show_error(res['error'])
                items = [{'url': u, 'caption': res['caption'], 'username': res['username'], 'thumb': res['thumbnail']} for u in res['media']]

            if not items:
                return self.show_error("No media found")

            if len(items) == 1:
                self._download_items(items)
            else:
                self.show_selection_modal(items)

        except Exception as e:
            self.show_error(f"Error: {str(e)}")

    @mainthread
    def show_error(self, msg):
        dialog = MDDialog(
            title="Error",
            text=msg,
            buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())]
        )
        dialog.open()

    @mainthread
    def show_selection_modal(self, items):
        selected = {item['url']: True for item in items}
        content = MDBoxLayout(orientation='vertical', spacing=8, padding=8)

        for it in items:
            row = MDBoxLayout(size_hint_y=None, height=40, spacing=10)
            icon = MDIconButton(
                icon="checkbox-marked",
                theme_text_color="Custom",
                text_color=(0, 1, 0, 1),
                on_release=lambda btn, u=it['url']: self.toggle_one(btn, u, selected)
            )
            lbl = MDLabel(text=os.path.basename(it['url']), size_hint_x=0.8)
            row.add_widget(icon)
            row.add_widget(lbl)
            content.add_widget(row)

        self.dialog = MDDialog(
            title="Select media to download",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="Download", on_release=lambda *_: (self.dialog.dismiss(), self._confirmed_download(items, selected))),
                MDFlatButton(text="Cancel", on_release=lambda *_: self.dialog.dismiss())
            ]
        )
        self.dialog.open()

    def toggle_one(self, button, url, sel):
        sel[url] = not sel[url]
        button.icon = "checkbox-marked" if sel[url] else "checkbox-blank-outline"

    def _confirmed_download(self, items, selected):
        chosen = [it for it in items if selected[it['url']]]
        if not chosen:
            return self.show_error("Select at least one media")
        self._download_items(chosen)

    def _download_items(self, items):
        for it in items:
            fname = os.path.basename(it['url']).split('?')[0]
            path = os.path.join(download_file.DIRECTORY, fname)
            if os.path.exists(path):
                self.show_error(f"{fname} already exists")
            else:
                download_file(it['url'], fname, on_progress=self.on_progress)

            save_history_entry(self.platform, {
                'path': path,
                'caption': it.get('caption', ''),
                'user': it.get('username', ''),
                'thumb': it.get('thumb', ''),
                'platform': self.platform
            })
            self.add_history_item({
                'path': path,
                'caption': it.get('caption', ''),
                'user': it.get('username', ''),
                'thumb': it.get('thumb', '')
            })

        self.linkfield.text = ""
        self.progress.animate_complete()

    @mainthread
    def on_progress(self, pct):
        self.progress.value = pct

    def load_history(self):
        allh = load_history()
        loaded = False
        for e in allh:
            if e.get('platform') == self.platform:
                self.add_history_item(e)
                loaded = True
        if not loaded:
            self.show_no_history()

    @mainthread
    def show_no_history(self):
        self.no_media_label.text = "No downloaded media"
        self.no_media_label.opacity = 1

    @mainthread
    def add_history_item(self, e):
        if self.no_media_label in self.history_container.children:
            self.history_container.remove_widget(self.no_media_label)

        card = MDCard(
            orientation='horizontal',
            size_hint_y=None,
            height=120,
            padding=12,
            spacing=12,
            md_bg_color=(0.1, 0.1, 0.1, 1),
            radius=[12]
        )
        img = AsyncImage(source=e['thumb'], size_hint=(None, None), size=(100, 100))
        text_box = MDBoxLayout(orientation='vertical', spacing=4)
        text_box.add_widget(MDLabel(text=e.get('user', ''), bold=True, theme_text_color="Custom", text_color=(1, 1, 1, 1)))
        text_box.add_widget(MDLabel(
            text=(e.get('caption', '')[:60] + "...") if len(e.get('caption', '')) > 60 else e.get('caption', ''),
            theme_text_color="Secondary"
        ))

        btn = MDRaisedButton(
            text="⬇",
            md_bg_color=(0, 0.5, 0, 1),
            on_release=lambda *_: download_file(e['path'], os.path.basename(e['path']), on_progress=self.on_progress)
        )
        card.add_widget(img)
        card.add_widget(text_box)
        card.add_widget(btn)

        self.history_container.add_widget(card)



class StealthApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.primary_hue = "900"
        self.tabs = MDTabs()
        self.tab_map = {}

        for p in PLATFORMS:
            tab = PlatformTab(p, title=p.capitalize())
            self.tabs.add_widget(tab)
            self.tab_map[p] = tab

        self.last_clip = ""
        return self.tabs

    def on_start(self):
        Clock.schedule_interval(self.check_clip, CLIP_POLL_SECS)

    def check_clip(self, dt):
        try:
            clip = Clipboard.paste().strip()
            if clip == self.last_clip:
                return
            self.last_clip = clip

            plat = detect_platform(clip)
            if plat != "unknown" and plat in self.tab_map:
                current_tab = self.tabs.get_current_tab()
                if current_tab.text.lower() != plat:
                    self.tabs.switch_tab(self.tab_map[plat])
                self.tab_map[plat].linkfield.text = clip
                self.tab_map[plat].on_download()
        except Exception as e:
            print(f"Clipboard check error: {e}")


if __name__ == "__main__":
    StealthApp().run()

