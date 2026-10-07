import streamlit as st
from openai import OpenAI
import edge_tts
import asyncio
import io
import tempfile
import os

st.set_page_config(page_title="مساعدي الذكي", page_icon="🤖", layout="centered")

# ====== إعدادات ======
API_KEY = st.secrets["GROQ_API_KEY"]
VOICE = "ar-SA-HamedNeural"

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

SYSTEM_PROMPT = """أنت مساعد ذكي اسمه "مساعدي".
تتكلم العربية الفصحى المبسطة، وترد بإجابات واضحة ومختصرة.
أنت مفيد، مهذب، وتشرح بأمثلة عند الحاجة."""

# ====== دوال مساعدة ======
def transcribe_audio(audio_bytes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        f.write(audio_bytes)
        temp_path = f.name
    try:
        with open(temp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3-turbo",
                language="ar",
            )
        return transcription.text
    finally:
        os.unlink(temp_path)

async def text_to_speech(text, filename):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(filename)

# ====== الذاكرة ======
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

# ====== الواجهة ======
st.title("🤖 مساعدي الذكي")
st.caption("شات بوت مجاني بالعربي — كتابة أو صوت")

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message("assistant").write(msg["content"])

# ====== إدخال صوتي ======
st.markdown("---")
st.subheader("🎤 اضغط للتحدث")

from streamlit_mic_recorder import mic_recorder

audio = mic_recorder(
    start_prompt="ابدأ التسجيل",
    stop_prompt="أوقف التسجيل",
    just_once=True,
    key="voice_recorder",
)

user_input = None

if audio and audio["id"] != st.session_state.last_audio_id:
    st.session_state.last_audio_id = audio["id"]
    with st.spinner("جاري تحويل الصوت إلى نص..."):
        try:
            user_input = transcribe_audio(audio["bytes"])
            if user_input:
                st.success(f"قلت: {user_input}")
        except Exception as e:
            st.error(f"خطأ في تحويل الصوت: {e}")

# ====== إدخال نصي ======
if user_input is None:
    user_input = st.chat_input("أو اكتب رسالتك هنا...")

# ====== معالجة الرسالة ======
if user_input:
    st.chat_message("user").write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("يفكر..."):
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=st.session_state.messages,
                temperature=0.7,
            )
            reply = response.choices[0].message.content
        st.write(reply)

        with st.spinner("جاري تحويل الرد إلى صوت..."):
            try:
                audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
                asyncio.run(text_to_speech(reply, audio_path))
                with open(audio_path, "rb") as f:
                    audio_bytes = f.read()
                st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                os.unlink(audio_path)
            except Exception as e:
                st.warning(f"تعذر تشغيل الصوت: {e}")

    st.session_state.messages.append({"role": "assistant", "content": reply})

# ====== الشريط الجانبي ======
with st.sidebar:
    st.header("⚙️ الإعدادات")
    if st.button("🗑️ مسح المحادثة"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.session_state.last_audio_id = None
        st.rerun()
