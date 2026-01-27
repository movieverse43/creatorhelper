import streamlit as st
import yt_dlp
import tempfile
import os
import asyncio
import edge_tts
from moviepy import VideoFileClip, AudioFileClip

# --- Page Config ---
st.set_page_config(page_title="AI Audio & Video Toolkit", page_icon="🎥", layout="wide")
st.title("🎥 AI Audio & Video Toolkit")

# Tab များကို ကြေညာခြင်း
tab1, tab2, tab3 = st.tabs(["📥 YouTube Downloader", "🔊 TTS", "🎬 Dubbing"])

# --- TAB 1: YOUTUBE DOWNLOADER ---
with tab1:
    st.subheader("YouTube Video/Audio Downloader")
    yt_url = st.text_input("YouTube URL ကို ဒီမှာထည့်ပါ:", placeholder="https://www.youtube.com/watch?v=...", key="yt_dl_url")
    
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        dl_type = st.selectbox("Download လုပ်မည့် အမျိုးအစား:", ["Video (MP4)", "Audio (MP3/M4A)"])
    with col_dl2:
        quality = st.selectbox("Quality (Video အတွက်သာ):", ["Best Quality", "720p", "480p", "360p"])

    if st.button("📥 Start Download", type="primary"):
        if yt_url:
            with st.spinner("YouTube မှ ဖိုင်ရယူနေသည်..."):
                try:
                    # Download options ချိန်ညှိခြင်း
                    ydl_opts = {
                        'format': 'bestaudio/best' if dl_type == "Audio (MP3/M4A)" else 'bestvideo+bestaudio/best',
                        'nocheckcertificate': True,
                        'quiet': True,
                    }
                    
                    if dl_type == "Audio (MP3/M4A)":
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }]

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(yt_url, download=True)
                        file_name = ydl.prepare_filename(info)
                        
                        # Audio ဖြစ်လျှင် mp3 ဖြစ်သွားအောင် extension ပြင်ခြင်း
                        if dl_type == "Audio (MP3/M4A)":
                            file_name = os.path.splitext(file_name)[0] + ".mp3"

                        st.success(f"✅ Download ပြီးပါပြီ: {info.get('title')}")
                        
                        with open(file_name, "rb") as f:
                            st.download_button(
                                label="💾 Click here to save file",
                                data=f,
                                file_name=os.path.basename(file_name),
                                mime="video/mp4" if "Video" in dl_type else "audio/mpeg"
                            )
                        # Download ပြီးရင် စက်ထဲက ဖိုင်ကို ပြန်ဖျက်ခြင်း (Cleanup)
                        # os.remove(file_name) 
                except Exception as e:
                    st.error(f"Download Error: {str(e)}")
        else:
            st.warning("YouTube URL အရင်ထည့်ပါ။")

# --- TAB 2: TTS (Edge-TTS) ---
with tab2:
    st.subheader("Text to Audio (Edge-TTS)")
    tts_text = st.text_area("အသံထွက်စေချင်သော စာသားများ:", height=150, key="t2_input")
    c1, c2, c3 = st.columns(3)
    with c1:
        narrator = st.selectbox("Voice:", ["Thiha (Male)", "Nilar (Female)"], key="t2_n")
        v_map = {"Thiha (Male)": "my-MM-ThihaNeural", "Nilar (Female)": "my-MM-NilarNeural"}
    with c2:
        speed = st.slider("Speed (%)", -50, 50, 0, 5, key="t2_s")
    with c3:
        vol = st.slider("Volume (%)", -50, 50, 0, 5, key="t2_v")

    if st.button("🔊 Generate Audio", type="primary", key="t2_btn"):
        if tts_text:
            out_tts = "output_tts.mp3"
            async def run_tts():
                c = edge_tts.Communicate(tts_text, v_map[narrator], rate=f"{speed:+d}%", volume=f"{vol:+d}%")
                await c.save(out_tts)
            asyncio.run(run_tts())
            st.audio(out_tts)

# --- TAB 3: DUBBING ---
with tab3:
    st.subheader("Video Dubbing (Auto-Sync)")
    dub_v = st.file_uploader("Video တင်ပါ", type=["mp4", "mov"], key="t3_v")
    dub_t = st.text_area("Dubbing စာသား:", height=150, key="t3_t")
    
    if st.button("🎬 Start Dubbing", type="primary", key="t3_btn"):
        if dub_v and dub_t:
            with st.spinner("Processing..."):
                try:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        v_path = os.path.join(tmpdir, "v.mp4")
                        with open(v_path, "wb") as f: f.write(dub_v.getbuffer())
                        
                        clip = VideoFileClip(v_path)
                        v_dur = clip.duration
                        
                        temp_a = os.path.join(tmpdir, "temp.mp3")
                        async def get_a():
                            c = edge_tts.Communicate(dub_t, "my-MM-ThihaNeural")
                            await c.save(temp_a)
                        asyncio.run(get_a())
                        
                        with AudioFileClip(temp_a) as t_audio:
                            a_dur = t_audio.duration

                        speed_f = int(max(min((a_dur / v_dur - 1) * 100, 45), -25))
                        st.info(f"ဗီဒီယိုကြာချိန်: {v_dur:.2f}s | Speed: {speed_f}%")
                        
                        final_a = os.path.join(tmpdir, "final.mp3")
                        async def get_f_a():
                            c = edge_tts.Communicate(dub_t, "my-MM-ThihaNeural", rate=f"{speed_f:+d}%")
                            await c.save(final_a)
                        asyncio.run(get_f_a())
                        
                        final_out = "dubbed_result.mp4"
                        with AudioFileClip(final_a) as new_audio:
                            f_clip = clip.with_audio(new_audio) if hasattr(clip, "with_audio") else clip.set_audio(new_audio)
                            f_clip.write_videofile(final_out, codec="libx264", audio_codec="aac")
                            f_clip.close()
                        clip.close()

                        st.video(final_out)
                        with open(final_out, "rb") as f:
                            st.download_button("📥 Download Dubbed Video", f, file_name="dubbed.mp4")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
