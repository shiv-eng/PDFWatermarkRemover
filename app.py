import streamlit as st
from streamlit_gsheets import GSheetsConnection
import fitz
import io
import uuid
from PIL import Image
from collections import Counter
import pandas as pd
from datetime import datetime
import pytz

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="PDF Watermark Remover",
    page_icon="💧",
    layout="wide"
)

# -------------------------------------------------
# COOKIES (PERSISTENT VISITOR ID)
# -------------------------------------------------
cookies = EncryptedCookieManager(
    prefix="pdfwm_",
    password="change-this-to-a-long-random-string"
)

if not cookies.ready():
    st.stop()

if "visitor_id" not in cookies:
    cookies["visitor_id"] = str(uuid.uuid4())

visitor_id = cookies["visitor_id"]

# -------------------------------------------------
# GOOGLE SHEETS
# -------------------------------------------------
conn = st.connection("gsheets", type=GSheetsConnection)

# -------------------------------------------------
# TIME (IST)
# -------------------------------------------------
def ist_now():
    return datetime.now(
        pytz.timezone("Asia/Kolkata")
    ).strftime("%d-%m-%Y %I:%M %p")

# -------------------------------------------------
# GLOBAL STATS (UX / DX)
# -------------------------------------------------
def get_stats():
    try:
        df = conn.read(worksheet="Stats", ttl=0)
        return int(df.iloc[0]["UX"]), int(df.iloc[0]["DX"])
    except:
        return 0, 0

def save_stats(ux, dx):
    df = pd.DataFrame([{"UX": ux, "DX": dx}])
    conn.update(worksheet="Stats", data=df)

# -------------------------------------------------
# VISITOR CLASSIFICATION
# -------------------------------------------------
def classify_user(row):
    last_seen = datetime.strptime(row["last_seen"], "%d-%m-%Y %I:%M %p")
    now = datetime.strptime(ist_now(), "%d-%m-%Y %I:%M %p")

    visits = int(row["visit_count"])
    downloads = int(row["download_count"])

    if visits >= 10 or downloads >= 5:
        return "power"
    if visits >= 3 and (now - last_seen).days == 0:
        return "daily"
    if visits >= 2 and (now - last_seen).days <= 7:
        return "weekly"
    return "new"

# -------------------------------------------------
# VISITOR TRACKING + UX COUNT
# -------------------------------------------------
def track_visitor(visitor_id):
    now = ist_now()

    try:
        df = conn.read(worksheet="Visitors", ttl=0)
    except:
        df = pd.DataFrame(columns=[
            "visitor_id", "first_seen", "last_seen",
            "visit_count", "download_count", "user_type"
        ])

    is_new_visitor = visitor_id not in df["visitor_id"].values

    if is_new_visitor:
        df = pd.concat([df, pd.DataFrame([{
            "visitor_id": visitor_id,
            "first_seen": now,
            "last_seen": now,
            "visit_count": 1,
            "download_count": 0,
            "user_type": "new"
        }])], ignore_index=True)
    else:
        idx = df.index[df["visitor_id"] == visitor_id][0]
        df.at[idx, "last_seen"] = now
        df.at[idx, "visit_count"] = int(df.at[idx, "visit_count"]) + 1
        df.at[idx, "user_type"] = classify_user(df.loc[idx])

    conn.update(worksheet="Visitors", data=df)

    return is_new_visitor

# -------------------------------------------------
# SESSION INIT
# -------------------------------------------------
if "ux_count" not in st.session_state:
    ux, dx = get_stats()
    st.session_state.ux_count = ux
    st.session_state.dx_count = dx

if "visitor_tracked" not in st.session_state:
    is_new = track_visitor(visitor_id)

    if is_new:
        st.session_state.ux_count += 1
        save_stats(st.session_state.ux_count, st.session_state.dx_count)

    st.session_state.visitor_tracked = True

# -------------------------------------------------
# CSS (UNCHANGED)
# -------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.ghost-counter {
    position: fixed;
    bottom: 10px;
    right: 15px;
    color: #D1D5DB;
    font-size: 0.65rem;
    font-family: monospace;
    opacity: 0.5;
}

.center-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
}

