import streamlit as st
from supabase import create_client
from datetime import date
import uuid

st.set_page_config(page_title="Emily's Abroad Journal", layout="centered")

st.title("Emily's Travel Journal!")
st.write("Follow along with my adventures abroad")

# ---------------------------
# Supabase setup (from secrets)
# ---------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
SUPABASE_SERVICE_KEY = st.secrets["SUPABASE_SERVICE_KEY"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

TABLE_NAME = "Posts"  # IMPORTANT: your table is capital P based on your screenshot

sb_public = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
sb_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# ---------------------------
# Admin gate (session state)
# ---------------------------
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# ---------------------------
# Helpers
# ---------------------------
def format_post_label(p: dict) -> str:
    """How each post appears in the dropdown."""
    d = p.get("date") or ""
    t = p.get("title") or "(untitled)"
    loc = p.get("location") or ""
    label = f"{d} — {t}"
    if loc:
        label += f" ({loc})"
    if p.get("is_published") is False:
        label += " [DRAFT]"
    return label

def fetch_posts(include_drafts: bool) -> list[dict]:
    """
    Public: use anon key + only published (RLS should enforce too)
    Admin: use service key + optionally include drafts
    """
    if st.session_state.is_admin and include_drafts:
        client = sb_admin
        q = client.table(TABLE_NAME).select("*").order("date", desc=True)
    else:
        client = sb_public
        q = (
            client.table(TABLE_NAME)
            .select("*")
            .eq("is_published", True)
            .order("date", desc=True)
        )

    res = q.execute()
    return res.data or []

# ---------------------------
# Sidebar UI (dropdown + admin login)
# ---------------------------
with st.sidebar:
    st.header("Menu")

    st.subheader("Admin")
    if not st.session_state.is_admin:
        pw = st.text_input("Admin Password", type="password")
        if st.button("Log in"):
            if pw == ADMIN_PASSWORD:
                st.session_state.is_admin = True
                st.success("Admin Unlocked ✅")
                st.rerun()
            else:
                st.error("Wrong Password")
    else:
        st.success("Admin Mode ✅")
        if st.button("Log out"):
            st.session_state.is_admin = False
            st.rerun()

    st.divider()

    include_drafts = False
    if st.session_state.is_admin:
        include_drafts = st.checkbox("Show drafts too", value=True)

# ---------------------------
# Load posts from Supabase
# ---------------------------
posts = fetch_posts(include_drafts=include_drafts)

with st.sidebar:
    st.subheader("Choose a post")

    if not posts:
        st.info("No posts yet.")
        selected_post = None
    else:
        # Keep selection stable using id
        options = posts
        selected_post = st.selectbox(
            label="",
            options=options,
            format_func=format_post_label,
        )

# ---------------------------
# Admin controls (create new post)
# ---------------------------
if st.session_state.is_admin:
    with st.sidebar:
        st.divider()
        st.subheader("New post")

        with st.form("new_post_form"):
            new_title = st.text_input("Title")
            new_date = st.date_input("Date", value=date.today())
            new_location = st.text_input("Location (optional)")
            new_tags = st.text_input("Tags (comma separated)", placeholder="food, museum, friends")
            new_content = st.text_area("Content", height=200)

            c1, c2 = st.columns(2)
            with c1:
                save_draft = st.form_submit_button("Save Draft")
            with c2:
                publish = st.form_submit_button("Publish")

            if save_draft or publish:
                payload = {
                    "id": str(uuid.uuid4()),
                    "date": str(new_date),
                    "title": new_title,
                    "location": new_location,
                    "tags": new_tags,  # your column is text in your table
                    "content": new_content,
                    "is_published": bool(publish),
                }

                sb_admin.table(TABLE_NAME).insert(payload).execute()
                st.success("Saved ✅")
                st.rerun()

# ---------------------------
# Main page: display selected post
# ---------------------------
if selected_post is None:
    st.write("")
    st.info("Add your first post in Supabase or (if you're admin) using the form in the sidebar.")
else:
    st.subheader(format_post_label(selected_post))

    # Optional cover image
    cover = selected_post.get("cover_image_url")
    if cover:
        st.image(cover, use_container_width=True)

    # Content
    st.markdown(selected_post.get("content") or "")

    # Optional tags/location display
    loc = selected_post.get("location")
    tags = selected_post.get("tags")
    if loc or tags:
        st.caption(f"{'📍 ' + loc if loc else ''}{' | ' if loc and tags else ''}{'🏷️ ' + tags if tags else ''}")