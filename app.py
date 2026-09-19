import streamlit as st
from streamlit_mic_recorder import mic_recorder
from openai import OpenAI
import os
import sys

# Import your entire script functions directly
try:
    import jarvis
except ImportError:
    st.error("Could not link jarvis.py. Make sure both app.py and jarvis.py are in the same folder on GitHub.")
    st.stop()

st.set_page_config(page_title="Jarvis Web Terminal", page_icon="🤖")
st.title("🤖 J.A.R.V.I.S. Web Hub")
st.caption("Bridging Web Interface to Android Architecture")

# 1. Initialize API Key Validation
if "OPENROUTER_API_KEY" in st.secrets:
    api_key = st.secrets["OPENROUTER_API_KEY"]
    os.environ["OPENROUTER_API_KEY"] = api_key
    jarvis.OPENROUTER_API_KEY = api_key
else:
    st.error("Please add your OPENROUTER_API_KEY in the Streamlit Advanced Settings -> Secrets panel.")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

# 2. Browser Audio Collector
audio = mic_recorder(
    start_prompt="🎙️ Wake Jarvis / Speak Command",
    stop_prompt="🛑 Stop & Execute Tasks",
    key='jarvis_web_mic'
)

if audio:
    with st.spinner("Converting Voice-to-Text via OpenRouter Whisper..."):
        try:
            audio_payload = ("audio.wav", audio['bytes'], "audio/wav")
            transcription = client.audio.transcriptions.create(
                model="openai/whisper-large-v3",
                file=audio_payload
            )
            user_text = transcription.text
            
            st.info(f"**Recognized Voice Command:** '{user_text}'")
            
            # 3. Intercept Termux Hardware commands to show safely on screen instead of crashing
            # We mock the print/speak pipeline
            output_placeholder = st.empty()
            
            # Redirect jarvis' internal speak mechanism to print out on screen instead
            def web_speak(text):
                st.success(f"**JARVIS Response:** {text}")
            jarvis.speak = web_speak

            with st.spinner("Executing system processes..."):
                # Run your core direct handling commands logic!
                result = jarvis.handle_direct_command(user_text)
                
                if result == "__EXIT__":
                    st.warning("Shutdown instruction received.")
                elif result:
                    web_speak(result)
                else:
                    # Handoff to OpenRouter LLM if no native task matches
                    st.write("🧠 Processing fallback via AI network...")
                    ai_answer = jarvis.ask_ai(user_text)
                    web_speak(ai_answer)
                    
        except Exception as e:
            st.error(f"Execution Error: {e}")
            
