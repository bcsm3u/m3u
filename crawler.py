import requests
import time
import re
import json

BASE_INDEX = "https://index.bettercallshiv.workers.dev"
ROOT_PATH = "/"
VIDEO_EXT = (".mp4", ".mkv", ".avi", ".mov", ".webm")

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*",
})


def get_drives():
    r = session.get(BASE_INDEX, timeout=20, allow_redirects=True)
    r.raise_for_status()
    match = re.search(r'window\.drive_names\s*=\s*JSON\.parse\(\'(.+?)\'\)', r.text)
    if match:
        json_str = match.group(1)
        drives = json.loads(json_str)
        return drives
    return []


def list_folder(drive, path, page_token=None, page_index=0):
    if not path.endswith("/"):
        path += "/"
    url = f"{BASE_INDEX}/{drive}:{path}"
    payload = {
        "page_token": page_token,
        "page_index": page_index
    }
    r = session.post(url, json=payload, timeout=20)
    r.raise_for_status()
    return r.json()


def crawl(drive, path, depth=0, max_depth=20):
    if depth > max_depth:
        return []
    videos = []
    page_token = None
    page_index = 0
    while True:
        data = list_folder(drive, path, page_token, page_index)
        files = data.get("data", {}).get("files", [])
        for f in files:
            name = f.get("name")
            mime = f.get("mimeType")
            if not name:
                continue
            if mime == "application/vnd.google-apps.folder":
                sub = f"{path.rstrip('/')}/{name}"
                time.sleep(0.2)
                videos.extend(crawl(drive, sub, depth + 1))
            elif name.lower().endswith(VIDEO_EXT):
                videos.append({
                    "name": name,
                    "url": f"{BASE_INDEX}/{drive}:{path.rstrip('/')}/{name}"
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
    drives = get_drives()
    print(f"Detected drives: {drives}")
    for drive in drives:
        data = list_folder(drive, ROOT_PATH)
        files = data.get("data", {}).get("files", [])
        for f in files:
            if f.get("mimeType") != "application/vnd.google-apps.folder":
                continue
            folder = f.get("name")
            folder_path = f"/{folder}"
            print(f"Scraping {drive}:{folder_path}")
            videos = crawl(drive, folder_path)
            if videos:
                write_m3u(folder, videos)
            else:
                print(f"Skipped {folder} (no videos)")


if __name__ == "__main__":
    main()
