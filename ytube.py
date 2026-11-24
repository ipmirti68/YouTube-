import requests
import sys
import subprocess
from datetime import datetime

def create_umittube_folder():
    import os
    if not os.path.exists("tube"):
        os.makedirs("tube")

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

def load_liste():
    custom = []
    # Senin liste.txt dosyan
    url = "https://raw.githubusercontent.com/ipmirti68/YouTube-/refs/heads/main/liste.txt"
    print(f"liste.txt okunuyor: {url}")
    r = requests.get(url, timeout=20)
    print(f"liste.txt geldi: {r.text[:200]}")
    for line in r.text.splitlines():
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
            print(f"Listeden bulundu: {name} - {video}")
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
        master.append(f"#EXTINF:-1 tvg-logo=\"\" group-title=\"tube\",{name}")
        master.append(url)
        master.append("")
    with open("tube/tube.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(master))

def main():
    try:
        create_umittube_folder()
        channels = []
        for name, vid in load_liste():
            link = get_youtube_link(vid)
            if link:
                channels.append((name, link))
                print(f"Added: {name}")
            else:
                print(f"Link bulunamadi: {name}")
        for name, url in channels:
            save_channel_as_m3u8(name, url)
        create_master_playlist(channels)
        print(f"Done: {len(channels)} channels")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
