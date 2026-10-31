import streamlit as st
import agent  # noqa: F401  (loads .env on import)
from agent import db, loop
from agent.providers import get_provider
from agent.providers.base import LLMError

st.set_page_config(page_title="Student Support Agent")
db.ensure()
st.title("Student Support Agent")

@st.cache_resource
def provider():
    return get_provider()

try:
    prov = provider()
except LLMError as e:   # config problems only; the message is ours and contains no secrets
    st.error("Setup problem: " + (e.detail or "invalid configuration"))
    st.markdown("Fix `.env` (see README), then restart. Example: `LLM_PROVIDER=gemini`, `GEMINI_API_KEY=...`, `MODEL=...`")
    st.stop()

sid = st.sidebar.selectbox("Student (demo selector)", ["S101", "S102", "S103"])
st.sidebar.caption("⚠️ Demo selector only – **not authentication**. Real sign-in/authorization is Assignment 2.")
st.sidebar.caption(f"Provider: {prov.name} · Model: {prov.model}")
if st.session_state.get("sid") != sid or st.sidebar.button("New session (memory persists)"):
    st.session_state.update(sid=sid, history=[], view=[])

for role, text, tr in st.session_state.view:
    with st.chat_message(role):
        st.write(text)
        if tr:
            with st.expander("trace"): st.json(tr)

if q := st.chat_input("Ask about fees, scholarships, courses..."):
    with st.chat_message("user"): st.write(q)
    try:
        ans, tr = loop.chat(prov, sid, st.session_state.history, q)
    except Exception:
        ans, tr = "Something went wrong. Please try again.", None
    with st.chat_message("assistant"):
        st.write(ans)
        if tr:
            with st.expander("trace"): st.json(tr)
    st.session_state.view += [("user", q, None), ("assistant", ans, tr)]
