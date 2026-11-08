# Yazar: Ahmet Dogan
import json
import os
import re
import time
import requests
import subprocess

def write_cookies():
    # GitHub Secrets: YT_COOKIES icine cookies.txt icerigini koyarsan kullanilir
    c = os.environ.get('YT_COOKIES', '').strip()
    if not c:
        return None
    try:
        # Secrets'e base64 veya duz yazi olarak koyabilirsin
        # base64 ise decode et, degilse oldugu gibi yaz
        import base64
        try:
            dec = base64.b64decode(c).decode('utf-8', errors='ignore')
            if 'Netscape' in dec or 'youtube' in dec.lower():
                c = dec
        except Exception:
            pass
        with open('cookies.txt', 'w', encoding='utf-8') as f:
            f.write(c)
        return 'cookies.txt'
    except Exception as e:
        print("Cookie yazma hatasi:", e)
        return None

def build_base_cmd(extra_clients=None):
    cmd = ['yt-dlp', '--no-warnings', '--no-playlist']
    # cookies varsa ekle - bu bot kontrolunu en guclu asan yontem
    cf = write_cookies()
    if cf:
        cmd += ['--cookies', cf]
    # NOT: --impersonate kullanma! curl_cffi kurulu degilse yt-dlp baslamadan coker
    # Onceki hatanin sebebi buydu: Traceback ... with YoutubeDL
    po_token = os.environ.get('YT_PO_TOKEN', '').strip()
    visitor = os.environ.get('YT_VISITOR_DATA', '').strip()
    clients = extra_clients if extra_clients else 'android,ios,tv_embedded'
    args = 'youtube:player_client=' + clients
    args += ';player_skip=webpage,configs'
    if po_token:
        args += ';po_token=' + po_token
    if visitor:
        args += ';visitor_data=' + visitor
    cmd += ['--extractor-args', args]
    return cmd

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
            cmd = build_base_cmd() + ['--get-id', url]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
            v = r.stdout.strip()
            v = v.split('\n')[0] if v else ""
            if len(v) == 11:
                return v
            print("Live Hata:")
            print(r.stderr[:300])
        except Exception:
            continue
    return None

def get_latest(channel):
    # 1. Once channel_id ile RSS dene (en hizli)
    cid = channel.get("channel_id", "")
    if cid:
        try:
            u = "https://www.youtube.com/"
            u = u + "feeds/videos.xml"
            u = u + "?channel_id="
            u = u + cid
            r = requests.get(u, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
            p = r"<yt:videoId>"
            p = p + r"([A-Za-z0-9_-]{11})"
            p = p + r"</yt:videoId>"
            m = re.findall(p, r.text)
            if m:
                return m[0]
        except Exception:
            pass
    # 2. channel_id yoksa / bos ise handle ile yt-dlp'den son videoyu al (TRT icin bu lazim)
    h = channel.get("handle", "")
    if h:
        try:
            url = "https://www.youtube.com/" + h + "/videos"
            cmd = build_base_cmd() + ['--flat-playlist', '--playlist-end', '1', '--get-id', url]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
            v = r.stdout.strip()
            v = v.split('\n')[0] if v else ""
            if len(v) == 11:
                return v
            print("Latest handle hatasi:", r.stderr[:300])
        except Exception as e:
            print(e)
    return None

def get_m3u(vid):
    vu = "https://www.youtube.com/"
    vu = vu + "watch?v="
    vu = vu + vid
    # 1. Tur: android/ios (canli icin)
    # 2. Tur: web + android (eski video / bitmis canli icin, PO_TOKEN + cookies ile calisir)
    denemeler = []
    denemeler.append(('android,ios,tv_embedded', 'best[height<=720]/best'))
    denemeler.append(('android,ios,tv_embedded', 'best'))
    denemeler.append(('web,android', 'best[height<=720]/best'))
    denemeler.append(('web,android', 'best'))
    denemeler.append(('web,android', 'best[ext=mp4]/best'))
    for clients, fmt in denemeler:
        cmd = build_base_cmd(clients) + ['-g', '-f', fmt, vu]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
            s = r.stdout.strip()
            print("Deneme:")
            print(clients + " | " + fmt)
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
    # TESHIS: Secrets geliyor mu?
    ck = os.environ.get('YT_COOKIES', '').strip()
    pt = os.environ.get('YT_PO_TOKEN', '').strip()
    if ck:
        print("COOKIE: VAR, uzunluk=" + str(len(ck)))
    else:
        print("COOKIE: YOK! Secrets'e YT_COOKIES eklenmemis veya workflow env'e eklenmemis")
    if pt:
        print("PO_TOKEN: VAR")
    else:
        print("PO_TOKEN: YOK")
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
        # TRT icin direkt TRT linki varsa YouTube botuna hic bulasma
        direct = ch.get("direct_url", "")
        if direct:
            print("Direkt link kullaniliyor, YouTube atlaniyor")
            print(direct)
            c = []
            c.append('#EXTM3U')
            c.append("#EXTINF:-1,CANLI " + name)
            c.append(direct)
            fn = "m3u_files/" + safe(name) + ".m3u"
            f = open(fn, 'w')
            f.write('\n'.join(c))
            f.close()
            d = {}
            d['name'] = name
            d['status'] = 'success'
            d['m3u_url'] = direct
            d['is_live'] = True
            results.append(d)
            continue
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
