import base64
import os
import re
import requests
import urllib3
import sys
import subprocess
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ENCRYPTED_URL = os.environ.get('ENCRYPTED_PLAYLIST_URL')

def create_umittube_folder():
    if not os.path.exists("Umittube"):
        os.makedirs("Umittube")

def decrypt_url():
    return base64.b64decode(ENCRYPTED_URL).decode("utf-8")

def fetch_playlist(url):
    r = requests.get(url, verify=False, timeout=30)
    r.raise_for_status()
    return r.text

def parse_playlist(content):
    lines = content.strip().split("\n")
    channels = []
    for i in range(len(lines)):
        if lines[i].startswith("#EXTINF"):
            m = re.search(r",(.+)$", lines[i])
            if m and i+1 < len(lines) and not lines[i+1].startswith("#"):
                channels.append((m.group(1).strip(), lines[i+1].strip()))
    return channels

def get_youtube_link(video_id):
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        result = subprocess.run(["yt-dlp", "-g", "-f", "best[ext=m3u8]/best", url], capture_output=True, text=True, timeout=60)
        link = result.stdout.strip().split("\n")[0]
        if link.startswith("http"):
            return link
    except Exception as e:
        print(f"YouTube hatasi {video_id}: {e}")
    return None

def load_custom_youtube():
    custom = []
    try:
        with open("youtube-listesi.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(",")
                if len(parts) >= 2:
                    name = parts[0].strip()
                    video = parts[1].strip()
                    if "v=" in video:
                        video = video.split("v=")[1].split("&")[0]
                    custom.append((name, video))
    except FileNotFoundError:
        print("youtube-listesi.txt bulunamadi")
    return custom

def save_channel_as_m3u8(channel_name, stream_url):
    safe_name = "".join(c for c in channel_name if c.isalnum() or c in ".-_").rstrip()
    safe_name = safe_name.replace('ı','i').replace('ğ','g').replace('ü','u').replace('ş','s').replace('ö','o').replace('ç','c')
    safe_name = safe_name.replace('İ','I').replace('Ğ','G').replace('Ü','U').replace('Ş','S').replace('Ö','O').replace('Ç','C')
    filename = f"Umittube/{safe_name}.m3u8"
    content = f"#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720\n{stream_url}\n"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved: {filename}")

def create_master_playlist(channels):
    master = ["#EXTM3U", "# Playlist: Umittube", f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", f"# Total channels: {len(channels)}", ""]
    for name, url in channels:
        master.append(f"#EXTINF:-1 tvg-logo=\"\" group-title=\"Umittube\",{name}")
        master.append(url)
        master.append("")
    with open("Umittube/umittube.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(master))
    github = ["#EXTM3U"]
    for name, url in channels:
        github.append(f"#EXTINF:-1,{name}")
        github.append(url)
    with open("Umittube/umittube_github.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(github))

def main():
    try:
        create_umittube_folder()
        playlist_url = decrypt_url()
        print(f"Fetching playlist from: {playlist_url[:50]}...")
        channels = parse_playlist(fetch_playlist(playlist_url))
        print(f"Found {len(channels)} channels from mywire")
        # Senin YouTube listeni ekle
        for name, vid in load_custom_youtube():
            link = get_youtube_link(vid)
            if link:
                channels.append((name, link))
                print(f"Added YouTube: {name}")
        for name, url in channels:
            save_channel_as_m3u8(name, url)
        create_master_playlist(channels)
        print(f"Done: {len(channels)} channels")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
