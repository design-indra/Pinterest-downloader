from flask import Flask, render_template, request, redirect, Response
import requests
import os
import time

template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)

RAPIDAPI_KEY = "f30b4baaecmsh7d04f39e3f19019p15339bjsnad800cd8c0d2"
RAPIDAPI_HOST = "pinterest-downloader1.p.rapidapi.com"

def get_pinterest_data(url):
    url = url.strip()
    if "pinterest.com" not in url and "pin.it" not in url:
        return None

    print(f"Fetching Pinterest: {url}")
    try:
        r = requests.get(
            f"https://{RAPIDAPI_HOST}/pinterest",
            params={"url": url},
            headers={
                "x-rapidapi-key": RAPIDAPI_KEY,
                "x-rapidapi-host": RAPIDAPI_HOST
            },
            timeout=20
        )
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:500]}")
        data = r.json()

        # Ambil data dari berbagai struktur response
        title = data.get("title") or data.get("description", "Pinterest Media")
        video_url = None
        image_url = None
        thumbnail = None

        # Cek video
        video = data.get("video") or data.get("video_url")
        if video:
            video_url = video if isinstance(video, str) else video.get("url") or video.get("video_url")

        # Cek image
        image = data.get("image") or data.get("image_url") or data.get("images")
        if image:
            if isinstance(image, str):
                image_url = image
            elif isinstance(image, dict):
                image_url = image.get("orig", {}).get("url") or list(image.values())[-1].get("url") if image else None
            elif isinstance(image, list):
                image_url = image[0] if image else None

        thumbnail = data.get("thumbnail") or image_url

        if video_url or image_url:
            return {
                "title": title,
                "thumbnail": thumbnail,
                "video": video_url,
                "image": image_url,
                "type": "video" if video_url else "image"
            }

    except Exception as e:
        print(f"Pinterest error: {e}")
    return None

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    if request.method == "POST":
        input_url = request.form.get("url", "").strip()
        if not input_url or ("pinterest.com" not in input_url and "pin.it" not in input_url):
            error = "Masukkan link Pinterest yang valid."
        else:
            result = get_pinterest_data(input_url)
            if not result:
                error = "Gagal mengambil media. Pastikan link benar dan coba lagi."
    return render_template("index.html", result=result, error=error)

@app.route("/download")
def download():
    media_url = request.args.get("url")
    media_type = request.args.get("type", "image")
    if not media_url:
        return "URL tidak valid", 400
    try:
        r = requests.get(
            media_url,
            headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.pinterest.com/"},
            stream=True,
            timeout=25
        )
        ext = "mp4" if media_type == "video" else "jpg"
        mime = "video/mp4" if media_type == "video" else "image/jpeg"
        filename = f"PinSave_{int(time.time())}.{ext}"
        def generate():
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
        return Response(generate(), headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": mime,
        })
    except Exception as e:
        print(f"Download error: {e}")
        return redirect(media_url)

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

if __name__ == "__main__":
    app.run(debug=True)
