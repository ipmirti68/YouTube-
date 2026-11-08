#!/usr/bin/env python3
"""
YouTube M3U Generator - Sultanlar Ligi / YouTube Only
TVF Voleybol TV + 【entity-TRT Spor¦canonical_name=TRT Spor】 Yildiz icin
"""
import json
import os
import re
import time
import requests
import subprocess
from datetime import datetime

def yaz(metin, renk=36):
    print(f"\033[{renk}m{metin}\033[0m")

def get_live_video_id(channel):
    """Kanalin su anki canli yayin video ID'sini bul - /live uzerinden"""
    handle = channel.get("handle", "")
    channel_id = channel.get("channel_id", "")
    
    # Denenecek URL'ler - sirayla
    urls = []
    if handle:
        urls.append(f"https://www.youtube.com/{handle}/live")
    if channel_id:
        urls.append(f"https://www.youtube.com/channel/{channel_id}/live")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'tr-TR,tr;q=0.9'
    }

    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            # /live yonlenirse URL'de v= olur
            m = re.search(r'watch\?v=([A-Za-z0-9_-]{11})', r.url)
            if m:
                return m.group(1)
            # Sayfa icinde videoId ara
            m2 = re.findall(r'"videoId":"([A-Za-z0-9_-]{11})"', r.text)
            if m2:
                return m2[0]
        except:
            continue
    return None

def get_m3u_from_video(video_id):
    """yt-dlp ile m3u8 linkini al"""
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
    print("="*70)
    yaz("🏐 Sultanlar Ligi - YouTube M3U Generator", 36)
    print("="*70)

    try:
        with open('channels.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        yaz("❌ channels.json bulunamadi!", 31)
        return

    channels = [c for c in data['channels'] if c.get('enabled', True)]
    os.makedirs('m3u_files', exist_ok=True)
    results = []

    for i, ch in enumerate(channels, 1):
        name = ch['name']
        print(f"\n[{i}/{len(channels)}] 📺 {name}")

        yaz("   🔍 Canli yayin araniyor...", 36)
        video_id = get_live_video_id(ch)

        if not video_id:
            yaz("   ❌ Su an canli yayin YOK - Mac saati degil", 31)
            results.append({'name': name, 'status': 'failed'})
            continue

        yaz(f"   ✅ Canli bulundu: https://youtu.be/{video_id}", 32)
        m3u_url = get_m3u_from_video(video_id)

        if m3u_url:
            content = []
            content.append('#EXTM3U')
            content.append(f'#EXTINF:-1 tvg-logo="https://img.youtube.com/vi/{video_id}/hqdefault.jpg" tvg-name="{name}",🔴 {name} CANLI - Sultanlar Ligi')
            content.append(m3u_url)
            
            filename = f"m3u_files/{safe_filename(name)}.m3u"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            
            yaz(f"   ✅ M3U olustu: {filename}", 32)
            results.append({'name': name, 'status': 'success', 'm3u_url': m3u_url, 'video_id': video_id})
        else:
            yaz("   ❌ m3u alinamadi - yt-dlp guncelle: pip install -U yt-dlp", 31)
            results.append({'name': name, 'status': 'failed'})
        
        time.sleep(2)

    # Toplu liste
    content = ['#EXTM3U', '#PLAYLIST:Sultanlar Ligi YouTube']
    for r in results:
        if r['status'] == 'success':
            content.append(f'#EXTINF:-1,🔴 {r["name"]}')
            content.append(r['m3u_url'])
    with open('m3u_files/all_channels.m3u', 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))
    
    print("\n" + "="*70)
    yaz(f"✅ Bittt. Toplam basarili: {len([r for r in results if r['status']=='success'])} / {len(channels)}", 32)
    yaz("📺 Gunes Tv'ye ekleyecegin dosya: m3u_files/all_channels.m3u", 36)

if __name__ == "__main__":
    main()  content.append('')
    
    with open('m3u_files/all_channels.m3u', 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))
    
    renkli_yaz("✅ Master playlist yaradıldı: m3u_files/all_channels.m3u", 32)

if __name__ == "__main__":
    main()
