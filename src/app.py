"""Streamlit frontend vocal pour la Clinique Dentaire Saint-Michel."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from dotenv import load_dotenv
from faster_whisper import WhisperModel

load_dotenv()

from google import genai

import src.voice as voice_module
from src.agent import create_chat
from src.config import WHISPER_COMPUTE_TYPE, WHISPER_MODEL
from src.tools import reset_session_state
from src.voice import record_audio, speak, transcribe


@st.cache_resource
def load_whisper():
    return WhisperModel(WHISPER_MODEL, compute_type=WHISPER_COMPUTE_TYPE)


st.set_page_config(
    page_title="Clinique Dentaire Saint-Michel",
    page_icon="\U0001f9b7",
    layout="centered",
)

st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(180deg, #f0f8ff 0%, #ffffff 100%); }
    .clinic-header {
        text-align: center;
        padding: 1rem 0 0.5rem;
        border-bottom: 2px solid #0e7490;
        margin-bottom: 1rem;
    }
    .clinic-header h1 { color: #0e7490; margin: 0; font-size: 1.8rem; }
    .clinic-header p { color: #6b7280; margin: 0.2rem 0 0; font-size: 1rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="clinic-header">
        <h1>\U0001f9b7 Clinique Dentaire Saint-Michel</h1>
        <p>Assistante virtuelle vocale</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Preload Whisper model (cached across reruns)
voice_module._whisper_model = load_whisper()

# --- Start call screen ---
if not st.session_state.get("call_active"):
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("\U0001f4de Lancer l'appel", use_container_width=True, type="primary"):
            st.session_state.call_active = True
            st.session_state.messages = []
            st.rerun()
    st.stop()

# --- Initialize call (first run only) ---
if not st.session_state.get("initialized"):
    reset_session_state()
    client = genai.Client()
    chat = create_chat(client)

    with st.spinner("Connexion en cours..."):
        greeting = chat.send_message("L'appel commence. Accueille le patient.").text or ""

    st.session_state.client = client
    st.session_state.chat = chat
    st.session_state.messages = [{"role": "assistant", "content": greeting}]
    st.session_state.initialized = True

    # Play greeting aloud
    speak(client, greeting)

# --- End call button (shown before blocking on mic) ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("\U0001f4f4 Raccrocher", use_container_width=True, type="secondary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- Render conversation ---
chat_area = st.empty()
status = st.empty()


def render():
    with chat_area.container():
        for msg in st.session_state.messages:
            avatar = "\U0001f9b7" if msg["role"] == "assistant" else "\U0001f9d1"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])


render()

# --- Listen / respond loop (blocks on mic input) ---
status.info("\U0001f3a4 En ecoute...")
audio = record_audio()
status.empty()

if not audio:
    st.rerun()

status.info("\U0001f4dd Transcription...")
user_text = transcribe(audio)
status.empty()

if not user_text:
    st.rerun()

st.session_state.messages.append({"role": "user", "content": user_text})
render()

status.info("\U0001f4ac Reponse en cours...")
response = st.session_state.chat.send_message(user_text).text or ""
status.empty()

st.session_state.messages.append({"role": "assistant", "content": response})
render()

speak(st.session_state.client, response)

st.rerun()
