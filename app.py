import streamlit as st
import subprocess
import os

st.set_page_config(page_title="Jarvis Backend Panel", page_icon="🤖")
st.title("🤖 Jarvis Backend Portal")

# 1. Safely route your OpenRouter API key from Streamlit's secrets into the environment variables
if "OPENROUTER_API_KEY" in st.secrets:
    os.environ["OPENROUTER_API_KEY"] = st.secrets["OPENROUTER_API_KEY"]
else:
    st.error("Missing API Key! Please paste your OPENROUTER_API_KEY into the Streamlit Advanced Settings -> Secrets panel.")
    st.stop()

# 2. Build the simple user interface text input
user_query = st.text_input("Send a request to Jarvis:", placeholder="Type something...")

if st.button("Trigger Backend Engine"):
    if user_query:
        with st.spinner("Running jarvis.py backend code..."):
            try:
                # 3. This executes 'python jarvis.py' in the background and sends the query
                result = subprocess.run(
                    ["python", "jarvis.py", user_query],
                    capture_output=True,
                    text=True,
                    timeout=30 # Prevents the script from hanging forever if it gets stuck
                )
                
                # 4. Display the results back to the website visitor
                if result.returncode == 0:
                    st.success("Backend completed execution successfully!")
                    if result.stdout:
                        st.subheader("Jarvis Response:")
                        st.write(result.stdout)
                else:
                    st.error("The backend script returned an execution error:")
                    st.code(result.stderr if result.stderr else result.stdout)
                    
            except Exception as e:
                st.error(f"Failed to communicate with backend: {e}")
    else:
        st.warning("Please enter a prompt first.")
        
