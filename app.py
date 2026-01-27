import streamlit as st
import yt_dlp
import tempfile
import os
import asyncio
import edge_tts
from moviepy import VideoFileClip, AudioFileClip

# --- Page Config ---
st.set_page_config(page_title="Creator Helper Toolkit", page_icon="🎬", layout="wide")
st.title("🎬 Creator Helper Toolkit")

tab1, tab2, tab3 = st.tabs(["📥 YouTube Downloader", "🔊 TTS", "🎬 Dubbing"])

# --- TAB 1: YOUTUBE DOWNLOADER ---
with tab1:
    st.subheader("YouTube Downloader")
    yt_url = st.text_input("YouTube URL:", placeholder="https://www.youtube.com/watch?v=...", key="yt_dl_url")
    
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        dl_type = st.selectbox("Format:", ["Video (MP4)", "Audio (MP3)"])
    with col_dl2:
        quality = st.selectbox("Resolution:", ["Best", "720p", "480p", "360p"])

    if st.button("📥 Download Now", type="primary"):
        if yt_url:
            status = st.empty()
            progress = st.progress(0)
            try:
                is_audio = dl_type == "Audio (MP3)"
                
                with tempfile.TemporaryDirectory() as tmpdir:
                    status.info("🔄 YouTube ဆီမှ အချက်အလက်ရယူနေသည်...")
                    progress.progress(20)
                    
                    # 403 Forbidden ကို ကျော်လွှားရန် နောက်ဆုံးပေါ် headers များ
                    ydl_opts = {
                        'format': 'bestaudio/best' if is_audio else f'bestvideo[height<={quality[:-1]}]+bestaudio/best' if quality != "Best" else 'best',
                        'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                        'restrictfilenames': True,
                        'nocheckcertificate': True,
                        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                        'referer': 'https://www.google.com/',
                        'http_headers': {
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                            'Accept-Language': 'en-US,en;q=0.5',
                        }
                    }

                    if is_audio:
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }]

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        progress.progress(50)
                        status.info("📥 ဒေါင်းလုဒ်ဆွဲနေသည်...")
                        info = ydl.extract_info(yt_url, download=True)
                        file_path = ydl.prepare_filename(info)
                        
                        if is_audio:
                            file_path = os.path.splitext(file_path)[0] + ".mp3"
                        
                        progress.progress(100)
                        status.success(f"✅ Downloaded: {info.get('title')}")
                        
                        # ဖိုင်ပျောက်မသွားစေရန် Memory (RAM) ထဲသို့ အရင်ဖတ်သွင်းခြင်း
                        with open(file_path, "rb") as f:
                            file_bytes = f.read()
                            
                        st.download_button(
                            label="💾 Save to Computer (ဒါကိုနှိပ်ပါ)",
                            data=file_bytes,
                            file_name=os.path.basename(file_path),
                            mime="audio/mpeg" if is_audio else "video/mp4"
                        )
            except Exception as e:
                status.error(f"Download Error: {str(e)}")
                st.info("💡 အကြံပြုချက်: YouTube က ပိတ်ထားပါက တခြား Link တစ်ခုဖြင့် ပြန်စမ်းကြည့်ပါ။")
        else:
            st.warning("YouTube URL ထည့်ပေးပါ။")

# --- TAB 2 & 3 ကုဒ်များမှာ ယခင်အတိုင်းဖြစ်ပါသည် ---
# (နေရာလွတ်စေရန် အကျဉ်းချထားပါသည်)
