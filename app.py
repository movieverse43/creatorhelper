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
tab1, tab2, tab3 = st.tabs(["📥 YouTube Downloader", "🔊 TTS (Text to Audio)", "🎬 Dubbing"])

# --- TAB 1: YOUTUBE DOWNLOADER (Bypass 403 Forbidden) ---
with tab1:
    st.subheader("YouTube Video/Audio Downloader")
    yt_url = st.text_input("YouTube URL:", placeholder="https://www.youtube.com/watch?v=...", key="yt_dl_url")
    
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        dl_type = st.selectbox("Format:", ["Video (MP4)", "Audio (MP3)"])
    with col_dl2:
        quality = st.selectbox("Resolution:", ["Best", "720p", "480p", "360p"])

    if st.button("📥 Download Now", type="primary"):
        if yt_url:
            with st.spinner("Downloading... Please wait."):
                try:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        is_audio = dl_type == "Audio (MP3)"
                        
                        # YouTube ရဲ့ Bot Detection ကို ကျော်လွှားရန် Browser headers များ ထည့်ခြင်း
                        ydl_opts = {
                            'format': 'bestaudio/best' if is_audio else f'bestvideo[height<={quality[:-1]}]+bestaudio/best' if quality != "Best" else 'best',
                            'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                            'nocheckcertificate': True,
                            'ignoreerrors': True,
                            'no_warnings': True,
                            'quiet': True,
                            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            'referer': 'https://www.youtube.com/',
                            'add_header': [
                                'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                                'Accept-Language: en-US,en;q=0.5',
                            ],
                        }

                        if is_audio:
                            ydl_opts['postprocessors'] = [{
                                'key': 'FFmpegExtractAudio',
                                'preferredcodec': 'mp3',
                                'preferredquality': '192',
                            }]

                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(yt_url, download=True)
                            raw_path = ydl.prepare_filename(info)
                            
                            # extension ပြန်လည်စစ်ဆေးခြင်း
                            final_path = os.path.splitext(raw_path)[0] + (".mp3" if is_audio else ".mp4")
                            
                            # အကယ်၍ ffmpeg မရှိလျှင် .mkv သို့မဟုတ် တခြား format ဖြစ်နိုင်သောကြောင့် အမှန်တကယ်ရှိသောဖိုင်ကိုရှာသည်
                            if not os.path.exists(final_path):
                                # ပုံမှန်အားဖြင့် extract_info အပြီးတွင် ဖိုင်နာမည် ပြောင်းလဲသွားနိုင်သဖြင့် list ပြန်စစ်သည်
                                files = [os.path.join(tmpdir, f) for f in os.listdir(tmpdir)]
                                if files: final_path = files[0]

                            st.success(f"✅ Downloaded: {info.get('title')}")
                            with open(final_path, "rb") as f:
                                st.download_button(
                                    label="💾 Save to Computer",
                                    data=f,
                                    file_name=os.path.basename(final_path),
                                    mime="audio/mpeg" if is_audio else "video/mp4"
                                )
                except Exception as e:
                    st.error(f"Download Error: {str(e)}")
        else:
            st.warning("YouTube URL ထည့်ပေးပါ။")

# --- TAB 2: TTS (Edge-TTS) ---
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
            out_tts = "speech.mp3"
            async def run_tts():
                c = edge_tts.Communicate(tts_text, v_map[narrator], rate=f"{speed:+d}%", volume=f"{vol:+d}%")
                await c.save(out_tts)
            asyncio.run(run_tts())
            st.audio(out_tts)

# --- TAB 3: DUBBING (Auto-Sync) ---
with tab3:
    st.subheader("Auto-Sync Video Dubbing")
    dub_v = st.file_uploader("Video တင်ပါ", type=["mp4", "mov"])
    dub_t = st.text_area("Dubbing စာသား:", height=150)
    
    if st.button("🎬 Start Dubbing", type="primary"):
        if dub_v and dub_t:
            with st.spinner("Processing Dubbing..."):
                try:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        v_path = os.path.join(tmpdir, "v.mp4")
                        with open(v_path, "wb") as f: f.write(dub_v.getbuffer())
                        
                        clip = VideoFileClip(v_path)
                        v_dur = clip.duration
                        
                        temp_a = os.path.join(tmpdir, "t.mp3")
                        async def get_a():
                            await edge_tts.Communicate(dub_t, "my-MM-ThihaNeural").save(temp_a)
                        asyncio.run(get_a())
                        
                        with AudioFileClip(temp_a) as audio_clip:
                            a_dur = audio_clip.duration
                            # Speed calculation (-25% to +45%)
                            speed_f = int(max(min((a_dur / v_dur - 1) * 100, 45), -25))
                            st.write(f"Syncing Speed: {speed_f}%")
                            
                            final_a = os.path.join(tmpdir, "f.mp3")
                            async def get_f():
                                await edge_tts.Communicate(dub_t, "my-MM-ThihaNeural", rate=f"{speed_f:+d}%").save(final_a)
                            asyncio.run(get_f())
                            
                            final_out = "dubbed_video.mp4"
                            with AudioFileClip(final_a) as new_audio:
                                f_clip = clip.with_audio(new_audio) if hasattr(clip, 'with_audio') else clip.set_audio(new_audio)
                                f_clip.write_videofile(final_out, codec="libx264", audio_codec="aac")
                                f_clip.close()
                        clip.close()
                        st.video(final_out)
                        st.success("Dubbing အောင်မြင်ပါသည်။")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
