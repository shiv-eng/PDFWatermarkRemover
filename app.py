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
# This replaces your old local JSON saving logic with Cloud GSheets [cite: 13, 21]
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Connection Error: Please check your Secrets formatting.")
    conn = None

def get_stats():
    """Fetches UX/DX counts from your Google Sheet [cite: 22, 110]"""
    if conn:
        try:
            df = conn.read(worksheet="Stats", ttl=0)
            return int(df.iloc[0]["UX"]), int(df.iloc[0]["DX"])
        except:
            return 0, 0
    return 0, 0

def save_stats(ux, dx):
    """Saves counts permanently so they don't reset [cite: 30, 83]"""
    if conn:
        try:
            df = pd.DataFrame([{"UX": ux, "DX": dx}])
            conn.update(worksheet="Stats", data=df)
        except:
            pass

# Initialize and Sync Stats
if 'ux_count' not in st.session_state:
    ux, dx = get_stats()
    st.session_state.ux_count, st.session_state.dx_count = ux, dx

# --- 3. CSS STYLING (Restored Original UI & Centering) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* GHOST COUNTER - Fixed to bottom right [cite: 3, 5] */
    .ghost-counter {
        position: fixed !important;
        bottom: 15px !important;
        right: 15px !important;
        color: #D1D5DB !important;
        font-size: 0.75rem !important;
        font-weight: 500 !important;
        z-index: 9999;
        pointer-events: none;
        user-select: none;
        letter-spacing: 0.05em;
        opacity: 0.6;
    }

    /* Hero & Centering Logic  */
    .hero-container { text-align: center; margin-bottom: 40px; padding: 20px 0; }
    .hero-title { 
        font-weight: 800; 
        background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%); 
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        font-size: 3.5rem; 
        margin-bottom: 8px; 
    }
    .hero-subtitle { color: #6B7280; font-size: 1.2rem; margin-bottom: 5px;}

    [data-testid="stFileUploader"] { 
        background-color: #FFFFFF; 
        border: 2px dashed #E5E7EB; 
        border-radius: 20px; 
        padding: 30px; 
    }

    .feature-box { text-align: center; padding: 1rem; }
    
    /* Download Button Style */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%);
        color: white !important;
        border: none;
        padding: 0.6rem 2rem;
        border-radius: 10px;
        font-weight: 600;
        width: 100%;
    }

    /* Hide default Streamlit elements to keep UI clean */
    [data-testid="stHeader"], footer { display: none !important; }
    .block-container { padding-top: 2rem !important; }
    </style>
""", unsafe_allow_html=True)

# --- 4. CORE PDF LOGIC (Full Original Logic Restored) ---

def detect_watermark_candidates(file_bytes):
    """The Auto-Detect Feature: Scans pages for repetitive text [cite: 5, 7]"""
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        page_limit = min(5, len(doc))
        text_counts = Counter()
        for i in range(page_limit):
            page = doc[i]
            blocks = [b[4].strip() for b in page.get_text("blocks") if len(b[4].strip()) > 3]
            text_counts.update(blocks)
        # Identify text appearing on almost every page
        threshold = max(2, page_limit - 1)
        return ", ".join([text for text, count in text_counts.items() if count >= threshold])
    except:
        return ""

def clean_page_logic(page, header_h, footer_h, keywords_str):
    """The Smart-Fill & Keyword Removal Logic [cite: 1, 7]"""
    if keywords_str:
        keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
        for keyword in keywords:
            for quad in page.search_for(keyword):
                page.add_redact_annot(quad, fill=None)
        page.apply_redactions()

    # Smart Background Color Detection for Filling Margins
    rect = page.rect
    pix = page.get_pixmap(clip=fitz.Rect(0, rect.height-10, 1, rect.height-9))
    r, g, b = pix.pixel(0, 0)
    dynamic_color = (r/255, g/255, b/255)

    if footer_h > 0:
        page.draw_rect(fitz.Rect(0, rect.height - footer_h, rect.width, rect.height), 
                       color=dynamic_color, fill=dynamic_color)
    if header_h > 0:
        page.draw_rect(fitz.Rect(0, 0, rect.width, header_h), 
                       color=dynamic_color, fill=dynamic_color)

# --- 5. UI LAYOUT ---

# Hidden Persistent Counter in Bottom Right
st.markdown(f'<div class="ghost-counter">UX: {st.session_state.ux_count} | DX: {st.session_state.dx_count}</div>', unsafe_allow_html=True)

st.markdown("""
<div class="hero-container">
    <div class="hero-title">PDF Watermark Remover</div>
    <div class="hero-subtitle">Clean, Professional, and Private Document Processing</div>
