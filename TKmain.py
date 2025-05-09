import tkinter as tk
from tkinter import messagebox, filedialog
import yt_dlp
import os
import shutil

# Check if ffmpeg is available
FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None
if not FFMPEG_AVAILABLE:
    print("Warning: ffmpeg not found. Video and audio merging may fail.")

class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("390x460")

        # URL Entry
        tk.Label(root, text="YouTube URL:").pack(pady=5)
        self.url_entry = tk.Entry(root, width=50)
        self.url_entry.pack(pady=5)

        # Video Quality Selection
        tk.Label(root, text="Select Video Quality:").pack(pady=5)
        self.quality_var = tk.StringVar(value="720p")
        qualities = ["1080p", "720p", "480p", "360p"]
        self.quality_menu = tk.OptionMenu(root, self.quality_var, *qualities)
        self.quality_menu.pack(pady=5)

        # Subtitles Checkbox
        self.subtitles_var = tk.BooleanVar()
        tk.Checkbutton(root, text="Download Subtitles", variable=self.subtitles_var).pack(pady=5)

        # MP3 Download Options
        tk.Label(root, text="Audio Download Options:").pack(pady=5)
        self.audio_var = tk.StringVar(value="video_only")
        tk.Radiobutton(root, text="Video Only", variable=self.audio_var, value="video_only").pack(pady=2)
        tk.Radiobutton(root, text="MP3 Only", variable=self.audio_var, value="mp3_only").pack(pady=2)
        tk.Radiobutton(root, text="Both Video and MP3", variable=self.audio_var, value="both").pack(pady=2)

        # Save Location
        tk.Label(root, text="Save Location:").pack(pady=5)
        self.save_path_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Desktop"))
        self.save_path_entry = tk.Entry(root, textvariable=self.save_path_var, width=50)
        self.save_path_entry.pack(pady=5)
        tk.Button(root, text="Browse", command=self.browse_save_path).pack(pady=5)

        # Download Button
        tk.Button(root, text="Download", command=self.download).pack(pady=10)

        # Status Label
        self.status_label = tk.Label(root, text="")
        self.status_label.pack(pady=5)

    def browse_save_path(self):
        folder = filedialog.askdirectory(initialdir=self.save_path_var.get(), title="Select Save Location")
        if folder:
            self.save_path_var.set(folder)

    def download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return

        save_path = self.save_path_var.get()
        if not os.path.isdir(save_path):
            messagebox.showerror("Error", "Invalid save location")
            return

        if not FFMPEG_AVAILABLE:
            messagebox.showerror("Error", "ffmpeg is not installed or not in PATH. Video and audio merging will fail.")
            self.status_label.config(text="Download failed.")
            return

        self.status_label.config(text="Processing...")
        self.root.update()

        try:
            # Base yt-dlp options for video download
            video_ydl_opts = {
                'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
                'merge_output_format': 'mp4',  # Ensure video and audio are merged into MP4
            }

            # Handle video quality
            quality = self.quality_var.get()
            quality_height = int(quality[:-1])  # Extract the numeric part (e.g., 720 from "720p")
            video_ydl_opts['format'] = (
                f'bestvideo[height<={quality_height}]+bestaudio/best[height<={quality_height}]'
                f'/best[height<={quality_height}]'
            )

            # Handle subtitles
            subtitles_downloaded = False
            if self.subtitles_var.get():
                video_ydl_opts['writesubtitles'] = True
                video_ydl_opts['writeautomaticsub'] = True  # Include auto-generated subtitles
                video_ydl_opts['subtitleslangs'] = ['en', 'en-US']  # Try both 'en' and 'en-US'
                video_ydl_opts['subtitlesformat'] = 'srt'
                # Ensure subtitle file has the same name as the video
                video_ydl_opts['subtitlesouttmpl'] = os.path.join(save_path, '%(title)s.%(ext)s')

            audio_option = self.audio_var.get()
            video_file_path = None

            # Step 1: Download the video (with audio) if needed
            if audio_option in ["video_only", "both"]:
                with yt_dlp.YoutubeDL(video_ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    video_file_path = ydl.prepare_filename(info).replace('.%(ext)s', '.mp4')

                    # Check if subtitles were actually downloaded
                    expected_srt_file = os.path.join(save_path, f"{info['title']}.srt")
                    if self.subtitles_var.get() and os.path.exists(expected_srt_file):
                        subtitles_downloaded = True
                    elif self.subtitles_var.get():
                        # Check available subtitle languages for debugging
                        available_subs = info.get('subtitles', {})
                        auto_subs = info.get('automatic_captions', {})
                        if not available_subs.get('en') and not available_subs.get('en-US') and not auto_subs.get('en') and not auto_subs.get('en-US'):
                            messagebox.showwarning("Warning", "No English subtitles (manual or auto-generated) available for this video.")
                        else:
                            messagebox.showwarning("Warning", "Failed to download subtitles. Available languages: " + str(list(available_subs.keys()) + list(auto_subs.keys())))

            # Step 2: Download audio as MP3 if needed
            if audio_option in ["mp3_only", "both"]:
                audio_ydl_opts = {
                    'outtmpl': os.path.join(save_path, '%(title)s_audio.%(ext)s'),  # Different name to avoid conflict
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                }
                with yt_dlp.YoutubeDL(audio_ydl_opts) as ydl:
                    ydl.download([url])

            # Clean up any intermediate files (e.g., .webm)
            for file in os.listdir(save_path):
                if file.endswith('.webm') or file.endswith('.mkv'):
                    try:
                        os.remove(os.path.join(save_path, file))
                    except:
                        pass

            # Update status based on options
            if audio_option == "mp3_only":
                self.status_label.config(text="Audio downloaded as MP3!")
            elif audio_option == "both":
                self.status_label.config(text="Video (with audio) and MP3 downloaded!")
            else:
                self.status_label.config(text="Video (with audio) downloaded!")

            if subtitles_downloaded:
                self.status_label.config(text=self.status_label.cget("text") + " (with subtitles)")

        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            messagebox.showerror("Error", error_msg)
            self.status_label.config(text="Download failed.")

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloader(root)
    root.mainloop()