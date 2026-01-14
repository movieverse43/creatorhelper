import streamlit as st
import os
import yt_dlp
from openai import OpenAI

# OpenAI API Key (ဒီနေရာမှာ သင့် Key ကို ထည့်ပါ သို့မဟုတ် Streamlit Secrets သုံးပါ)
client = OpenAI(api_key="YOUR_OPENAI_API_KEY")

def check_password():
    def password_entered():
        if st.session_state["username"] == "admin" and st.session_state["password"] == "12345":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Username သို့မဟုတ် Password မှားနေပါတယ်။")
        return False
    return True

def download_audio(link):
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
        }],
        'outtmpl': 'temp_audio.%(ext)s',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([link])
    return "temp_audio.m4a"

if check_password():
    st.title("📝 AI YouTube Transcriber (Whisper)")
    video_url = st.text_input("YouTube URL ကို ထည့်ပါ:")

    if st.button("AI နဲ့ စာသားပြောင်းမယ်"):
        if video_url:
            try:
                with st.spinner('ဗီဒီယိုမှ အသံကို ဆွဲယူနေသည်...'):
                    audio_file = download_audio(video_url)
                
                with st.spinner('Whisper AI က စာသားပြောင်းပေးနေသည်...'):
                    with open(audio_file, "rb") as f:
                        transcript = client.audio.transcriptions.create(
                            model="whisper-1", 
                            file=f
                        )
                    st.success("အောင်မြင်စွာ ပြောင်းလဲပြီးပါပြီ!")
                    st.text_area("Result:", transcript.text, height=300)
                    
                    # File ပြန်ဖျက်ခြင်း
                    os.remove(audio_file)
            except Exception as e:
                st.error(f"အမှားတစ်ခုရှိနေပါသည်: {e}")
