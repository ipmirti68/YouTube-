import json
import os
import re
import time
import requests
import subprocess

def build_base_cmd():
    # PO_TOKEN / VISITOR_DATA varsa 【entity-GitHub¦canonical_name=GitHub】 Secrets'ten al
    # Secrets isimleri: YT_PO_TOKEN , YT_VISITOR_DATA
    cmd = ['yt-dlp', '--no-warnings', '--no-playlist']

    po_token = os.environ.get('YT_PO_TOKEN', '').strip()
    visitor = os.environ.get('YT_VISITOR_DATA', '').strip()

    # En stabil istemciler: android -> ios -> tv_embedded
    # web'i en sona bile koyma, bot kontrolü direkt oradan patlatıyor
    clients = 'android,ios,tv_embedded'

    args = f'youtube:player_client={clients}'
    args += ';player_skip=webpage,configs'

    if po_token:
        args += f';po_token={po_token}'
    if visitor:
        args += f';visitor_data={visitor}'

    cmd += ['--extractor-args', args]
    return cmd

def get_live(channel):
    h = channel.get("handle", "")
    cid = channel.get("channel_id", "")
    urls = []
    if h:
        urls.append(f"https://www.youtube.com/{h}/live")
    if cid:
        urls.append(f"https://www.youtube.com/channel/{cid}/live")

    for url in urls:
        try:
            cmd = build_base_cmd() + ['--get-id', url]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
            v = r.stdout.strip().split('\n')[0] if r.stdout.strip() else ""
            if len(v) == 11:
                return v
            else:
                # Hata logda görünsün diye
                print("Live Hata:", r.stderr[:300])
        except Exception as e:
            print(e)
            continue
    return None

def get_latest(channel):
    cid = channel.get("channel_id", "")
    if not cid:
        return None
    try:
        u = f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
        r = requests.get(u, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        m = re.findall(r"<yt:videoId>([A-Za-z0-9_-]{11})</yt:videoId>", r.text)
        if m:
            return m[0]
    except Exception:
        pass
    return None

def get_m3u(vid):
    vu = f"https://www.youtube.com/watch?v={vid}"
    denemeler = [
        'best[height<=720]/best',
        'best',
        'best[ext=mp4]/best',
    ]
    for fmt in denemeler:
        cmd = build_base_cmd() + ['-g', '-f', fmt, vu]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
            s = r.stdout.strip()
            print("Deneme:")
            print(fmt)
            print("Sonuc:")
            print(s[:100])
           
