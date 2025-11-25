import streamlit as st

st.set_page_config(page_title="Test Deployment App")

st.title("🚀 Streamlit Deployment Test")

st.write("This is a simple Streamlit app to verify deployment is working correctly.")

name = st.text_input("Enter your name:")

if name:
    st.success(f"Hello, {name}! Your Streamlit app is running!")

st.write("---")
st.write("If you can see this, your app deployed successfully.")
