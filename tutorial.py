import os
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton

TUTORIAL_FILE = "tutorial_seen.txt"

def tutorial_seen():
    return os.path.exists(TUTORIAL_FILE)

def mark_tutorial_as_seen():
    with open(TUTORIAL_FILE, "w") as f:
        f.write("seen")

def show_tutorial(app):
    if tutorial_seen():
        return
    dialog = MDDialog(
        title="📘 Quick Tutorial",
        text=(
            "• Long press any downloaded item to:\n"
            "  → View media\n"
            "  → Share to other apps\n"
            "  → Copy caption\n"
            "  → Open in original app\n"
            "  → Repost or delete\n\n"
            "You can always re-access this in your download history!"
        ),
        buttons=[MDRaisedButton(text="Got it", on_release=lambda x: dismiss_dialog(dialog))]
    )
    dialog.open()
    mark_tutorial_as_seen()


def dismiss_dialog(dialog):
    dialog.dismiss()
