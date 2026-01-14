import streamlit as st
import requests
import os
import time

# --- ၁။ CONFIG & SECRETS ---
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
    ADMIN_USER = st.secrets["ADMIN_USER"]
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
except:
    st.error("Secrets များကို မတွေ့ပါ။ Streamlit Settings တွင် Secrets များ ထည့်သွင်းပါ။")
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

# --- ၃။ AI QUERY FUNCTION (Improved) ---
def query_whisper(data):
    # Model လေးနေရင် အကြိမ်ကြိမ် ပြန်ကြိုးစားမည့် logic
    for i in range(3): 
        response = requests.post(API_URL, headers=headers, data=data)
        
        # အကယ်၍ JSON မဟုတ်ဘဲ အခြား error တက်လာရင်
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 503: # Model Loading ဖြစ်နေရင်
            st.info("AI Model ကို စက်နှိုးနေပါသည် (Loading)... ၂၀ စက္ကန့်ခန့် စောင့်ပေးပါ။")
            time.sleep(20)
            continue
        else:
            return {"error": f"Server Error: {response.status_code} - {response.text}"}
    return {"error": "AI Model အလုပ်လုပ်ရန် အချိန်ကြာမြင့်နေပါသည်။ ခဏနေမှ ပြန်စမ်းကြည့်ပါ။"}

# --- ၄။ MAIN APP ---
if check_password():
    with st.sidebar:
        st.title("Settings")
        if st.button("Log Out"):
            del st.session_state["password_correct"]
            st.rerun()

    st.title("🎙️ AI Audio Transcriber")
    st.write(f"Welcome, **{ADMIN_USER}**!")

    # File Uploader
    uploaded_file = st.file_uploader("အသံဖိုင် (သို့) ဗီဒီယိုဖိုင် တင်ပါ", type=["mp3", "wav", "m4a", "mp4"])

    if uploaded_file is not None:
        st.audio(uploaded_file)

        if st.button("AI နဲ့ စာသားပြောင်းမယ်"):
            try:
                with st.spinner('AI က စာသားပြောင်းပေးနေသည်...'):
                    # ဖိုင်ကို ဖတ်ခြင်း
                    file_bytes = uploaded_file.read()
                    
                    # API ကို ခေါ်ခြင်း
                    result = query_whisper(file_bytes)
                    
                    if isinstance(result, dict) and "text" in result:
                        st.success("✅ အောင်မြင်စွာ ပြောင်းလဲပြီးပါပြီ!")
                        st.text_area("Result Transcript:", result["text"], height=300)
                        st.download_button("📥 Download Result", result["text"], file_name="transcript.txt")
                    elif isinstance(result, dict) and "error" in result:
                        st.error(f"AI Error: {result['error']}")
                    else:
                        st.error("မထင်မှတ်ထားသော အမှားတစ်ခု ဖြစ်ပေါ်ခဲ့ပါသည်။")

            except Exception as e:
                st.error(f"Error: {str(e)}")
