#!/usr/bin/env python3
"""
YouTube M3U Generator - Sultanlar Ligi / YouTube Only
Canli varsa canli, yoksa RSS ile eski video / mac tekrari getirir
"""
import json
import os
import re
import time
import requests
import subprocess

def yaz(metin, renk=36):
    print(f"\033[{renk}m{metin}\033[0m")

def get_live_video_id(channel):
    handle = channel.get("handle", "")
    channel_id = channel.get("channel_id", "")
    urls = []
    if handle:
        urls.append(f"https://www.youtube.com/{handle}/live")
    if channel_id:
        urls.append(f"https://www.youtube.com/channel/{channel_id}/live")
    for url in urls:
        try:
            r = subprocess.run(['yt-dlp', '--get-id', '--no-warnings', url], capture_output=True, text=True, timeout=30)
            vid = r.stdout.strip().split('\n')[0] if r.stdout.strip() else ""
            if len(vid) == 11:
                return vid
        except Exception:
            continue
    return None

def get_latest_video_id(channel):
    # RSS ile en son videoyu al - en saglam yol
    channel_id = channel.get("channel_id", "")
    if not channel_id:
        return None
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        r = requests.get(url, timeout=15)
        m = re.findall(r"<yt:videoId>([A-Za-z0-9_-]{11})</yt:videoId>", r.text)
        if m:
            return m[0]
    except Exception:
        pass
    return None

def get_m3u_from_video(video_id):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = [
        'yt-dlp',
        '-g',
        '-f', 'best[height<=720][ext=mp4]/best[height<=720]/best',
        '--no-warnings',
        '--extractor-args', 'youtube:player_client=android,web',
        video_url
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip().startswith("http"):
            return result.stdout.strip().split('\n')[0]
    except Exception as e:
        print(f"Hata: {e}")
    return None

def safe_filename(name):
    name = name.lower()
    name = re.sub(r'[^a-z0-9]', '_', name)
    return re.sub(r'_+', '_', name).strip('_')

def main():
    print("=" * 70)
    yaz("Sultanlar Ligi - YouTube M3U Generator", 36)
    print("=" * 70)

    try:
        with open('channels.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        yaz("channels.json bulunamadi!", 31)
        return

    channels = [c for c in data['channels'] if c.get('enabled', True)]
    os.makedirs('m3u_files', exist_ok=True)
    results = []

    for i, ch in enumerate(channels, 1):
        name = ch['name']
        print(f"\n[{i}/{len(channels)}] {name}")
        yaz("Canli yayin araniyor...", 36)
        video_id = get_live_video_id(ch)
        is_live = True

        if not video_id:
            yaz("Canli YOK, eski video / mac tekrari getiriliyor...", 33)
            video_id = get_latest_video_id(ch)
            is_live = False
            if not video_id:
                yaz("Eski video da bulunamadi", 31)
                results.append({'name': name, 'status': 'failed'})
                continue

        if is_live:
            yaz(f"Canli bulundu: https://youtu.be/{video_id}", 32)
        else:
            yaz(f"Eski video bulundu: https://youtu.be/{video_id}", 33)

        m3u_url = get_m3u_from_video(video_id)

        if m3u_url:
            etiket = "CANLI" if is_live else "TEKRAR"
            content = []
            content.append('#EXTM3U')
            content.append(f'#EXTINF:-1 tvg-logo="https://img.youtube.com/vi/{video_id}/hqdefault.jpg" tvg-name="{name}",{etiket} {name} - Sultanlar Ligi')
            content.append(m3u_url)
            filename = f"m3u_files/{safe_filename(name)}.m3u"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            yaz(f"M3U olustu: {filename}", 32)
            results.append({'name': name, 'status': 'success', 'm3u_url': m3u_url, 'video_id': video_id, 'is_live': is_live})
        else:
            yaz("m3u alinamadi", 31)
            results.append({'name': name, 'status': 'failed'})
        time.sleep(2)

    content = ['#EXTM3U', '#PLAYLIST:Sultanlar Ligi YouTube']
    for r in results:
        if r['status'] == 'success':
            etiket = "CANLI" if r
