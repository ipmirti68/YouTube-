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
