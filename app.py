from flask import Flask, render_template, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

# =========================
# DOWNLOAD FOLDER
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_PATH = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_PATH, exist_ok=True)


# =========================
# PARSE (VIDEO / PLAYLIST / CHANNEL FULL)
# =========================
@app.route("/parse", methods=["POST"])
def parse():

    url = request.json.get("url")

    try:
        ydl_opts = {
            "quiet": True,
            "extract_flat": True,
            "skip_download": True,
            "playlistend": None
        }

        videos = []

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if not info:
                return jsonify({"videos": []})

            entries = info.get("entries", [])

            for e in entries:
                if not e:
                    continue

                video_id = e.get("id") or e.get("url")

                videos.append({
                    "title": e.get("title", "Unknown"),
                    "url": f"https://www.youtube.com/watch?v={video_id}"
                })

        return jsonify({"videos": videos})

    except Exception as e:
        return jsonify({"error": str(e)})


# =========================
# DOWNLOAD ALL MP4 (MERGED)
# =========================
def download_all(urls):

    success = []
    failed = []

    ydl_opts = {
        "format": "bv*+ba/best",
        "merge_output_format": "mp4",
        "outtmpl": os.path.join(DOWNLOAD_PATH, "%(title)s.%(ext)s"),

        "quiet": True,
        "ignoreerrors": True,
        "noplaylist": False
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        for url in urls:

            try:
                print(f"⬇️ Downloading: {url}")

                info = ydl.extract_info(url, download=True)

                if not info:
                    failed.append(url)
                    continue

                print(f"✅ DONE: {info.get('title')}")
                success.append(info.get("title"))

            except Exception as e:
                print(f"❌ FAIL: {url} -> {e}")
                failed.append(url)

    return success, failed


# =========================
# API DOWNLOAD
# =========================
@app.route("/download", methods=["POST"])
def download():

    urls = request.json.get("urls", [])

    try:
        success, failed = download_all(urls)

        return jsonify({
            "message": "Download finished",
            "success": success,
            "failed": failed,
            "folder": DOWNLOAD_PATH
        })

    except Exception as e:
        return jsonify({"error": str(e)})


# =========================
@app.route("/")
def index():
    return render_template("index.html")


# =========================
if __name__ == "__main__":
    app.run(debug=True)