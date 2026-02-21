import os
import streamlit as st

st.set_page_config(page_title="Emily's Abroad Journal", layout = "centered")

st.title("Emily's Travel Journal!")
st.write("Follow along with my adventures abroad")

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

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

with st.sidebar:
    st.subheader("Admin")

    if not st.session_state.is_admin:
        pw = st.text_input('Admin Password', type= 'password')
        if st.button("Log in"):
            if pw == st.secrets['ADMIN PASSWORD']:
                st.session_state.is_admin = True
                st.success("Admin Unlocked")
                st.rerun()

            else:
                st.error("Wrong Password")
    else:
        st.success('Admin Mode')
        if st.button("Log out"):
            st.session_state.is_admin = False
            st.rerun()
    st.divider()
with st.sidebar:
    if st.session_state.is_admin:
        st.write("Admin controls go here")
        
st.subheader(nice_title(selected))
st.markdown(content)


