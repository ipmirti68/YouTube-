import json
import os
import re
import time
import requests
import subprocess

def build_base_cmd():
    cmd = ['yt-dlp', '--no-warnings', '--no-playlist']
    po_token = os.environ.get('YT_PO_TOKEN', '').strip()
    visitor = os.environ.get('YT_VISITOR_DATA', '').strip()
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
            out = r.stdout.strip()
            v = out.split('\n')[0] if out else ""
            if len(v) == 11:
                return v
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
            print("Hata:")
            print(r.stderr[:500])
            if s.startswith("http"):
                return s.split('\n')[0]
        except Exception as e:
            print(e)
            continue
        time.sleep(1)
    return None

def safe(name):
    n = name.lower()
    n = re.sub(r'[^a-z0-9]', '_', n)
    n = re.sub(r'_+', '_', n)
    return n.strip('_')

def main():
    print("Basliyor")
    try:
        with open('channels.json') as f:
            data = json.load(f)
    except Exception:
        print("channels.json yok!")
        return
    chans = [c for c in data['channels'] if c.get('enabled')]
    os.makedirs('m3u_files', exist_ok=True)
    results = []
    for ch in chans:
        name = ch['name']
        print(name)
        vid = get_live(ch)
        live = True
        if not vid:
            print("Canli YOK")
            vid = get_latest(ch)
            live = False
            if not vid:
                print("Eski de YOK")
                results.append({'name': name, 'status': 'failed'})
                continue
        print("Canli bulundu" if live else "Eski bulundu")
        print(vid)
        url = get_m3u(vid)
        if url:
            et = "CANLI" if live else "TEKRAR"
            c = ['#EXTM3U', f"#EXTINF:-1,{et} {name}", url]
            fn = f"m3u_files/{safe(name)}.m3u"
            with open(fn, 'w') as f:
                f.write('\n'.join(c))
            print("Oldu")
            print(fn)
            results.append({'name': name, 'status': 'success', 'm3u_url': url, 'is_live': live})
        else:
            print("m3u YOK")
            results.append({'name': name, 'status': 'failed'})
        time.sleep(2)
    c = ['#EXTM3U', '#PLAYLIST:Sultanlar']
    for r in results:
        if r['status'] == 'success':
            et = "CANLI" if r.get('is_live') else "TEKRAR"
            c.append(f"#EXTINF:-1,{et} {r['name']}")
            c.append(r['m3u_url'])
    with open('m3u_files/all_channels.m3u', 'w') as f:
        f.write('\n'.join(c))
    print("Bitti")

if __name__ == "__main__":
    main()
