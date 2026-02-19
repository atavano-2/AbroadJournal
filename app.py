import os
import streamlit as st

st.set_page_config(page_title="Emily's Abroad Journal", layout = "centered")

st.title("Emily's Travel Journal")
st.write("Follow along with my adventures abroad!")

POSTS_DIR = "posts"

def list_posts():
    files = [f for f in os.listdir(POSTS_DIR) if f.endswith(".md")]
    files.sort(reverse = True)
    return files

def nice_title(filename: str) -> str:
    name = filename.replace(".md", "")
    parts = name.split("-")
    if len(parts) >= 4 and all(p.isdigit() for p in parts[:3]):
        name = " ".join(parts)

    else:
        name = " ".join(parts)

    return name.title()

posts = list_posts()
selected = st.sidebar.selectbox("Choose a post", posts, format_func=nice_title)
with open(os.path.join(POSTS_DIR,selected), "r", encoding ="utf-8") as f:
    content = f.read()

st.subheader(nice_title(selected))
st.markdown(content)


