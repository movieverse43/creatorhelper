import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import re

# Page အပြင်အဆင်
st.set_page_config(page_title="Myanmar YT Transcriber", page_icon="📝", layout="centered")

st.title("📝 YouTube Transcriber")
st.markdown("YouTube ဗီဒီယို Link ကို ထည့်လိုက်ရုံနဲ့ စာသားအဖြစ် ပြောင်းလဲပေးမှာပါ။")

# YouTube ID ထုတ်ယူတဲ့ Function
def extract_video_id(url):
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

# Input ပိုင်း
video_url = st.text_input("YouTube URL ကို ဒီမှာ Paste လုပ်ပါ:", placeholder="https://www.youtube.com/watch?v=...")

if st.button("စာသားပြောင်းမယ်"):
    if video_url:
        video_id = extract_video_id(video_url)
        if video_id:
            with st.spinner('ခဏစောင့်ပါ... စာသားတွေ ဆွဲယူနေပါတယ်...'):
                try:
                    # Transcript ဆွဲယူခြင်း
                    transcript = YouTubeTranscriptApi.get_transcript(video_id)
                    full_text = " ".join([t['text'] for t in transcript])
                    
                    st.success("ပြီးပါပြီ!")
                    
                    # ရလာတဲ့စာသားကို ပြသခြင်း
                    st.text_area("ရလဒ် (Transcript):", full_text, height=300)
                    
                    # Download ခလုတ်
                    st.download_button(
                        label="စာသားဖိုင် (Text File) အနေနဲ့ သိမ်းမယ်",
                        data=full_text,
                        file_name="transcript.txt",
                        mime="text/plain"
                    )
                except Exception as e:
                    st.error("Error: ဒီဗီဒီယိုမှာ Transcript မရှိပါဘူး (သို့မဟုတ်) ပိတ်ထားပါတယ်။")
        else:
            st.error("မှန်ကန်တဲ့ YouTube Link တစ်ခု ထည့်ပေးပါ။")
    else:
        st.warning("Link အရင်ထည့်ပေးပါ။")