import streamlit as st
from streamlit_gsheets import GSheetsConnection
import fitz  # PyMuPDF
import io
import uuid
from PIL import Image
from collections import Counter
import pandas as pd
st.write("Secrets loaded:", "gsheets" in st.secrets)
st.write("Secrets keys:", list(st.secrets.keys()))

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="PDF Watermark Remover",
    page_icon="💧",
    layout="wide"
)

# --- 2. PERSISTENT DATABASE CONNECTION ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception:
    conn = None

def get_stats():
    if conn:
        try:
            df = conn.read(worksheet="Stats", ttl=0)
            return int(df.iloc[0]["UX"]), int(df.iloc[0]["DX"])
        except Exception:
            return 0, 0
    return 0, 0

def save_stats(ux, dx):
    if conn:
        try:
            df = pd.DataFrame([{"UX": ux, "DX": dx}])
            conn.update(
                worksheet="Stats",
                data=df,
                mode="replace"   # 🔑 REQUIRED FIX
            )
        except Exception as e:
            st.error(f"GSheets write failed: {e}")

# --- SESSION STATE INIT ---
if "ux_count" not in st.session_state:
    ux, dx = get_stats()
    st.session_state.ux_count = ux
    st.session_state.dx_count = dx

# --- 3. CSS STYLING ---
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
    z-index: 999999;
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
    background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3.5rem;
    margin-top: 1rem;
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

.stDownloadButton > button {
    background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%);
    color: white;
    border-radius: 10px;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# --- 4. CORE LOGIC ---

def detect_watermark_candidates(file_bytes):
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        counts = Counter()
        for i in range(min(5, len(doc))):
            page = doc[i]
            blocks = [
                b[4].strip()
                for b in page.get_text("blocks")
                if len(b[4].strip()) > 3
            ]
            counts.update(blocks)
        return ", ".join([t for t, c in counts.items() if c >= 2])
    except Exception:
        return ""

def clean_page(page, h_h, f_h, kw):
    if kw:
        for k in [s.strip() for s in kw.split(",") if s.strip()]:
            for quad in page.search_for(k):
                page.add_redact_annot(quad, fill=None)
        page.apply_redactions()

    r = page.rect
    pix = page.get_pixmap(clip=fitz.Rect(0, r.height-10, 1, r.height-9))
    color = tuple(c/255 for c in pix.pixel(0, 0))

    if f_h > 0:
        page.draw_rect(
            fitz.Rect(0, r.height - f_h, r.width, r.height),
            color=color, fill=color
        )

    if h_h > 0:
        page.draw_rect(
            fitz.Rect(0, 0, r.width, h_h),
            color=color, fill=color
        )

def dx_callback():
    st.session_state.dx_count += 1
    save_stats(st.session_state.ux_count, st.session_state.dx_count)

# --- 5. UI ---

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

    with st.container(border=True):
        col_s, col_p = st.columns([3, 2])
        uid = uuid.uuid4().hex

        with col_s:
            st.subheader("🛠️ Settings")
            with st.expander("Advanced Options"):
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
            st.subheader("👁️ Preview")
            prev = fitz.open(stream=uploaded_file.getvalue(), filetype="pdf")
            p0 = prev[0]
            clean_page(p0, h_h, f_h, txt)
            st.image(
                Image.open(io.BytesIO(p0.get_pixmap(dpi=100).tobytes("png"))),
                use_container_width=True
            )

else:
    st.markdown("""
    <div class="feature-grid">
        <div class="feature-item"><h3>⚡ Auto-Detect</h3><p>Identifies repetitive text.</p></div>
        <div class="feature-item"><h3>🎨 Smart Fill</h3><p>Matches background color.</p></div>
        <div class="feature-item"><h3>🛡️ Private</h3><p>In-memory processing only.</p></div>
    </div>
    """, unsafe_allow_html=True)
