import streamlit as st
from streamlit_gsheets import GSheetsConnection
import fitz  # PyMuPDF
import io
import uuid
from PIL import Image
from collections import Counter
import pandas as pd

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="PDF Watermark Remover", page_icon="💧", layout="wide")

# --- 2. DATABASE CONNECTION ---
# Establishing connection once at start
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception:
    conn = None

def get_stats():
    if conn:
        try:
            df = conn.read(worksheet="Stats", ttl=0)
            return int(df.iloc[0]["UX"]), int(df.iloc[0]["DX"])
        except Exception: pass
    return 0, 0

def save_stats(ux, dx):
    if conn:
        try:
            df = pd.DataFrame([{"UX": ux, "DX": dx}])
            conn.update(worksheet="Stats", data=df)
        except Exception: pass

# Sync State
if 'ux_count' not in st.session_state:
    ux, dx = get_stats()
    st.session_state.ux_count, st.session_state.dx_count = ux, dx

# --- 3. CSS STYLING (LOCKED CENTER UI) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .ghost-counter {
        position: fixed !important; bottom: 10px !important; right: 15px !important;
        color: #D1D5DB !important; font-size: 0.65rem !important;
        font-family: monospace !important; z-index: 999999 !important;
        pointer-events: none !important; user-select: none !important; opacity: 0.5;
    }

    .hero-container { text-align: center; margin-bottom: 2rem; margin-top: 1rem; }
    .hero-title { 
        font-weight: 800; background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%); 
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
        font-size: 3.5rem; margin-bottom: 0.5rem; 
    }
    .hero-subtitle { color: #6B7280; font-size: 1.2rem; }

    [data-testid="stFileUploader"] { background-color: #FFFFFF; border: 2px dashed #E5E7EB; border-radius: 20px; padding: 20px; }
    
    .feature-grid { display: flex; justify-content: center; gap: 4rem; text-align: center; margin-top: 3rem; }
    .feature-item { max-width: 250px; }
    
    .stDownloadButton > button {
        background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%);
        color: white !important; border: none; padding: 0.6rem 2rem;
        border-radius: 10px; font-weight: 600; width: 100%;
    }
    
    [data-testid="stHeader"], footer { display: none !important; }
    .block-container { padding-top: 1rem !important; }
    </style>
""", unsafe_allow_html=True)

# --- 4. CORE LOGIC ---
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

# --- 5. UI LAYOUT ---
st.markdown(f'<div class="ghost-counter">UX: {st.session_state.ux_count} | DX: {st.session_state.dx_count}</div>', unsafe_allow_html=True)

st.markdown('<div class="hero-container"><div class="hero-title">PDF Watermark Remover</div><div class="hero-subtitle">Clean, Professional, and Private Document Processing</div></div>', unsafe_allow_html=True)

_, uploader_col, _ = st.columns([1, 3, 1])
with uploader_col:
    uploaded_file = st.file_uploader("Upload", type="pdf", label_visibility="collapsed")

if uploaded_file:
    sig = f"{uploaded_file.name}_{uploaded_file.size}"
    if st.session_state.get("last_sig") != sig:
        st.session_state.ux_count += 1
        save_stats(st.session_state.ux_count, st.session_state.dx_count)
        st.session_state.last_sig = sig
        st.rerun()

    with st.container(border=True):
        col_s, col_p = st.columns([3, 2], gap="large")
        with col_s:
            st.subheader("🛠️ Settings")
            txt = st.text_input("Keywords (comma separated)")
            h_h = st.slider("Top Cut", 0, 150, 0)
            f_h = st.slider("Bottom Cut", 0, 150, 25)
            
            doc = fitz.open(stream=uploaded_file.getvalue(), filetype="pdf")
            out = io.BytesIO()
            for page in doc: clean_page(page, h_h, f_h, txt)
            doc.save(out)
            
            st.download_button(
                "📥 Download Clean PDF", 
                data=out.getvalue(), 
                file_name=f"Clean_{uploaded_file.name}",
                on_click=lambda: (st.session_state.update(dx_count=st.session_state.dx_count+1), save_stats(st.session_state.ux_count, st.session_state.dx_count))
            )
        
        with col_p:
            st.subheader("👁️ Preview")
            doc_p = fitz.open(stream=uploaded_file.getvalue(), filetype="pdf")
            page0 = doc_p[0]
            clean_page(page0, h_h, f_h, txt)
            st.image(Image.open(io.BytesIO(page0.get_pixmap(dpi=100).tobytes("png"))), use_container_width=True)
else:
    st.markdown("""
    <div class="feature-grid">
        <div class="feature-item"><h3>⚡ Auto-Detect</h3><p>Identifies repetitive text automatically.</p></div>
        <div class="feature-item"><h3>🎨 Smart Fill</h3><p>Replaces removed areas with background color.</p></div>
        <div class="feature-item"><h3>🛡️ Private</h3><p>Files are processed in memory only.</p></div>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f'<div style="text-align: center; margin-top: 4rem;"><img src="https://visitor-badge.laobi.icu/badge?page_id=pdfwatermarkremover.streamlit.app"></div>', unsafe_allow_html=True)
