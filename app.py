import streamlit as st
import whisper
import yt_dlp
import tempfile
import os
import asyncio
import edge_tts
from moviepy import VideoFileClip, AudioFileClip

# --- Page Config ---
st.set_page_config(page_title="AI Audio & Dubbing Toolkit", page_icon="🎙️", layout="wide")
st.title("🎙️ AI Audio & Dubbing Toolkit")

# Tab များကို ဤနေရာတွင် ကြေညာပါသည်
tab1, tab2, tab3 = st.tabs(["🎥 Transcribe", "🔊 TTS", "🎬 Dubbing"])

# --- TAB 1: TRANSCRIPTION ---
with tab1:
    @st.cache_resource
    def load_whisper():
        return whisper.load_model("base")
    model = load_whisper()

    st.subheader("Video to Text")
    option = st.radio("Source:", ("YouTube Link", "File Upload"), horizontal=True, key="t1_opt")
    input_data = st.text_input("URL:") if option == "YouTube Link" else st.file_uploader("Upload File", type=["mp4","mp3","m4a"])

    if st.button("🚀 Start Transcribing", type="primary"):
        if input_data:
            with st.spinner("Processing..."):
                with tempfile.TemporaryDirectory() as tmpdir:
                    audio_path = os.path.join(tmpdir, "audio")
                    if option == "YouTube Link":
                        ydl_opts = {'format': 'm4a/bestaudio', 'outtmpl': audio_path + '.%(ext)s', 'quiet': True}
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([input_data])
                        audio_path += ".m4a"
                    else:
                        audio_path = os.path.join(tmpdir, input_data.name)
                        with open(audio_path, "wb") as f: f.write(input_data.getbuffer())
                    
                    result = model.transcribe(audio_path, fp16=False)
                    st.text_area("Result:", value=result["text"], height=250)
                    if hasattr(st, "copy_to_clipboard"): st.copy_to_clipboard(result["text"])

# --- TAB 2: TTS ---
with tab2:
    st.subheader("Text to Audio")
    tts_text = st.text_area("စာသားများ ရိုက်ထည့်ပါ:", height=150, key="t2_input")
    col1, col2, col3 = st.columns(3)
    with col1:
        narrator = st.selectbox("Voice:", ["Thiha (Male)", "Nilar (Female)"])
        voice_map = {"Thiha (Male)": "my-MM-ThihaNeural", "Nilar (Female)": "my-MM-NilarNeural"}
    with col2:
        speed = st.slider("Speed (%)", -50, 50, 0, 5)
    with col3:
        vol = st.slider("Volume (%)", -50, 50, 0, 5)

    if st.button("🔊 Generate Audio", type="primary"):
        if tts_text:
            output_file = "output_tts.mp3"
            async def run_edge():
                comm = edge_tts.Communicate(tts_text, voice_map[narrator], rate=f"{speed:+d}%", volume=f"{vol:+d}%")
                await comm.save(output_file)
            asyncio.run(run_edge())
            st.audio(output_file)

# --- TAB 3: DUBBING ---
with tab3:
    st.subheader("Video Dubbing (Auto-Sync)")
    dub_v = st.file_uploader("Video တင်ပါ", type=["mp4", "mov"], key="t3_v")
    dub_t = st.text_area("Dubbing စာသား:", height=150, key="t3_t")
    
    if st.button("🎬 Start Dubbing", type="primary"):
        if dub_v and dub_t:
            with st.spinner("Dubbing in progress..."):
                try:
                    # Windows Permission Error အတွက် Temp Directory စနစ်
                    with tempfile.TemporaryDirectory() as tmpdir:
                        v_path = os.path.join(tmpdir, "v.mp4")
                        with open(v_path, "wb") as f:
                            f.write(dub_v.getbuffer())
                        
                        clip = VideoFileClip(v_path)
                        v_dur = clip.duration
                        
                        # 1. TTS အသံ ကြာချိန်ကို စစ်ဆေးခြင်း
                        temp_a_path = os.path.join(tmpdir, "temp.mp3")
                        async def get_initial_a():
                            c = edge_tts.Communicate(dub_t, "my-MM-ThihaNeural")
                            await c.save(temp_a_path)
                        asyncio.run(get_initial_a())
                        
                        with AudioFileClip(temp_a_path) as temp_audio:
                            a_dur = temp_audio.duration

                        # Speed calculation (-25% to +45%)
                        speed_f = int(max(min((a_dur / v_dur - 1) * 100, 45), -25))
                        st.info(f"ဗီဒီယိုကြာချိန်: {v_dur:.2f}s | အမြန်နှုန်းချိန်ညှိမှု: {speed_f}%")
                        
                        # 2. Final TTS ကို အမြန်နှုန်းအသစ်ဖြင့် ထုတ်ယူခြင်း
                        final_a_path = os.path.join(tmpdir, "final.mp3")
                        async def get_final_a():
                            c = edge_tts.Communicate(dub_t, "my-MM-ThihaNeural", rate=f"{speed_f:+d}%")
                            await c.save(final_a_path)
                        asyncio.run(get_final_a())
                        
                        # 3. ဗီဒီယိုနှင့် အသံ ပေါင်းစပ်ခြင်း
                        final_v_output = "dubbed_video_result.mp4"
                        with AudioFileClip(final_a_path) as new_audio:
                            # MoviePy Version ၂ မျိုးလုံးအတွက် Support လုပ်ရန်
                            final_clip = clip.with_audio(new_audio) if hasattr(clip, "with_audio") else clip.set_audio(new_audio)
                            final_clip.write_videofile(final_v_output, codec="libx264", audio_codec="aac")
                            final_clip.close()
                        
                        clip.close() # Video clip ကို ပိတ်ရန်

                        st.video(final_v_output)
                        st.success("Dubbing အောင်မြင်ပါသည်။")
                        with open(final_v_output, "rb") as f:
                            st.download_button("📥 Download Video", f, file_name="dubbed_video.mp4")
                            
                except Exception as e:
                    st.error(f"Dubbing Error: {str(e)}")
        else:
            st.warning("ဗီဒီယိုနှင့် စာသားကို အရင်ထည့်ပါ။")
