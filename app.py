import streamlit as st
import yt_dlp
import requests
import os
import re

# --- ၁။ CONFIG & SECRETS ---
# Secrets ထဲက အချက်အလက်များကို ခေါ်ယူခြင်း
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
    ADMIN_USER = st.secrets["ADMIN_USER"]
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
except:
    st.error("Secrets များကို မတွေ့ပါ။ .streamlit/secrets.toml ဖိုင်ကို စစ်ဆေးပါ။")
    st.stop()

API_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3-turbo"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# Page အပြင်အဆင်
st.set_page_config(page_title="AI YouTube Transcriber", page_icon="🎙️")

# --- ၂။ LOGIN LOGIC ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 Login Required")
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Log In"):
            if user == ADMIN_USER and pw == ADMIN_PASSWORD:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။")
        return False
    return True

# --- ၃။ UTILITY FUNCTIONS ---
def extract_video_id(url):
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def query_whisper(filename):
    with open(filename, "rb") as f:
        data = f.read()
    response = requests.post(API_URL, headers=headers, data=data)
    return response.json()

# --- ၄။ MAIN APP ---
if check_password():
    # Sidebar မှာ Logout Button ထားခြင်း
    with st.sidebar:
        st.title("Settings")
        if st.button("Log Out"):
            del st.session_state["password_correct"]
            st.rerun()

    st.title("🎙️ AI YouTube Transcriber")
    st.write(f"Welcome, **{ADMIN_USER}**!")

    video_url = st.text_input("YouTube URL:", placeholder="https://www.youtube.com/watch?v=...")

    if st.button("AI နဲ့ စာသားပြောင်းမယ် (Free)"):
        if video_url:
            video_id = extract_video_id(video_url)
            if video_id:
                try:
                    # အသံဖိုင် Download ဆွဲခြင်း
                    with st.spinner('ဗီဒီယိုမှ အသံကို ဆွဲယူနေသည် (YouTube)...'):
                        temp_filename = f"audio_{video_id}.m4a"
                        ydl_opts = {
                            'format': 'm4a/bestaudio/best',
                            'outtmpl': temp_filename,
                            'quiet': True,
                            'noplaylist': True
                        }
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            ydl.download([video_url])
                    
                    # AI ဆီ ပို့ခြင်း
                    with st.spinner('Whisper AI က စာသားပြောင်းပေးနေသည်...'):
                        result = query_whisper(temp_filename)
                        
                        if isinstance(result, dict) and "text" in result:
                            st.success("✅ အောင်မြင်စွာ ပြောင်းလဲပြီးပါပြီ!")
                            st.text_area("Result Transcript:", result["text"], height=300)
                            st.download_button(
                                label="📥 Download Text File",
                                data=result["text"],
                                file_name=f"transcript_{video_id}.txt",
                                mime="text/plain"
                            )
                        elif isinstance(result, dict) and "error" in result:
                            st.error(f"AI Error: {result['error']}")
                        else:
                            st.error("AI က အဖြေပြန်မပေးပါ။ ခဏနေ ပြန်စမ်းကြည့်ပါ။")
                    
                    # ယာယီဖိုင် ဖျက်သိမ်းခြင်း
                    if os.path.exists(temp_filename):
                        os.remove(temp_filename)

                except Exception as e:
                    st.error(f"Error ဖြစ်သွားပါသည်: {str(e)}")
            else:
                st.error("မှန်ကန်သော YouTube Link ထည့်ပေးပါ။")
        else:
            st.warning("Link အရင်ထည့်ပေးပါ။")
