import streamlit as st
from streamlit_gsheets import GSheetsConnection
import fitz  # PyMuPDF
import io
import uuid
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
# This connection uses the secrets you pasted in the dashboard
conn = st.connection("gsheets", type=GSheetsConnection)

def get_stats():
    """Fetch UX/DX counts from Google Sheets."""
    try:
        # ttl=0 is vital to ensure we don't show old cached numbers
        df = conn.read(worksheet="Stats", ttl=0)
        return int(df.iloc[0]["UX"]), int(df.iloc[0]["DX"])
    except Exception:
        # Fallback to avoid crashing the UI if Google is slow
        return 0, 0

def save_stats(ux, dx):
    """Update Google Sheets with new counts."""
    try:
        df = pd.DataFrame([{"UX": ux, "DX": dx}])
        conn.update(worksheet="Stats", data=df)
    except Exception:
        pass

# Initialize Session State on first load
if 'ux_count' not in st.session_state:
    ux, dx = get_stats()
    st.session_state.ux_count = ux
    st.session_state.dx_count = dx

# --- 3. CSS STYLING (LOCKED CENTER UI) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* GHOST COUNTER - PINNED TO BOTTOM RIGHT */
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

    .hero-container { text-align: center; margin-bottom: 2rem; margin-top: 2rem; }
    .hero-title { 
        font-weight: 800; 
        background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%); 
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        font-size: 3.5rem; 
        margin-bottom: 0.5rem; 
    }
    .hero-subtitle { color: #6B7280; font-size: 1.2rem; }

    [data-testid="stFileUploader"] { 
        background-color: #FFFFFF; 
        border: 2px dashed #E5E7EB; 
        border-radius: 20px; 
        padding: 20px; 
    }
    
    .feature-grid { 
        display: flex; 
        justify-content: center; 
        gap: 3rem; 
        text-align: center; 
        margin-top: 3rem; 
    }
    .feature-item { max-width: 250px; }
    
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
    .block-container { padding-top: 1rem !important; }
    </style>
""", unsafe_allow_html=True)

# --- 4. CORE PDF LOGIC ---

def detect_watermark_candidates(file_bytes):
    """Scans first 5 pages for repetitive text blocks."""
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text_counts = Counter()
        for i in range(min(5, len(doc))):
            page = doc[i]
            blocks = [b[4].strip() for b in page.get_text("blocks") if len(b[4].strip()) > 3]
            text_counts.update(blocks)
        return ", ".join([t for t, c in text_counts.items() if c >= 2])
    except:
        return ""

def clean_page(page, h_h, f_h, kw):
    """Removes keywords and wipes margins with smart-fill color."""
    if kw:
        for k in [s.strip() for s in kw.split(',') if s.strip()]:
            for quad in page.search_for(k):
                page.add_redact_annot(quad, fill=None)
        page.apply_redactions()
    
    # Detect background color for margins (Smart Fill)
    r = page.rect
    pix = page.get_pixmap(clip=fitz.Rect(0, r.height-10, 1, r.height-9))
    color = (pix.pixel(0, 0)[0]/255, pix.pixel(0, 0)[1]/255, pix.pixel(0, 0)[2]/255)
    
    if f_h > 0:
        page.draw_rect(fitz.Rect(0, r.height - f_h, r.width, r.height), color=color, fill=color)
    if h_h > 0:
        page.draw_rect(fitz.Rect(0, 0, r.width, h_h), color=color, fill=color)

# --- 5. UI LAYOUT ---

# Hidden Persistent Counter
st.markdown(f'<div class="ghost-counter">UX: {st.session_state.ux_count} | DX: {st.session_state.dx_count}</div>', unsafe_allow_html=True)

# Centered Hero Section
st.markdown("""
<div class="hero-container">
    <div class="hero-title">PDF Watermark Remover</div>
    <div class="hero-subtitle">Clean, Professional, and Private Document Processing</div>
</div>
""", unsafe_allow_html=True)

# Centered Uploader
_, uploader_col, _ = st.columns([1, 3, 1])
with uploader_col:
    uploaded_file = st.file_uploader("Upload", type="pdf", label_visibility="collapsed")

if uploaded_file:
    # Handle New File Uploads
    sig = f"{uploaded_file.name}_{uploaded_file.size}"
    if st.session_state.get("last_sig") != sig:
        st.session_state.ux_count += 1
        save_stats(st.session_state.ux_count, st.session_state.dx_count)
        st.session_state.last_sig = sig
        st.session_state.detected_text = detect_watermark_candidates(uploaded_file.getvalue())
        st.rerun()

    # Document Editor Container
    with st.container(border=True):
        col_settings, col_preview = st.columns([3, 2], gap="large")
        uid = uuid.uuid4().hex
        
        with col_settings:
            st.subheader("🛠️ Settings")
            txt = st.text_input("Keywords (comma separated)", value=st.session_state.get("detected_text", ""), key=f"t_{uid}")
            top_cut = st.slider("Top Margin Cut", 0, 150, 0, key=f"h_{uid}")
            bot_cut = st.slider("Bottom Margin Cut", 0, 150, 25, key=f"f_{uid}")
            
            # Prepare Clean PDF
            doc_full = fitz.open(stream=uploaded_file.getvalue(), filetype="pdf")
            out_buffer = io.BytesIO()
            for page in doc_full:
                clean_page(page, top_cut, bot_cut, txt)
            doc_full.save(out_buffer)
            
            st.download_button(
                "📥 Download Clean PDF", 
                data=out_buffer.getvalue(), 
                file_name=f"Clean_{uploaded_file.name}",
                on_click=lambda: (st.session_state.update(dx_count=st.session_state.dx_count+1), save_stats(st.session_state.ux_count, st.session_state.dx_count))
            )
        
        with col_preview:
            st.subheader("👁️ Preview")
            doc_prev = fitz.open(stream=uploaded_file.getvalue(), filetype="pdf")
            page0 = doc_prev[0]
            clean_page(page0, top_cut, bot_cut, txt)
            st.image(Image.open(io.BytesIO(page0.get_pixmap(dpi=100).tobytes("png"))), use_container_width=True)

else:
    # Feature icons - Shown when no file is uploaded
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

# Visitor Badge Footer
st.markdown(f"""
<div style="text-align: center; margin-top: 4rem;">
    <img src="https://visitor-badge.laobi.icu/badge?page_id=pdfwatermarkremover.streamlit.app">
</div>
""", unsafe_allow_html=True)
