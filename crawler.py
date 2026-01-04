import requests
import time
import os

BASE_INDEX = "https://index.bettercallshiv.workers.dev"
ROOT_PATH = "/"
VIDEO_EXT = (".mp4", ".mkv", ".avi", ".mov", ".webm")

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "Accept": "application/json",
})


def list_folder(path, page_token=None, page_index=0):
    if not path.endswith("/"):
        path += "/"
    url = f"{BASE_INDEX}/0:{path}"
    payload = {
        "page_token": page_token,
        "page_index": page_index
    }
    r = session.post(url, json=payload, timeout=20)
    r.raise_for_status()
    return r.json()


def crawl(path, depth=0, max_depth=20):
    if depth > max_depth:
        return []
    videos = []
    page_token = None
    page_index = 0
    while True:
        data = list_folder(path, page_token, page_index)
        files = data.get("data", {}).get("files", [])
        for f in files:
            name = f.get("name")
            mime = f.get("mimeType")
            if not name:
                continue
            if mime == "application/vnd.google-apps.folder":
                sub_path = f"{path.rstrip('/')}/{name}"
                time.sleep(0.2)
                videos.extend(crawl(sub_path, depth + 1, max_depth))
            elif name.lower().endswith(VIDEO_EXT):
                video_url = f"{BASE_INDEX}/0:{path.rstrip('/')}/{name}"
                videos.append({
                    "name": name,
                    "url": video_url
                })
        page_token = data.get("data", {}).get("nextPageToken")
        if not page_token:
            break
        page_index += 1
    return videos


def write_m3u(folder_name, videos):
    filename = f"{folder_name}.m3u"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for v in videos:
            f.write(f"#EXTINF:-1,{v['name']}\n{v['url']}\n")
    print(f"Wrote {filename} ({len(videos)} videos)")


def main():
    data = list_folder(ROOT_PATH)
    files = data.get("data", {}).get("files", [])
    for f in files:
        name = f.get("name")
        mime = f.get("mimeType")
        if mime != "application/vnd.google-apps.folder":
            continue
        folder_path = f"/{name}"
        print(f"Scraping folder: {folder_path}")
        videos = crawl(folder_path)
        if videos:
            write_m3u(name, videos)
        else:
            print(f"Skipped {name} (no videos found)")

if __name__ == "__main__":
    main()
