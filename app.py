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

# Tab များ သတ်မှတ်ခြင်း
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
                    
                    # Cloud ပေါ်တွင် 403 Error မတက်စေရန် Headers များထည့်ခြင်း
                    ydl_opts = {
                        'format': 'bestaudio/best' if is_audio else f'bestvideo[height<={quality[:-1]}]+bestaudio/best' if quality != "Best" else 'best',
                        'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                        'restrictfilenames': True,
                        'nocheckcertificate': True,
                        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                        'referer': 'https://www.google.com/',
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
                        
                        # ဖိုင်ပျောက်မသွားစေရန် RAM ထဲသို့ အရင်ဖတ်သွင်းခြင်း
                        with open(file_path, "rb") as f:
                            file_data = f.read()
                            
                        st.download_button(
                            label="💾 Save to Computer (နှိပ်ပါ)",
                            data=file_data,
                            file_name=os.path.basename(file_path),
                            mime="audio/mpeg" if is_audio else "video/mp4"
                        )
            except Exception as e:
                status.error(f"Error: {str(e)}")
        else:
            st.warning("YouTube URL ထည့်ပေးပါ။")

# --- TAB 2: TTS ---
with tab2:
    st.subheader("Edge-TTS (Myanmar/English)")
    tts_text = st.text_area("အသံထွက်ရန် စာသားများ:", height=150, key="t2_in")
    c1, c2, c3 = st.columns(3)
    with c1:
        narrator = st.selectbox("Voice:", ["Thiha (Male)", "Nilar (Female)"], key="t2_n")
        v_map = {"Thiha (Male)": "my-MM-ThihaNeural", "Nilar (Female)": "my-MM-NilarNeural"}
    with c2:
        speed = st.slider("Speed (%)", -50, 50, 0, 5)
    with c3:
        vol = st.slider("Volume (%)", -50, 50, 0, 5)

    if st.button("🔊 Generate Audio", type="primary"):
        if tts_text:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_mp3:
                async def run_tts():
                    c = edge_tts.Communicate(tts_text, v_map[narrator], rate=f"{speed:+d}%", volume=f"{vol:+d}%")
                    await c.save(tmp_mp3.name)
                asyncio.run(run_tts())
                st.audio(tmp_mp3.name)
                with open(tmp_mp3.name, "rb") as f:
                    st.download_button("📥 Download MP3", f, file_name="speech.mp3")

# --- TAB 3: DUBBING ---
with tab3:
    st.subheader("Auto-Sync Video Dubbing")
    dub_v = st.file_uploader("Video ဖိုင်တင်ပါ", type=["mp4", "mov"])
    dub_t = st.text_area("Dubbing စာသား:", height=150)
    
    if st.button("🎬 Start Dubbing", type="primary"):
        if dub_v and dub_t:
            with st.spinner("Processing..."):
                try:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        v_path = os.path.join(tmpdir, "v.mp4")
                        with open(v_path, "wb") as f: f.write(dub_v.getbuffer())
                        
                        clip = VideoFileClip(v_path)
                        temp_a = os.path.join(tmpdir, "t.mp3")
                        asyncio.run(edge_tts.Communicate(dub_t, "my-MM-ThihaNeural").save(temp_a))
                        
                        with AudioFileClip(temp_a) as audio_clip:
                            speed_val = int(max(min((audio_clip.duration / clip.duration - 1) * 100, 45), -25))
                            final_a = os.path.join(tmpdir, "f.mp3")
                            asyncio.run(edge_tts.Communicate(dub_t, "my-MM-ThihaNeural", rate=f"{speed_val:+d}%").save(final_a))
                            
                            with AudioFileClip(final_a) as new_audio:
                                final_v = "dubbed.mp4"
                                f_clip = clip.with_audio(new_audio) if hasattr(clip, 'with_audio') else clip.set_audio(new_audio)
                                f_clip.write_videofile(final_v, codec="libx264", audio_codec="aac")
                                f_clip.close()
                        clip.close()
                        st.video(final_v)
                        with open(final_v, "rb") as f:
                            st.download_button("📥 Download Video", f, file_name="dubbed.mp4")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
