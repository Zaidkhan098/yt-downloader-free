import customtkinter as ctk
import threading
import os
import re
import urllib.request
from PIL import Image
import yt_dlp
import io
import itertools
import sys
import os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

ctk.set_appearance_mode("dark")


class YTApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("YT Downloader Free")
        self.geometry("1100x750")
        self.iconbitmap(resource_path("icon.ico"))

        self.download_path = os.path.expanduser("~/Downloads")
        self.video_url = None

        self.configure(fg_color="#020617")

        self.build_ui()
        self.animate_bg()

    # ---------------- UI ----------------
    def build_ui(self):

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=30, pady=20)

        ctk.CTkLabel(top, text="▶ YT Downloader Free",
                     font=("Arial", 18, "bold"),
                     text_color="#ff0000").pack(side="left")

        self.card = ctk.CTkFrame(self, corner_radius=20, fg_color="#0f172a")
        self.card.pack(expand=True, padx=40, pady=20, fill="both")

        ctk.CTkLabel(self.card, text="Download YouTube Videos",
                     font=("Segoe UI", 32, "bold")).pack(pady=20)

        self.url_entry = ctk.CTkEntry(self.card, placeholder_text="Paste URL...", height=50)
        self.url_entry.pack(padx=100, fill="x")

        self.fetch_btn = ctk.CTkButton(self.card, text="Fetch", command=self.fetch_video)
        self.fetch_btn.pack(pady=10)

        self.thumb = ctk.CTkLabel(self.card, text="")
        self.thumb.pack(pady=10)

        self.title_label = ctk.CTkLabel(self.card, text="", wraplength=800)
        self.title_label.pack()

        self.mode = ctk.CTkComboBox(self.card, values=["MP4", "MP3"])
        self.mode.set("MP4")
        self.mode.pack(pady=5)

        self.quality = ctk.CTkComboBox(self.card, values=["Best"])
        self.quality.pack(pady=5)

        self.download_btn = ctk.CTkButton(self.card, text="Download", command=self.start_download)
        self.download_btn.pack(pady=10)

        self.progress = ctk.CTkProgressBar(self.card)
        self.progress.pack(fill="x", padx=100)
        self.progress.set(0)

        self.status = ctk.CTkLabel(self.card, text="Ready")
        self.status.pack()

    # ---------------- BG ----------------
    def animate_bg(self):
        colors = itertools.cycle(["#020617", "#0f172a", "#020617"])

        def loop():
            self.configure(fg_color=next(colors))
            self.after(1500, loop)

        loop()

    # ---------------- FETCH ----------------
    def fetch_video(self):
        url = self.url_entry.get().strip()
        self.video_url = url

        def run():
            try:
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    info = ydl.extract_info(url, download=False)

                self.title_label.configure(text=info.get("title"))

                # THUMB
                thumb_url = info.get("thumbnail")
                data = urllib.request.urlopen(thumb_url).read()
                img = Image.open(io.BytesIO(data)).resize((320, 180))
                self.thumb.configure(image=ctk.CTkImage(img, size=(320, 180)), text="")

                # QUALITIES
                formats = info.get("formats", [])
                qualities = []

                for f in formats:
                    if f.get("height"):
                        size = f.get("filesize") or 0
                        size_mb = round(size / (1024 * 1024), 1)
                        label = f"{f.get('height')}p ({size_mb} MB)"
                        qualities.append(label)

                qualities = sorted(list(set(qualities)), reverse=True)

                if qualities:
                    self.quality.configure(values=qualities)
                    self.quality.set(qualities[0])

                self.status.configure(text="Ready")

            except Exception as e:
                self.status.configure(text=str(e))

        threading.Thread(target=run, daemon=True).start()

    # ---------------- DOWNLOAD ----------------
    def start_download(self):
        threading.Thread(target=self.download, daemon=True).start()

    def download(self):
        try:
            self.status.configure(text="Downloading...")

            quality = self.quality.get().split("p")[0]

            if self.mode.get() == "MP4":
                fmt = f"bestvideo[height<={quality}]+bestaudio/best"
            else:
                fmt = "bestaudio"

            ydl_opts = {
                'format': fmt,
                'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self.hook],
                'merge_output_format': 'mp4'
            }

            if self.mode.get() == "MP3":
                ydl_opts.update({
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                })

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.video_url])

            self.status.configure(text="Download complete 🎉")

        except Exception as e:
            self.status.configure(text=str(e))

    # ---------------- PROGRESS ----------------
    def hook(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 1)
            downloaded = d.get('downloaded_bytes', 0)
            p = downloaded / total
            self.progress.set(p)

            speed = d.get('speed', 0)
            eta = d.get('eta', 0)

            speed_kb = round(speed / 1024, 1) if speed else 0

            self.status.configure(
                text=f"{speed_kb} KB/s | ETA: {eta}s"
            )


if __name__ == "__main__":
    app = YTApp()
    app.mainloop()