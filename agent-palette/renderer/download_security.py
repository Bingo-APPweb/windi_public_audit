import hmac, hashlib, time, threading, os
from pathlib import Path
from datetime import datetime

SECRET_KEY = os.environ.get("WINDI_DOWNLOAD_SECRET", "windi-dragon-2026")

def generate_signed_url(filename, base="/api/dragon/download", ttl=15):
    expires = int(time.time()) + (ttl * 60)
    token = hmac.new(SECRET_KEY.encode(), f"{filename}:{expires}".encode(), hashlib.sha256).hexdigest()[:32]
    return {
        "download_url": f"{base}/{filename}?token={token}&expires={expires}",
        "expires_at": datetime.utcfromtimestamp(expires).isoformat() + "Z",
        "ttl_minutes": ttl
    }

def verify_token(filename, token, expires):
    if int(time.time()) > expires:
        return False, "Link expired. Please regenerate."
    expected = hmac.new(SECRET_KEY.encode(), f"{filename}:{expires}".encode(), hashlib.sha256).hexdigest()[:32]
    return (True, None) if hmac.compare_digest(token, expected) else (False, "Invalid token.")

def cleanup_old(output_dir, max_age=30):
    cutoff = time.time() - (max_age * 60)
    for f in Path(output_dir).iterdir():
        if f.is_file() and f.stat().st_mtime < cutoff:
            f.unlink()

_running = False
def start_cleanup(output_dir):
    global _running
    if _running:
        return
    _running = True
    def loop():
        while _running:
            try:
                cleanup_old(output_dir)
            except:
                pass
            time.sleep(600)
    threading.Thread(target=loop, daemon=True).start()
