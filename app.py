import streamlit as st
from streamlit_gsheets import GSheetsConnection
import fitz  # PyMuPDF
import io
import uuid
import time
from PIL import Image
from collections import Counter
import pandas as pd

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="PDF Watermark Remover",
    page_icon="💧", 
    layout="wide"
)

# --- 2. PERSISTENT DATABASE CONNECTION ---
# Added try-except to prevent app crash if connection fails
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
            conn.update(worksheet="Stats", data=df)
        except Exception:
            pass

# Initialize Session State
if 'ux_count' not in st.session_state:
    ux, dx = get_stats()
    st.session_state.ux_count = ux
    st.session_state.dx_count = dx

# --- 3. CSS STYLING (FORCE CENTER ALIGNMENT) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    /* Global Styles */
    html, body, [class*="css"] { 
        font-family: 'Inter', sans-serif; 
    }

    /* Fixed Ghost Counter at Bottom Right */
    .ghost-counter {
        position: fixed !important;
        bottom: 10px !important;
        right: 15px !important;
        color: #D1D5DB !important;
        font-size: 0.65rem !important;
        font-family: monospace !important;
        z-index: 999999 !important;
        pointer-events: none !important;
        user-select: none !important;
        opacity: 0.5;
    }

    /* Center Container for Title and Icons */
    .center-wrapper {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        width: 100%;
    }

    .hero-title { 
        font-weight: 800; 
        background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%); 
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        font-size: 3.5rem; 
        margin-top: 1rem;
        margin-bottom: 0.5rem; 
    }

    .hero-subtitle { 
        color: #6B7280; 
        font-size: 1.2rem; 
        margin-bottom: 2rem;
    }

    /* Styling for the three feature sections */
    .feature-grid {
        display: flex;
        justify-content: center;
        gap: 4rem;
        margin-top: 2rem;
        width: 100%;
    }

    .feature-item {
        max-width: 250px;
    }

    [data-testid="stFileUploader"] {
        background-color: #FFFFFF;
        border: 2px dashed #E5E7EB;
        border-radius: 20px;
        padding: 20px;
    }

    [data-testid="stExpander"] {
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        background-color: #FAFAFA;
    }

    .stDownloadButton > button {
        background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%);
        color: white !important;
        border: none;
        padding: 0.6rem 2rem;
        border-radius: 10px;
        font-weight: 600;
        width: 100%;
    }

    [data-testid="stHeader"], footer { display: none !important; }
    .block-container { padding-top: 2rem !important; }
    </style>
""", unsafe_allow_html=True)

# --- 4. CORE LOGIC ---

def detect_watermark_candidates(file_bytes):
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        counts = Counter()
        for i in range(min(5, len(doc))):
            page = doc[i]
            blocks = [b[4].strip() for b in page.get_text("blocks") if len(b[4].strip()) > 3]
            counts.update(blocks)
        return ", ".join([t for t, c in counts.items() if c >= 2])
    except: return ""

def clean_page(page, h_h, f_h, kw):
    if kw:
        for k in [s.strip() for s in kw.split(',') if s.strip()]:
            for quad in page.search_for(k): page.add_redact_annot(quad, fill=None)
        page.apply_redactions()
    r = page.rect
    pix = page.get_pixmap(clip=fitz.Rect(0, r.height-10, 1, r.height-9))
    color = (pix.pixel(0, 0)[0]/255, pix.pixel(0, 0)[1]/255, pix.pixel(0, 0)[2]/255)
    if f_h > 0: page.draw_rect(fitz.Rect(0, r.height - f_h, r.width, r.height), color=color, fill=color)
    if h_h > 0: page.draw_rect(fitz.Rect(0, 0, r.width, h_h), color=color, fill=color)

def dx_callback():
    st.session_state.dx_count += 1
    save_stats(st.session_state.ux_count, st.session_state.dx_count)

# --- 5. UI LAYOUT ---

# Ghost Counter (Bottom Right)
st.markdown(f'<div class="ghost-counter">UX: {st.session_state.ux_count} | DX: {st.session_state.dx_count}</div>', unsafe_allow_html=True)

# Centered Title and Subtitle
st.markdown("""
<div class="center-wrapper">
    <div class="hero-title">PDF Watermark Remover</div>
    <div class="hero-subtitle">Clean, Professional, and Private Document Processing</div>
</div>
""", unsafe_allow_html=True)

# Center the Uploader using Streamlit Columns
_, uploader_col, _ = st.columns([1, 4, 1])
with uploader_col:
    uploaded_file = st.file_uploader("Upload", type="pdf", label_visibility="collapsed")

if uploaded_file:
    # Update UX stats on new file
    file_sig = f"{uploaded_file.name}_{uploaded_file.size}"
    if st.session_state.get("last_sig") != file_sig:
        st.session_state.ux_count += 1
        save_stats(st.session_state.ux_count, st.session_state.dx_count)
        st.session_state.last_sig = file_sig
        st.session_state.detected_text = detect_watermark_candidates(uploaded_file.getvalue())
        st.rerun()

    # Document Editor Interface
    with st.container(border=True):
        col_s, col_p = st.columns([3, 2], gap="large")
        uid = uuid.uuid4().hex
        with col_s:
            st.subheader("🛠️ Settings")
            with st.expander("Advanced Options", expanded=False):
                txt = st.text_input("Keywords", value=st.session_state.get("detected_text", ""), key=f"t_{uid}")
                h_h = st.slider("Top Cut", 0, 150, 0, key=f"h_{uid}")
                f_h = st.slider("Bottom Cut", 0, 150, 25, key=f"f_{uid}")
            
            doc = fitz.open(stream=uploaded_file.getvalue(), filetype="pdf")
            out_buf = io.BytesIO()
            for page in doc: clean_page(page, h_h, f_h, txt)
            doc.save(out_buf)
            st.download_button("📥 Download Clean PDF", data=out_buf.getvalue(), file_name=f"Clean_{uploaded_file.name}", on_click=dx_callback)
        
        with col_p:
            st.subheader("👁️ Preview")
            doc_prev = fitz.open(stream=uploaded_file.getvalue(), filetype="pdf")
            page0 = doc_prev[0]
            clean_page(page0, h_h, f_h, txt)
            st.image(Image.open(io.BytesIO(page0.get_pixmap(dpi=100).tobytes("png"))), use_container_width=True)

else:
    # Centered Feature Grid (only shows when no file is uploaded)
    st.markdown("""
    <div class="feature-grid">
        <div class="feature-item">
            <h3>⚡ Auto-Detect</h3>
            <p style="color: #6B7280;">Identifies repetitive text automatically.</p>
        </div>
        <div class="feature-item">
            <h3>🎨 Smart Fill</h3>
            <p style="color: #6B7280;">Replaces removed areas with background color.</p>
        </div>
        <div class="feature-item">
            <h3>🛡️ Private</h3>
            <p style="color: #6B7280;">Files are processed in memory only.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Footer Visitor Badge
st.markdown("""
<div style="text-align: center; margin-top: 5rem; border-top: 1px solid #E5E7EB; padding-top: 2rem;">
    <img src="https://visitor-badge.laobi.icu/badge?page_id=pdfwatermarkremover.streamlit.app&left_text=Total%20Visits&left_color=%231F2937&right_color=%232563EB">
</div>
""", unsafe_allow_html=True)
