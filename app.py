import streamlit as st
from supabase import create_client
from datetime import date
import uuid

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(page_title="Emily's Travel Journal", layout="wide")

# ---------------------------
# Aesthetic CSS (blush + editorial)
# ---------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

:root{
  --bg: #fbf4f3;
  --card: #ffffff;
  --ink: #1f2330;
  --muted: #6b7280;
  --line: rgba(31,35,48,0.08);
  --shadow: 0 10px 30px rgba(31,35,48,0.08);
  --radius: 18px;
}

html, body, [class*="css"]  {
  font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
  color: var(--ink);
}

.stApp {
  background: var(--bg);
}

/* Centered container feel */
.block-container {
  padding-top: 2.2rem;
  padding-bottom: 3rem;
  max-width: 1100px;
}

/* Sidebar polish */
section[data-testid="stSidebar"]{
  background: rgba(255,255,255,0.55);
  border-right: 1px solid var(--line);
}
section[data-testid="stSidebar"] .block-container{
  padding-top: 1.6rem;
}

/* Buttons */
.stButton>button, .stDownloadButton>button {
  border-radius: 999px;
  border: 1px solid var(--line);
  background: white;
  box-shadow: none;
  padding: 0.55rem 0.9rem;
}
.stButton>button:hover {
  box-shadow: 0 6px 20px rgba(31,35,48,0.08);
  transform: translateY(-1px);
}

/* Inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
  border-radius: 14px;
}

/* Hero title */
.hero-title {
  font-family: 'Playfair Display', serif;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: 0.35rem;
  font-size: 3rem;
  line-height: 1.05;
}
.hero-sub {
  color: var(--muted);
  margin-top: 0;
  margin-bottom: 1.5rem;
}

/* Card styles */
.card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  overflow: hidden;
  transition: transform .15s ease, box-shadow .15s ease;
}
.card:hover{
  transform: translateY(-3px);
  box-shadow: 0 16px 44px rgba(31,35,48,0.12);
}
.card-body{
  padding: 14px 16px 16px 16px;
}
.card-title{
  font-family: 'Playfair Display', serif;
  font-weight: 600;
  font-size: 1.15rem;
  margin: 0.1rem 0 0.25rem 0;
}
.card-meta{
  color: var(--muted);
  font-size: 0.9rem;
}
.pill{
  display: inline-block;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: rgba(255,255,255,0.65);
  font-size: 0.85rem;
  margin-right: 6px;
  margin-top: 8px;
  color: var(--ink);
}

/* Featured */
.feature-wrap{
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 22px;
  box-shadow: var(--shadow);
  overflow: hidden;
  margin-bottom: 1.25rem;
}
.feature-body{
  padding: 16px 18px 18px 18px;
}
.feature-title{
  font-family: 'Playfair Display', serif;
  font-weight: 700;
  font-size: 1.7rem;
  margin: 0 0 0.25rem 0;
}
.feature-meta{
  color: var(--muted);
  margin-bottom: 0.75rem;
}
hr.soft {
  border: 0;
  height: 1px;
  background: var(--line);
  margin: 1.2rem 0;
}

