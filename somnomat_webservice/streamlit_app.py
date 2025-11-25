import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import io

st.set_page_config(page_title="Basic Streamlit App", layout="centered")

st.title("Basic Streamlit App")
st.write("A minimal demo to upload files, view data, and show simple charts.")

st.sidebar.header("Controls")
mode = st.sidebar.selectbox("Mode", ["Demo data", "Upload CSV", "Upload Image"])

def sample_data(n=100):
    x = np.linspace(0, 4 * np.pi, n)
    return pd.DataFrame({
        "x": np.arange(n),
        "sin": np.sin(x),
        "cos": np.cos(x) + 0.1 * np.random.randn(n)
    })

if mode == "Demo data":
    n = st.sidebar.slider("Rows", min_value=10, max_value=1000, value=200, step=10)
    df = sample_data(n)
    st.subheader("Sample dataset")
    st.dataframe(df.head(50))
    st.subheader("Line chart")
    st.line_chart(df.set_index("x"))
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", data=csv, file_name="sample_data.csv", mime="text/csv")

elif mode == "Upload CSV":
    uploaded = st.file_uploader("Upload a CSV file", type=["csv"])
    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded)
            st.subheader("Preview")
            st.dataframe(df.head(100))
            numeric = df.select_dtypes(include=[np.number])
            if not numeric.empty:
                st.subheader("Numeric columns - line chart")
                st.line_chart(numeric)
            else:
                st.info("No numeric columns found for charting.")
            st.download_button("Download (unchanged)", data=df.to_csv(index=False).encode("utf-8"),
                               file_name="uploaded.csv", mime="text/csv")
        except Exception as e:
            st.error(f"Failed to read CSV: {e}")

else:  # Upload Image
    img_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
    if img_file is not None:
        try:
            img = Image.open(img_file)
            st.image(img, caption="Uploaded image", use_column_width=True)
            st.write("Image size:", img.size)
            # simple transform example
            if st.button("Convert to grayscale"):
                gray = img.convert("L")
                buf = io.BytesIO()
                gray.save(buf, format="PNG")
                st.image(gray, caption="Grayscale", use_column_width=True)
                st.download_button("Download grayscale", data=buf.getvalue(), file_name="grayscale.png", mime="image/png")
        except Exception as e:
            st.error(f"Failed to open image: {e}")

st.markdown("---")
st.caption("This is a starter Streamlit app. Modify streamlit_app.py to customize behavior.")