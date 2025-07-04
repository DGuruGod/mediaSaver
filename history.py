import os, json
HFILE = "history.json"
def load_history():
    return json.load(open(HFILE)) if os.path.exists(HFILE) else []

def save_history_entry(platform, entry):
    h = load_history()
    h.append({'platform': platform, **entry, 'time': datetime.now().isoformat()})
    json.dump(h, open(HFILE,'w'), indent=2)