.hero-title {
    font-weight: 800;
    font-size: 3.5rem;
    background: linear-gradient(135deg, #2563EB, #06B6D4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    color: #6B7280;
    font-size: 1.2rem;
    margin-bottom: 2rem;
}

.feature-grid {
    display: flex;
    justify-content: center;
    gap: 4rem;
    margin-top: 2rem;
}

.feature-item { max-width: 250px; }

[data-testid="stFileUploader"] {
    background: #fff;
    border: 2px dashed #E5E7EB;
    border-radius: 20px;
    padding: 20px;
}

[data-testid="stExpander"] {
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    background: #FAFAFA;
}

.stDownloadButton > button {
    background: linear-gradient(135deg, #2563EB, #06B6D4);
    color: white;
    border: none;
    padding: 0.6rem 2rem;
    border-radius: 10px;
    font-weight: 600;
    width: 100%;
}

[data-testid="stHeader"], footer { display: none; }
.block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# PDF LOGIC (UNCHANGED)
# -------------------------------------------------
def detect_watermark_candidates(file_bytes):
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        counts = Counter()
        for i in range(min(5, len(doc))):
            page = doc[i]
            blocks = [b[4].strip() for b in page.get_text("blocks") if len(b[4].strip()) > 3]
            counts.update(blocks)
        return ", ".join([t for t, c in counts.items() if c >= 2])
    except:
        return ""

def clean_page(page, h_h, f_h, kw):
    if kw:
        for k in [s.strip() for s in kw.split(",") if s.strip()]:
            for quad in page.search_for(k):
                page.add_redact_annot(quad, fill=None)
        page.apply_redactions()

    r = page.rect
    pix = page.get_pixmap(clip=fitz.Rect(0, r.height - 10, 1, r.height - 9))
    color = tuple(c / 255 for c in pix.pixel(0, 0))

    if f_h > 0:
        page.draw_rect(fitz.Rect(0, r.height - f_h, r.width, r.height), color=color, fill=color)
    if h_h > 0:
        page.draw_rect(fitz.Rect(0, 0, r.width, h_h), color=color, fill=color)

# -------------------------------------------------
# DOWNLOAD CALLBACK (DX + per-user)
# -------------------------------------------------
def dx_callback():
    st.session_state.dx_count += 1
    save_stats(st.session_state.ux_count, st.session_state.dx_count)

    try:
        df = conn.read(worksheet="Visitors", ttl=0)
        idx = df.index[df["visitor_id"] == visitor_id][0]
        df.at[idx, "download_count"] = int(df.at[idx, "download_count"]) + 1
        df.at[idx, "last_seen"] = ist_now()
        df.at[idx, "user_type"] = classify_user(df.loc[idx])
        conn.update(worksheet="Visitors", data=df)
    except:
        pass

# -------------------------------------------------
# UI (UNCHANGED)
# -------------------------------------------------
st.markdown(
    f'<div class="ghost-counter">UX: {st.session_state.ux_count} | DX: {st.session_state.dx_count}</div>',
    unsafe_allow_html=True
)

st.markdown("""
<div class="center-wrapper">
    <div class="hero-title">PDF Watermark Remover</div>
    <div class="hero-subtitle">Clean, Professional, and Private Document Processing</div>
</div>
""", unsafe_allow_html=True)

_, uploader_col, _ = st.columns([1, 4, 1])
with uploader_col:
    uploaded_file = st.file_uploader("Upload", type="pdf", label_visibility="collapsed")

if uploaded_file:
    sig = f"{uploaded_file.name}_{uploaded_file.size}"

    if st.session_state.get("last_sig") != sig:
        st.session_state.ux_count += 1
        save_stats(st.session_state.ux_count, st.session_state.dx_count)
        st.session_state.last_sig = sig
        st.session_state.detected_text = detect_watermark_candidates(uploaded_file.getvalue())
        st.rerun()

    col_s, col_p = st.columns([3, 2], gap="large")
    uid = uuid.uuid4().hex

    with col_s:
        with st.expander("Advanced Options", expanded=False):
            txt = st.text_input("Keywords", value=st.session_state.get("detected_text", ""), key=f"t_{uid}")
            h_h = st.slider("Top Cut", 0, 150, 0, key=f"h_{uid}")
            f_h = st.slider("Bottom Cut", 0, 150, 25, key=f"f_{uid}")

        doc = fitz.open(stream=uploaded_file.getvalue(), filetype="pdf")
        out_buf = io.BytesIO()
        for page in doc:
            clean_page(page, h_h, f_h, txt)
        doc.save(out_buf)

        st.download_button(
            "📥 Download Clean PDF",
            data=out_buf.getvalue(),
            file_name=f"Clean_{uploaded_file.name}",
            on_click=dx_callback
        )

    with col_p:
        prev = fitz.open(stream=uploaded_file.getvalue(), filetype="pdf")
        p0 = prev[0]
        clean_page(p0, h_h, f_h, txt)
        st.image(Image.open(io.BytesIO(p0.get_pixmap(dpi=100).tobytes("png"))), use_container_width=True)

else:
    st.markdown("""
    <div class="feature-grid">
        <div class="feature-item"><h3>⚡ Auto-Detect</h3><p style="color:#6B7280;">Identifies repetitive text automatically.</p></div>
        <div class="feature-item"><h3>🎨 Smart Fill</h3><p style="color:#6B7280;">Replaces removed areas with background color.</p></div>
        <div class="feature-item"><h3>🛡️ Private</h3><p style="color:#6B7280;">Files are processed in memory only.</p></div>
    </div>
    """, unsafe_allow_html=True)
# --- FOOTER ---
st.markdown("""
<div style="text-align: center; margin-top: 60px; border-top: 1px solid #E5E7EB; padding-top: 20px;">
    <img src="https://visitor-badge.laobi.icu/badge?page_id=pdfwatermarkremover.streamlit.app&left_text=Total%20Visits&left_color=%231F2937&right_color=%232563EB" alt="Visitor Count">
</div>
""", unsafe_allow_html=True)
