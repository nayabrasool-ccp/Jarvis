import streamlit as st
import os

# Import your backend functions directly from your jarvis.py file
# (Replace 'your_main_backend_function' with the actual function name in jarvis.py)
try:
    from jarvis import your_main_backend_function 
except ImportError:
    st.error("Could not import your backend code. Double-check your function names.")

st.set_page_config(page_title="Jarvis Web Portal", page_icon="🤖")
st.title("🤖 Jarvis Control Center")
st.write("Interact with your backend engine via the web.")

# Step 1: Ensure the OpenRouter secret is passed into the system environment
if "OPENROUTER_API_KEY" in st.secrets:
    os.environ["OPENROUTER_API_KEY"] = st.secrets["OPENROUTER_API_KEY"]
else:
    st.error("Missing OPENROUTER_API_KEY in Streamlit Cloud Secrets.")
    st.stop()

# Step 2: Build the Frontend Inputs
user_input = st.text_input("Send a command to Jarvis Backend:", placeholder="Type here...")

# Step 3: Trigger the Backend Logic
if st.button("Execute Command"):
    if user_input:
        with st.spinner("Processing in backend..."):
            try:
                # Run your backend function using the user's input
                backend_output = your_main_backend_function(user_input)
                
                st.success("Execution Complete!")
                st.subheader("Backend Output:")
                st.write(backend_output)
            except Exception as e:
                st.error(f"Backend crashed: {e}")
    else:
        st.warning("Please enter a command first.")
      
