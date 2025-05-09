import streamlit as st
import yt_dlp
import os
import json
import tempfile
import shutil
from streamlit.components.v1 import html

# Initialize session state for save path
if "save_path" not in st.session_state:
    st.session_state["save_path"] = os.path.expanduser("~/Downloads")

# Function to embed JavaScript for folder selection
def folder_selection_js():
    # HTML and JavaScript to show file explorer for folder selection
    html_code = """
    <input type="file" id="fileInput" webkitdirectory directory style="display:none" />
    <button onclick="document.getElementById('fileInput').click()">Select Folder</button>
    <script>
        document.getElementById('fileInput').addEventListener('change', function(event) {
            const filePath = event.target.files[0].webkitRelativePath;
            const folderPath = filePath.substring(0, filePath.lastIndexOf('/'));
            window.parent.postMessage({ type: 'folder-selected', folderPath: folderPath }, '*');
        });
    </script>
    """
    html(html_code)

# JavaScript listener for capturing the folder selection in Streamlit
def handle_folder_selection():
    # JavaScript code sends the folder path
    folder_path = st.query_params().get('folderPath', [None])[0]
    if folder_path:
        st.session_state["save_path"] = folder_path
        st.success(f"Download folder set to: {folder_path}")

# Handle folder selection
if st.button("Select Download Folder"):
    folder_selection_js()
    handle_folder_selection()

# Display selected folder
save_path = st.session_state["save_path"]
st.text(f"Save Location: {save_path}")

# YouTube URL input
url = st.text_input("Enter YouTube URL:")

# Video Quality selection
quality = st.selectbox("Select Video Quality:", ["1080p", "720p", "480p", "360p"])

# Audio format selection
audio_option = st.radio("Download Format:", ["Video Only", "MP3 Only", "Both Video & MP3"])

# Progress Bar
progress_bar = st.progress(0)
status_text = st.empty()

# Download function
def download_video():
    if not url:
        st.error("Please enter a YouTube URL")
        return

    st.info("Starting Download...")

    def progress_hook(d):
        if d['status'] == 'downloading':
            percent = float(d['_percent_str'].strip('%'))
            progress_bar.progress(int(percent))
            status_text.text(f"Downloading... {percent:.2f}%")
        elif d['status'] == 'finished':
            progress_bar.progress(100)
            status_text.text("Download Complete!")

    # yt-dlp options
    ydl_opts = {
        "outtmpl": os.path.join(save_path, "%(title)s.%(ext)s"),
        "progress_hooks": [progress_hook],
    }

    # Adjust format based on selection
    if audio_option == "MP3 Only":
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    else:
        quality_height = int(quality[:-1])
        ydl_opts["format"] = f"bestvideo[height<={quality_height}]+bestaudio/best"
        ydl_opts["merge_output_format"] = "mp4"

    # Download video
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        st.success("Download Complete!")
    except Exception as e:
        st.error(f"Error: {e}")

# Download button
if st.button("Download"):
    download_video()
