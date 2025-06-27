import re
from kivy.core.clipboard import Clipboard

PATTERNS = {
    "instagram": r"instagram\.com\/(p|reel|tv|stories)\/",
    "youtube": r"(youtube\.com\/watch\?v=|youtu\.be\/)",
    "tiktok": r"tiktok\.com\/@[\w\.\-]+\/video\/\d+",
    "twitter": r"(twitter\.com|x\.com)\/\w+\/status\/\d+"
}

def detect_platform(url: str) -> str:
    if url.strip() == "whatsapp-status":
        return "whatsapp"
    for plat, pat in PATTERNS.items():
        if re.search(pat, url):
            return plat
    return "unknown"

def get_clipboard_social_url():
    content = Clipboard.paste().strip()
    if detect_platform(content) != "unknown":
        return content
    return ""

