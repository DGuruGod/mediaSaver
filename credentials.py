import os

CRED_FILE = "credentials.txt"

def save_instagram_credentials(username: str, password: str):
    with open(CRED_FILE, "w") as f:
        f.write(f"{username}\n{password}")

def load_instagram_credentials():
    if not os.path.exists(CRED_FILE):
        return None, None
    with open(CRED_FILE, "r") as f:
        lines = f.read().splitlines()
        if len(lines) >= 2:
            return lines[0], lines[1]
    return None, None

def credentials_exist():
    return os.path.exists(CRED_FILE)
