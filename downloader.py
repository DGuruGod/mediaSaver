import yt_dlp
import requests
import os

# Try Android path, fall back to local directory
try:
    from android.storage import primary_external_storage_path
    DOWNLOAD_DIR = os.path.join(primary_external_storage_path(), "Download", "StealthFetcher")
except ImportError:
    DOWNLOAD_DIR = os.path.join(os.getcwd(), "StealthFetcher")

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

DIRECTORY = DOWNLOAD_DIR


def download_file(url, filename, on_progress=None):
    path = os.path.join(DOWNLOAD_DIR, filename)
    try:
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            total = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    if chunk:
                        file.write(chunk)
                        downloaded += len(chunk)
                        if on_progress and total:
                            percent = (downloaded * 100 / total)
                            on_progress(percent)

        return path
    except Exception as e:
        return {"error": str(e)}


def download_from_ytdlp(url, on_progress=None):
    class YTDLogger:
        def debug(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): print(f"[YTDLP ERROR]: {msg}")
        

        # ✅ Prevent 'str' object has no attribute 'write'
        def write(self, msg):
            print(f"[YTDLP] {msg.strip()}")
        
        def flush(self): pass  # Required by file-like objects

    def hook(d):
        if d.get("status") == "downloading" and on_progress:
            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes", 1)
            if total:
                percent = (downloaded * 100 / total)
                on_progress(percent)

    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'quiet': True,
        'progress_hooks': [hook],
        'logger': YTDLogger(),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print(f"YTDLP download error: {e}")
        return {"error": str(e)}

