import os
import time
import webbrowser
import json
from functools import partial
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.list import TwoLineAvatarIconListItem, IconLeftWidget
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu
from kivy.core.clipboard import Clipboard
from history import load_history

DOWNLOAD_DIR = "/storage/emulated/0/Download/StealthFetcher/"


class MediaItem(ButtonBehavior, BoxLayout):
    def __init__(self, entry, **kwargs):
        super().__init__(**kwargs)
        self.entry = entry
        self.orientation = "vertical"
        self.last_touch_time = 0

        # Create the list item UI
        self.list_item = TwoLineAvatarIconListItem(
            text=entry["username"],
            secondary_text=(entry["caption"][:60] + "...") if entry["caption"] else "No caption"
        )
        self.icon = IconLeftWidget(icon="image")
        self.list_item.add_widget(self.icon)
        self.add_widget(self.list_item)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.last_touch_time = time.time()
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            held_time = time.time() - self.last_touch_time
            if held_time >= 1.5:  # Long press after 1.5s
                self.show_options()
        return super().on_touch_up(touch)

    def show_options(self):
        options = [
            {"text": "📂 View", "callback": self.view_media},
            {"text": "📤 Share", "callback": self.share_media},
            {"text": "📋 Copy Caption", "callback": self.copy_caption},
            {"text": "🔗 Open in App", "callback": self.open_link},
            {"text": "🔁 Repost", "callback": self.repost},
            {"text": "🗑️ Delete", "callback": self.delete_entry}
        ]

        items = [
            {
                "text": o["text"],
                "on_release": partial(self.run_and_dismiss, callback=o["callback"])
            } for o in options
        ]

        self.menu = MDDropdownMenu(caller=self, items=items, width_mult=4)
        self.menu.open()

    def run_and_dismiss(self, *args, callback=None, **kwargs):
        self.menu.dismiss()
        if callback:
            callback()

    def view_media(self):
        for f in self.entry["media_files"]:
            os.system(f"am start -a android.intent.action.VIEW -d file://{f}")

    def share_media(self):
        for f in self.entry["media_files"]:
            os.system(
                f'am start -a android.intent.action.SEND -t "*/*" --es android.intent.extra.STREAM file://{f}'
            )

    def copy_caption(self):
        Clipboard.copy(self.entry.get("caption", ""))

    def open_link(self):
        webbrowser.open(self.entry["link"])

    def repost(self):
        for f in self.entry["media_files"]:
            os.system(
                f'am start -a android.intent.action.SEND -t "*/*" --es android.intent.extra.STREAM file://{f}'
            )

    def delete_entry(self):
        # Delete files
        for f in self.entry["media_files"]:
            try:
                os.remove(f)
            except Exception:
                pass

        # Delete from JSON
        path = "history.json"
        if os.path.exists(path):
            with open(path, "r") as f:
                history = json.load(f)
            history = [h for h in history if h["timestamp"] != self.entry["timestamp"]]
            with open(path, "w") as f:
                json.dump(history, f, indent=2)

        # Optional: Show deletion confirmation
        print(f"Deleted {len(self.entry['media_files'])} file(s).")


class HistoryScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        history = load_history()
        self.layout = MDBoxLayout(orientation='vertical', padding=10, spacing=10)

        if not history:
            from kivymd.uix.label import MDLabel
            self.layout.add_widget(MDLabel(text="No download history yet.", halign="center"))
        else:
            for entry in reversed(history):
                item = MediaItem(entry)
                self.layout.add_widget(item)

        self.add_widget(self.layout)