/* Post view */
.post-title{
  font-family: 'Playfair Display', serif;
  font-weight: 700;
  font-size: 2.2rem;
  margin-bottom: 0.25rem;
}
.post-meta{
  color: var(--muted);
  margin-bottom: 1rem;
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------
# Supabase setup (secrets)
# ---------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
SUPABASE_SERVICE_KEY = st.secrets["SUPABASE_SERVICE_KEY"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

TABLE_NAME = "Posts"

sb_public = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
sb_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# ---------------------------
# Session state
# ---------------------------
if "is_admin" not in st.session_state:
  st.session_state.is_admin = False
if "view" not in st.session_state:
  st.session_state.view = "home"  # home | post
if "selected_id" not in st.session_state:
  st.session_state.selected_id = None

# ---------------------------
# Helpers
# ---------------------------
def split_csv(s: str) -> list[str]:
  if not s:
    return []
  return [x.strip() for x in s.split(",") if x.strip()]

def get_cover_url(p: dict) -> str | None:
  cover = p.get("cover_image_url")
  if cover:
    return cover
  # fallback: first gallery url
  gallery = p.get("gallery_image_urls")
  urls = split_csv(gallery)
  return urls[0] if urls else None

def post_meta_line(p: dict) -> str:
  d = p.get("date") or ""
  loc = p.get("location") or ""
  if d and loc:
    return f"{d} • {loc}"
  return d or loc or ""

def fetch_posts(include_drafts: bool) -> list[dict]:
  if st.session_state.is_admin and include_drafts:
    q = sb_admin.table(TABLE_NAME).select("*").order("date", desc=True)
  else:
    q = (
      sb_public.table(TABLE_NAME)
      .select("*")
      .eq("is_published", True)
      .order("date", desc=True)
    )
  res = q.execute()
  return res.data or []

def open_post(post_id: str):
  st.session_state.selected_id = post_id
  st.session_state.view = "post"
  st.rerun()

def back_home():
  st.session_state.view = "home"
  st.session_state.selected_id = None
  st.rerun()

# ---------------------------
# Sidebar: Admin + Filters
# ---------------------------
with st.sidebar:
  st.subheader("Log In:")
  if not st.session_state.is_admin:
    pw = st.text_input("Enter Password", type="password")
    if st.button("Log in"):
      if pw == ADMIN_PASSWORD:
        st.session_state.is_admin = True
        st.success("Admin unlocked ✅")
        st.rerun()
      else:
        st.error("Wrong password")
  else:
    st.success("Admin mode ✅")
    if st.button("Log out"):
      st.session_state.is_admin = False
      st.rerun()

  st.divider()

  include_drafts = False
  if st.session_state.is_admin:
    include_drafts = st.checkbox("Show drafts", value=True)

  st.subheader("Search & filter")
  q_text = st.text_input("Search", placeholder="Try: Rome, museum, gelato…")

# Load posts once (after we know include_drafts)
posts = fetch_posts(include_drafts=include_drafts)

# Build title options
all_titles = sorted({(p.get("title") or "").strip() for p in posts if (p.get("title") or "").strip()})

with st.sidebar:
  title_choice = st.selectbox("Post title", options=["All"] + all_titles)

# Apply filters (title + search)
def matches(p: dict) -> bool:
  if title_choice != "All":
    if (p.get("title") or "").strip() != title_choice:
      return False

  if q_text.strip():
    q = q_text.strip().lower()
    blob = " ".join([
      str(p.get("title") or ""),
      str(p.get("location") or ""),
      str(p.get("tags") or ""),
      str(p.get("content") or ""),
      str(p.get("date") or ""),
    ]).lower()
    if q not in blob:
      return False

  return True

posts_filtered = [p for p in posts if matches(p)]

# ---------------------------
# Header (hero)
# ---------------------------
st.markdown('<div class="hero-title">Emily’s Travel Journal</div>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Follow along with my adventures abroad</p>', unsafe_allow_html=True)

# ---------------------------
# Admin: New post form (optional, lives on home)
# ---------------------------
if st.session_state.is_admin and st.session_state.view == "home":
  with st.expander("✍️ Create a new post", expanded=False):
    with st.form("new_post_form"):
      new_title = st.text_input("Title")
      new_date = st.date_input("Date", value=date.today())
      new_location = st.text_input("Location (optional)")
      new_tags = st.text_input("Tags (comma separated)", placeholder="food, museum, friends")
      new_cover = st.text_input("Cover image URL (optional)")
      new_gallery = st.text_input("Gallery image URLs (comma separated, optional)")
      new_content = st.text_area("Content", height=220)

      c1, c2 = st.columns(2)
      with c1:
        save_draft = st.form_submit_button("Save draft")
      with c2:
        publish = st.form_submit_button("Publish")

      if save_draft or publish:
        payload = {
          "id": str(uuid.uuid4()),
          "date": str(new_date),
          "title": new_title,
          "location": new_location,
          "tags": new_tags,
          "content": new_content,
          "cover_image_url": new_cover,
          "gallery_image_urls": new_gallery,
          "is_published": bool(publish),
        }
        sb_admin.table(TABLE_NAME).insert(payload).execute()
        st.success("Saved ✅")
        st.rerun()

# ---------------------------
# Views
# ---------------------------
if st.session_state.view == "post":
  # Find the selected post from our loaded list
  selected = next((p for p in posts if p.get("id") == st.session_state.selected_id), None)

  if not selected:
    st.warning("That post isn't available (it may be a draft, or was removed).")
    if st.button("← Back"):
      back_home()
  else:
    if st.button("← Back to home"):
      back_home()

    st.markdown(f'<div class="post-title">{selected.get("title") or "(untitled)"}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="post-meta">{post_meta_line(selected)}</div>', unsafe_allow_html=True)

    cover = get_cover_url(selected)
    if cover:
      st.image(cover, use_container_width=True)

    # Content
    st.markdown(selected.get("content") or "")

    # Gallery (optional)
    gallery_urls = split_csv(selected.get("gallery_image_urls") or "")
    if gallery_urls:
      st.markdown('<hr class="soft" />', unsafe_allow_html=True)
      st.subheader("Photos")
      # pretty gallery grid
      cols = st.columns(3)
      for i, url in enumerate(gallery_urls):
        with cols[i % 3]:
          st.image(url, use_container_width=True)

    # Tags / location
    loc = (selected.get("location") or "").strip()
    tags = split_csv(selected.get("tags") or "")
    pills = []
    if loc:
      pills.append(f"📍 {loc}")
    for t in tags[:6]:
      pills.append(f"🏷️ {t}")
    if pills:
      st.markdown('<hr class="soft" />', unsafe_allow_html=True)
      st.write(" ".join([f'<span class="pill">{p}</span>' for p in pills]), unsafe_allow_html=True)

else:
  # HOME view: Featured + grid of cards
  if not posts_filtered:
    st.info("No posts match your filters yet.")
  else:
    featured = posts_filtered[0]
    cover = get_cover_url(featured)

    # Featured block
    st.markdown('<div class="feature-wrap">', unsafe_allow_html=True)
    if cover:
      st.image(cover, use_container_width=True)
    st.markdown('<div class="feature-body">', unsafe_allow_html=True)
    st.markdown(f'<div class="feature-title">{featured.get("title") or "(untitled)"}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="feature-meta">{post_meta_line(featured)}</div>', unsafe_allow_html=True)

    preview = (featured.get("content") or "").strip()
    if len(preview) > 220:
      preview = preview[:220].rstrip() + "…"
    if preview:
      st.write(preview)

    if st.button("Read featured post →", key=f"read_featured_{featured.get('id')}"):
      open_post(featured.get("id"))

    st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown('<hr class="soft" />', unsafe_allow_html=True)

    # Grid of cards
    st.subheader("All posts")

    # 3-column grid (drops to 2/1 depending on screen)
    cols = st.columns(3)
    for i, p in enumerate(posts_filtered):
      cover = get_cover_url(p)
      with cols[i % 3]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        if cover:
          st.image(cover, use_container_width=True)
        st.markdown('<div class="card-body">', unsafe_allow_html=True)
        st.markdown(f'<div class="card-title">{p.get("title") or "(untitled)"}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="card-meta">{post_meta_line(p)}</div>', unsafe_allow_html=True)

        # tags pills (small)
        tags = split_csv(p.get("tags") or "")
        if tags:
          pills = "".join([f'<span class="pill">{t}</span>' for t in tags[:3]])
          st.markdown(pills, unsafe_allow_html=True)

        # draft badge for admin
        if st.session_state.is_admin and p.get("is_published") is False:
          st.markdown('<div class="card-meta" style="margin-top:8px;">📝 Draft</div>', unsafe_allow_html=True)

        if st.button("Open", key=f"open_{p.get('id')}"):
          open_post(p.get("id"))

        st.markdown('</div></div>', unsafe_allow_html=True)
        
