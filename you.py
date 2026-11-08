import json
import os
import re
import time
import requests
import subprocess

def get_live(channel):
    h = channel.get("handle", "")
    cid = channel.get("channel_id", "")
    urls = []
    if h:
        u = "https://www.youtube.com/"
        u = u + h
        u = u + "/live"
        urls.append(u)
    if cid:
        u = "https://www.youtube.com/"
        u = u + "channel/"
        u = u + cid
        u = u + "/live"
        urls.append(u)
    for url in urls:
        try:
            r = subprocess.run(
                ['yt-dlp', '--get-id', url],
                capture_output=True,
                text=True,
                timeout=30)
            v = r.stdout.strip()
            v = v.split('\n')[0]
            if len(v) == 11:
                return v
        except Exception:
            continue
    return None

def get_latest(channel):
    cid = channel.get("channel_id", "")
    if not cid:
        return None
    try:
        u = "https://www.youtube.com/"
        u = u + "feeds/videos.xml"
        u = u + "?channel_id="
        u = u + cid
        r = requests.get(u, timeout=15)
        p = r"<yt:videoId>"
        p = p + r"([A-Za-z0-9_-]{11})"
        p = p + r"</yt:videoId>"
        m = re.findall(p, r.text)
        if m:
            return m[0]
    except Exception:
        pass
    return None

def get_m3u(vid):
    vu = "https://www.youtube.com/"
    vu = vu + "watch?v="
    vu = vu + vid
    cmd = []
    cmd.append('yt-dlp')
    cmd.append('-g')
    cmd.append('-f')
    cmd.append('best[height<=720]')
    cmd.append('--no-warnings')
    cmd.append(vu)
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30)
        s = r.stdout.strip()
        if s.startswith("http"):
            return s.split('\n')[0]
    except Exception as e:
        print(e)
    return None

def safe(name):
    n = name.lower()
    n = re.sub(r'[^a-z0-9]', '_', n)
    n = re.sub(r'_+', '_', n)
    return n.strip('_')

def main():
    print("Basliyor")
    try:
        f = open('channels.json')
        data = json.load(f)
        f.close()
    except Exception:
        print("channels.json yok!")
        return
    chans = data['channels']
    chans = [c for c in chans]
    chans = [c for c in chans if c.get('enabled')]
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
                d = {}
                d['name'] = name
                d['status'] = 'failed'
                results.append(d)
                continue
        if live:
            print("Canli bulundu")
            print(vid)
        else:
            print("Eski bulundu")
            print(vid)
        url = get_m3u(vid)
        if url:
            if live:
                et = "CANLI"
            else:
                et = "TEKRAR"
            c = []
            c.append('#EXTM3U')
            s = "#EXTINF:-1,"
            s = s + et
            s = s + " "
            s = s + name
            c.append(s)
            c.append(url)
            fn = "m3u_files/"
            fn = fn + safe(name)
            fn = fn + ".m3u"
            f = open(fn, 'w')
            f.write('\n'.join(c))
            f.close()
            print("Oldu")
            print(fn)
            d = {}
            d['name'] = name
            d['status'] = 'success'
            d['m3u_url'] = url
            d['is_live'] = live
            results.append(d)
        else:
            print("m3u YOK")
            d = {}
            d['name'] = name
            d['status'] = 'failed'
            results.append(d)
        time.sleep(2)
    c = []
    c.append('#EXTM3U')
    c.append('#PLAYLIST:Sultanlar')
    for r in results:
        if r['status'] == 'success':
            if r.get('is_live'):
                et = "CANLI"
            else:
                et = "TEKRAR"
            s = "#EXTINF:-1,"
            s = s + et
            s = s + " "
            s = s + r['name']
            c.append(s)
            c.append(r['m3u_url'])
    f = open('m3u_files/all_channels.m3u', 'w')
    f.write('\n'.join(c))
    f.close()
    print("Bitti")

if __name__ == "__main__":
    main()
