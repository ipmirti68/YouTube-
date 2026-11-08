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
    search = channel.get("search", "")
    search = search.lower()
    if cid:
        try:
            u = "https://www.youtube.com/"
            u = u + "feeds/videos.xml"
            u = u + "?channel_id="
            u = u + cid
            r = requests.get(u, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
            # entry entry gez: baslik + videoId birlikte al
            entries = re.findall(r"<entry>(.*?)</entry>", r.text, re.DOTALL)
            for e in entries:
                vid_m = re.search(r"<yt:videoId>([A-Za-z0-9_-]{11})</yt:videoId>", e)
                tit_m = re.search(r"<title>(.*?)</title>", e, re.DOTALL)
                if not vid_m:
                    continue
                vid = vid_m.group(1)
                tit = tit_m.group(1).lower() if tit_m else ""
                # search varsa sadece o takim gecen videoyu al
                if search:
                    if search in tit:
                        print("Kuzeyboru maci bulundu: " + tit)
                        return vid
                    else:
                        continue
                return vid
            # search varsa ama RSS'de bulunamadiysa alta dus, yt-dlp search dene
            if search:
                print("RSS'de Kuzeyboru bulunamadi, arama deneniyor")
            else:
                return None
        except Exception:
            pass
    # search icin yt-dlp ile YouTube aramasi: son Kuzeyboru maci
    if search:
        try:
            q = "ytsearch5:" + search + " mac"
            cmd = build_base_cmd() + ['--flat-playlist', '--get-id', '--get-title', q]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=50)
            lines = r.stdout.strip().split('\n')
            # get-id + get-title cift cift gelir
            for i in range(0, len(lines)-1, 2):
                vid = lines[i].strip()
                tit = lines[i+1].lower() if i+1 < len(lines) else ""
                if len(vid) == 11 and search in tit:
                    print("Aramada bulundu: " + tit)
                    return vid
        except Exception as e:
            print(e)
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
    # Yedek yol: cookiesiz Invidious ile dene (yt-dlp bot yediyse)
    print("Invidious yedegi deneniyor...")
    inv = get_m3u_invidious(vid)
    if inv:
        return inv
    return None

def get_m3u_invidious(vid):
    # YouTube videosunu Invidious API uzerinden alir, giris istemez
    # Bir instance bozulursa digerini dener
    instances = []
    instances.append('https://inv.nadeko.net')
    instances.append('https://invidious.0011.lt')
    instances.append('https://inv.us.projectsegfau.lt')
    instances.append('https://iv.datura.network')
    for base in instances:
        try:
            u = base + '/api/v1/videos/' + vid
            r = requests.get(u, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
            if r.status_code != 200:
                print("Invidious " + base + " kod:" + str(r.status_code))
                continue
            data = r.json()
            # 1. HLS varsa en iyisi o
            hls = data.get('hlsUrl', '')
            if hls and hls.startswith('http'):
                print("Invidious HLS bulundu: " + base)
                return hls
            # 2. Yoksa adaptiveFormats icinden mp4 sec
            fmts = data.get('adaptiveFormats', [])
            best = None
            best_h = -1
            for f in fmts:
                if f.get('type', '').startswith('video/mp4'):
                    h = f.get('height', 0) or 0
                    if h <= 720 and h > best_h:
                        best = f.get('url', '')
                        best_h = h
            if best:
                print("Invidious MP4 bulundu: " + base)
                return best
            # 3. formatStreams
            fmts2 = data.get('formatStreams', [])
            for f in fmts2:
                u2 = f.get('url', '')
                if u2.startswith('http'):
                    print("Invidious format bulundu: " + base)
                    return u2
        except Exception as e:
            print("Invidious hata " + base + ": " + str(e)[:200])
            continue
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
url'])
    f = open('m3u_files/all_channels.m3u', 'w')
    f.write('\n'.join(c))
    f.close()
    print("Bitti")

if __name__ == "__main__":
    main()
