import streamlit as st
from streamlit_mic_recorder import mic_recorder
import os
import subprocess
import tempfile

st.set_page_config(page_title="Jarvis Voice Portal", page_icon="🎙️")
st.title("🎙️ Jarvis Voice-to-Text Portal")
st.write("Click the button, speak, and click stop. Your voice will be processed by your backend script.")

# 1. Forward OpenRouter secrets to the environment
if "OPENROUTER_API_KEY" in st.secrets:
    os.environ["OPENROUTER_API_KEY"] = st.secrets["OPENROUTER_API_KEY"]
else:
    st.error("Missing API Key! Please paste your OPENROUTER_API_KEY into Streamlit Advanced Settings -> Secrets.")
    st.stop()

# 2. Web browser microphone controller
audio = mic_recorder(
    start_prompt="🎙️ Start Speaking",
    stop_prompt="🛑 Stop & Process Voice",
    key='jarvis_voice_input'
)

# 3. Hand off the audio bytes to the backend
if audio:
    with st.spinner("Jarvis Backend is converting your voice to text..."):
        try:
            # Save browser audio data to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(audio['bytes'])
                temp_audio_path = temp_file.name

            # 4. Execute jarvis.py, passing the voice file path as a command-line argument
            result = subprocess.run(
                ["python", "jarvis.py", temp_audio_path],
                capture_output=True,
                text=True,
                timeout=45
            )

            # Delete the temporary file safely after processing
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)

            # 5. Display the result
            if result.returncode == 0:
                st.success("Processing Complete!")
                if result.stdout:
                    st.subheader("Transcribed Text & Backend Output:")
                    st.write(result.stdout)
            else:
                st.error("The backend returned an error:")
                st.code(result.stderr if result.stderr else result.stdout)

        except Exception as e:
            st.error(f"Error sending audio to backend: {e}")
            
