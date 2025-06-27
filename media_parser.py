import yt_dlp
import os
from utils import detect_platform

COOKIE_FILE = "cookies/instagram.txt"
os.makedirs("cookies", exist_ok=True)

WHATSAPP_STATUS_DIR = "/storage/emulated/0/WhatsApp/Media/.Statuses/"

def parse_yt_dlp_metadata(url, username=None, password=None):
    try:
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "cookiefile": COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
        }

        # Handle optional login and cookie saving
        if not os.path.exists(COOKIE_FILE) and username and password:
            ydl_opts.update({
                "username": username,
                "password": password,
                "cookiefile": COOKIE_FILE,
                "write_cookies": True,
            })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        media = []

        if "entries" in info:
            for entry in info["entries"]:
                media_url = entry.get("url")
                if media_url:
                    media.append(media_url)
        elif "url" in info:
            media.append(info["url"])

        return {
            "caption": info.get("title", ""),
            "username": info.get("uploader", ""),
            "thumbnail": info.get("thumbnail", ""),
            "media": media,
        }

    except Exception as e:
        return {"error": str(e)}

# Instagram uses the same function
def parse_instagram_metadata(url, username=None, password=None):
    return parse_yt_dlp_metadata(url, username, password)

# WhatsApp local status fetch
def parse_whatsapp_status_media():
    files = []

    if os.path.isdir(WHATSAPP_STATUS_DIR):
        for fname in sorted(os.listdir(WHATSAPP_STATUS_DIR)):
            if fname.lower().endswith((".jpg", ".jpeg", ".png", ".mp4", ".gif")):
                path = os.path.join(WHATSAPP_STATUS_DIR, fname)
                files.append({
                    "url": path,
                    "caption": f"WhatsApp status: {fname}",
                    "username": "WhatsApp Status",
                    "thumbnail": path,
                })

    return {"media": files}

