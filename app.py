import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="مساعدي الذكي", page_icon="🤖", layout="centered")

API_KEY = st.secrets["GROQ_API_KEY"]

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

SYSTEM_PROMPT = """أنت مساعد ذكي اسمه "مساعدي".
تتكلم العربية الفصحى المبسطة، وترد بإجابات واضحة ومختصرة.
أنت مفيد، مهذب، وتشرح بأمثلة عند الحاجة."""

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

st.title("🤖 مساعدي الذكي")
st.caption("شات بوت مجاني بالعربي")

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message("assistant").write(msg["content"])

user_input = st.chat_input("اكتب رسالتك هنا...")

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

    st.session_state.messages.append({"role": "assistant", "content": reply})

with st.sidebar:
    st.header("⚙️ الإعدادات")
    if st.button("🗑️ مسح المحادثة"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()
