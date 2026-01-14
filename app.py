import streamlit as st
import requests
import os

# --- ၁။ CONFIG & SECRETS ---
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
    ADMIN_USER = st.secrets["ADMIN_USER"]
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
except:
    st.error("Secrets များကို မတွေ့ပါ။ .streamlit/secrets.toml ကို စစ်ဆေးပါ။")
    st.stop()

API_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3-turbo"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# Page Setup
st.set_page_config(page_title="AI Audio Transcriber", page_icon="🎙️")

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

# --- ၃။ AI QUERY FUNCTION ---
def query_whisper(data):
    response = requests.post(API_URL, headers=headers, data=data)
    return response.json()

# --- ၄။ MAIN APP ---
if check_password():
    with st.sidebar:
        st.title("Settings")
        if st.button("Log Out"):
            del st.session_state["password_correct"]
            st.rerun()

    st.title("🎙️ AI Audio Transcriber")
    st.write(f"Welcome, **{ADMIN_USER}**! အသံဖိုင် (သို့မဟုတ်) ဗီဒီယိုဖိုင် တင်ပေးပါ။")

    # File Uploader (MP3, WAV, M4A, MP4 လက်ခံသည်)
    uploaded_file = st.file_uploader("ဖိုင်ရွေးချယ်ပါ (Max: 25MB)", type=["mp3", "wav", "m4a", "mp4"])

    if uploaded_file is not None:
        st.audio(uploaded_file) # တင်ထားတဲ့ဖိုင်ကို ပြန်နားထောင်လို့ရအောင်

        if st.button("AI နဲ့ စာသားပြောင်းမယ်"):
            try:
                with st.spinner('AI က စာသားပြောင်းပေးနေသည်... ခေတ္တစောင့်ပါ...'):
                    # Upload တင်ထားတဲ့ဖိုင်ကို ဖတ်ခြင်း
                    file_bytes = uploaded_file.read()
                    
                    # AI ဆီ ပို့ခြင်း
                    result = query_whisper(file_bytes)
                    
                    if isinstance(result, dict) and "text" in result:
                        st.success("✅ အောင်မြင်စွာ ပြောင်းလဲပြီးပါပြီ!")
                        
                        # ရလဒ်ပြသခြင်း
                        transcript_text = result["text"]
                        st.text_area("Result Transcript:", transcript_text, height=300)
                        
                        # Download ခလုတ်
                        st.download_button(
                            label="📥 Download Text File",
                            data=transcript_text,
                            file_name=f"transcript_{uploaded_file.name}.txt",
                            mime="text/plain"
                        )
                    elif isinstance(result, dict) and "error" in result:
                        st.error(f"AI Error: {result['error']}")
                    else:
                        st.error("AI Busy ဖြစ်နေပါသည်။ ခဏနေ ပြန်စမ်းကြည့်ပါ။")

            except Exception as e:
                st.error(f"Error ဖြစ်သွားပါသည်: {str(e)}")
