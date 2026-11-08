#!/usr/bin/env python3
import json
import os
import re
import time
import requests
import subprocess

def yaz(metin):
    print(metin)

def get_live_video_id(channel):
    handle = channel.get("handle", "")
    channel_id = channel.get("channel_id", "")
    urls = []
    if handle:
        urls.append("https://www.youtube.com/" + handle + "/live")
    if channel_id:
        urls.append("https://www.youtube.com/channel/" + channel_id + "/live")
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
    channel_id = channel.get("channel_id", "")
    if not channel_id:
        return None
    try:
        url = "https://www.youtube.com/feeds/videos.xml?channel_id=" + channel_id
        r = requests.get(url, timeout=15)
        m = re.findall(r"<yt:videoId>([A-Za-z0-9_-]{11})</yt:videoId>", r.text)
        if m:
            return m[0]
    except Exception:
        pass
    return None

def get_m3u_from_video(video_id):
    video_url = "https://www.youtube.com/watch?v=" + video_id
    cmd = ['yt-dlp', '-g', '-f', 'best[height<=720][ext=mp4]/best[height<=720]/best', '--no-warnings', '--extractor-args', 'youtube:player_client=android,web', video_url]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip().startswith("http"):
            return result.stdout.strip().split('\n')[0]
    except Exception as e:
        print(e)
    return None

def safe_filename(name):
    name = name.lower()
    name = re.sub(r'[^a-z0-9]', '_', name)
    return re.sub(r'_+', '_', name).strip('_')

def main():
    print("Sultanlar Ligi Basliyor")
    try:
        with open('channels.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        print("channels.json bulunamadi!")
        return
    channels = [c for c in data['channels'] if c.get('enabled', True)]
    os.makedirs('m3u_files', exist_ok=True)
    results = []
    for ch in channels:
        name = ch['name']
        print(name)
        video_id = get_live_video_id(ch)
        is_live = True
        if not video_id:
            print("Canli YOK, eski video deneniyor...")
            video_id = get_latest_video_id(ch)
            is_live = False
            if not video_id:
                print("Eski video da bulunamadi")
                results.append({'name': name, 'status': 'failed'})
                continue
        if is_live:
            print("Canli bulundu: " + video_id)
        else:
            print("Eski video bulundu: " + video_id)
        m3u_url = get_m3u_from_video(video_id)
        if m3u_url:
            if is_live:
                etiket = "CANLI"
            else:
                etiket = "TEKRAR"
            content = []
            content.append('#EXTM3U')
            content.append('#EXTINF:-1,' + etiket + ' ' + name)
            content.append(m3u_url)
            filename = "m3u_files/" + safe_filename(name) + ".m3u"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            print("M3U olustu: " + filename)
            results.append({'name': name, 'status': 'success', 'm3u_url': m3u_url, 'is_live': is_live})
        else:
            print("m3u alinamadi")
            results.append({'name': name, 'status': 'failed'})
        time.sleep(2)
    content = ['#EXTM3U', '#PLAYLIST:Sultanlar Ligi YouTube']
    for r in results:
        if r['status'] == 'success':
            if r.get('is_live'):
                etiket = "CANLI"
            else:
                etiket = "TEKRAR"
            content.append("#EXTINF:-1," + etiket
