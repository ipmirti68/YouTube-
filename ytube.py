import subprocess
import json

# KENDİ 7/24 YOUTUBE KANALLARIN BURAYA
CUSTOM_YOUTUBE = [
    {"name": "7-24 Yayin", "id": "NGsjOrzwjZk"},
    # İstersen buraya başka ekleyebilirsin:
    # {"name": "Cicek Taksi 7-24", "id": "XXXXXXX"},
]

def get_youtube_link(video_id):
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        # m3u8 olan en iyi linki al
        result = subprocess.run(
            ["yt-dlp", "-g", "-f", "best[ext=m3u8]/best", url],
            capture_output=True, text=True, timeout=30
        )
        link = result.stdout.strip().split("\n")[0]
        if link.startswith("http"):
            return link
    except Exception as e:
        print(f"YouTube hatası {video_id}: {e}")
    return None