</div>
""", unsafe_allow_html=True)

# Centered Uploader
_, uploader_col, _ = st.columns([1, 4, 1])
with uploader_col:
    uploaded_file = st.file_uploader("Upload", type="pdf", label_visibility="collapsed")

if uploaded_file:
    # Trigger UX count on new file upload
    file_sig = f"{uploaded_file.name}_{uploaded_file.size}"
    if st.session_state.get("last_sig") != file_sig:
        st.session_state.ux_count += 1
        save_stats(st.session_state.ux_count, st.session_state.dx_count)
        st.session_state.last_sig = file_sig
        st.session_state.detected_text = detect_watermark_candidates(uploaded_file.getvalue())
        st.rerun()

    # Main Workspace Container
    with st.container(border=True):
        col_settings, col_preview = st.columns([3, 2], gap="large")
        uid = uuid.uuid4().hex
        
        with col_settings:
            st.subheader("🛠️ Settings")
            with st.expander("Advanced Options", expanded=False):
                txt = st.text_input("Keywords", value=st.session_state.get("detected_text", ""), key=f"t_{uid}")
                h_h = st.slider("Top Cut", 0, 150, 0, key=f"h_{uid}")
                f_h = st.slider("Bottom Cut", 0, 150, 25, key=f"f_{uid}")
            
            # Full Document Processing
            doc_full = fitz.open(stream=uploaded_file.getvalue(), filetype="pdf")
            out_buffer = io.BytesIO()
            for page in doc_full:
                clean_page_logic(page, h_h, f_h, txt)
            doc_full.save(out_buffer)
            
            st.download_button(
                label="📥 Download Clean PDF",
                data=out_buffer.getvalue(),
                file_name=f"Clean_{uploaded_file.name}",
                on_click=lambda: (st.session_state.update(dx_count=st.session_state.dx_count+1), 
                                  save_stats(st.session_state.ux_count, st.session_state.dx_count))
            )
        
        with col_preview:
            st.subheader("👁️ Preview")
            doc_prev = fitz.open(stream=uploaded_file.getvalue(), filetype="pdf")
            page0 = doc_prev[0]
            clean_page_logic(page0, h_h, f_h, txt)
            # Use 'stretch' for modern Streamlit layout [cite: 147, 148]
            st.image(Image.open(io.BytesIO(page0.get_pixmap(dpi=100).tobytes("png"))), width=None)

else:
    # Feature Grid - Perfectly Centered [cite: 1]
    st.write("")
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown('<div class="feature-box"><h3>⚡ Auto-Detect</h3><p>Identifies repetitive text automatically.</p></div>', unsafe_allow_html=True)
    with f2:
        st.markdown('<div class="feature-box"><h3>🎨 Smart Fill</h3><p>Replaces removed areas with background color.</p></div>', unsafe_allow_html=True)
    with f3:
        st.markdown('<div class="feature-box"><h3>🛡️ Private</h3><p>Files are processed in memory only.</p></div>', unsafe_allow_html=True)

# Visitor Badge Footer
st.markdown(f'<div style="text-align: center; margin-top: 4rem;"><img src="https://visitor-badge.laobi.icu/badge?page_id=pdfwatermarkremover.streamlit.app"></div>', unsafe_allow_html=True)
