import streamlit as st
import fitz  # PyMuPDF
import io
import uuid
import time
from PIL import Image
from collections import Counter

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="PDF Watermark Remover",
    page_icon="💧", 
    layout="wide"
)

# --- 2. CSS STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* Clean Expander */
    [data-testid="stExpander"] {
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        background-color: #FAFAFA;
    }

    /* Uploader */
    [data-testid="stFileUploader"] {
        background-color: #FFFFFF;
        border: 2px dashed #E5E7EB;
        border-radius: 20px;
        padding: 30px;
    }
    
    /* Success/Auto-Detect Box */
    .auto-detect-box {
        background: linear-gradient(to right, #F0FDF4, #DCFCE7); /* Green tint */
        border: 1px solid #BBF7D0;
        color: #166534;
        padding: 12px 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        font-size: 0.95rem;
    }
    
    .hero-container { text-align: center; margin-bottom: 40px; padding: 20px 0; }
    .hero-title { 
        font-weight: 800; 
        background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%); 
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        font-size: 3.5rem; 
        margin-bottom: 8px; 
    }
    .hero-subtitle { color: #6B7280; font-size: 1.2rem; }
    
    .stDownloadButton > button {
        background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%);
        color: white !important;
        border: none;
        padding: 0.6rem 2rem;
        border-radius: 10px;
        font-weight: 600;
        width: 100%;
    }

    /* Center-aligned feature cards */
    .feature-card {
        text-align: center;
        padding: 10px;
    }
    
    [data-testid="stHeader"], footer { display: none !important; }
    .block-container { padding-top: 2rem !important; }
    div[data-testid="stImage"] { display: flex; justify-content: center; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CORE LOGIC ---

def detect_watermark_candidates(file_bytes):
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        page_limit = min(5, len(doc))
        text_counts = Counter()
        for i in range(page_limit):
            page = doc[i]
            text_blocks = [b[4].strip() for b in page.get_text("blocks")]
            filtered_blocks = [t for t in text_blocks if len(t) > 3]
            text_counts.update(filtered_blocks)
        threshold = max(2, page_limit - 1)
        return ", ".join([text for text, count in text_counts.items() if count >= threshold])
    except:
        return ""

def clean_page_logic(page, header_h, footer_h, keywords_str, match_case):
    if keywords_str:
        keywords = [k.strip() for k in keywords_str.split(',')]
        for keyword in keywords:
            if not keyword: continue
            quads = page.search_for(keyword)
            for quad in quads:
                if match_case:
                    res = page.get_text("text", clip=quad).strip()
                    if keyword not in res: continue
                page.add_redact_annot(quad, fill=None)
        page.apply_redactions()

    rect = page.rect
    clip = fitz.Rect(0, rect.height-10, 1, rect.height-9)
    pix = page.get_pixmap(clip=clip)
    r, g, b = pix.pixel(0, 0)
    dynamic_color = (r/255, g/255, b/255)

    if footer_h > 0:
        page.draw_rect(fitz.Rect(0, rect.height - footer_h, rect.width, rect.height), color=dynamic_color, fill=dynamic_color)
    if header_h > 0:
        page.draw_rect(fitz.Rect(0, 0, rect.width, header_h), color=dynamic_color, fill=dynamic_color)

@st.cache_data(show_spinner=False, ttl=3600)
def get_preview_image(file_bytes, header_h, footer_h, txt, case):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    if len(doc) < 1: return None
    page = doc[0]
    clean_page_logic(page, header_h, footer_h, txt, case)
    pix = page.get_pixmap(dpi=150) 
    return Image.open(io.BytesIO(pix.tobytes("png")))

@st.cache_data(show_spinner=False, ttl=3600)
def process_full_document(file_bytes, header_h, footer_h, txt, case):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    output_buffer = io.BytesIO()
    doc.set_metadata({}) 
    for page in doc:
        clean_page_logic(page, header_h, footer_h, txt, case)
    doc.save(output_buffer)
    output_buffer.seek(0)
    return output_buffer

# --- 4. UI LAYOUT ---

st.markdown("""
<div class="hero-container">
    <div class="hero-title">PDF Watermark Remover</div>
    <div class="hero-subtitle">Clean, Professional, and Private Document Processing</div>
</div>
""", unsafe_allow_html=True)

# 1. UPLOAD SECTION
c1, c2, c3 = st.columns([1, 6, 1])
with c2:
    uploaded_file = st.file_uploader("Drop your PDF here to start", type="pdf", label_visibility="collapsed")

# 2. INVISIBLE INITIALIZATION
if uploaded_file:
    file_bytes = uploaded_file.getvalue()
    file_signature = f"{uploaded_file.name}_{uploaded_file.size}"
    
    if "current_file_signature" not in st.session_state or st.session_state.current_file_signature != file_signature:
        with st.spinner("🚀 Initializing auto-clean..."):
            detected_txt = detect_watermark_candidates(file_bytes)
            new_uid = uuid.uuid4().hex
            st.session_state.unique_session_id = new_uid
            st.session_state.detected_text = detected_txt
            st.session_state.current_file_signature = file_signature
            time.sleep(0.5)
            
# 3. MAIN INTERFACE (Fix for Center Alignment)
if not uploaded_file:
    st.write("")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="feature-card"><h3>⚡ Auto-Detect</h3><p style="color: #6B7280;">Identifies repetitive text automatically.</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="feature-card"><h3>🎨 Smart Fill</h3><p style="color: #6B7280;">Replaces removed areas with background color.</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="feature-card"><h3>🛡️ Private</h3><p style="color: #6B7280;">Files are processed in memory only.</p></div>', unsafe_allow_html=True)

else:
    detected_msg = st.session_state.get('detected_text', 'None')
    st.markdown(f"""
    <div class="auto-detect-box">
        ✨ <b>Auto-Clean Applied!</b> Detected watermarks: <i>{detected_msg}</i>
    </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        col_settings, col_preview = st.columns([3, 2], gap="large")
        uid = st.session_state.get("unique_session_id", "default_1")
        
        with col_settings:
            st.subheader("🛠️ Removal Settings")
            with st.expander("Advanced Options (Click to Edit)", expanded=False):
                st.markdown("**📝 Text Watermarks**")
                text_input = st.text_input(
                    "Keywords", 
                    value=st.session_state.get("detected_text", ""),
                    key=f"txt_{uid}", 
                    help="Enter specific words to erase."
                )
                match_case = st.checkbox("Match Case", value=False, key=f"case_{uid}")
                st.markdown("---")
                st.markdown("**✂️ Header & Footer Cutters**")
                header_height = st.slider("Top Margin Cut", 0, 150, value=0, key=f"head_{uid}")
                footer_height = st.slider("Bottom Margin Cut", 0, 150, value=21, key=f"foot_{uid}")

            st.write("")
            final_pdf_data = process_full_document(
                uploaded_file.getvalue(), 
                header_height, 
                footer_height, 
                text_input, 
                match_case
            )
            st.download_button(
                label="📥 Download Clean PDF",
                data=final_pdf_data,
                file_name=f"Clean_{uploaded_file.name}",
                mime="application/pdf"
            )

        with col_preview:
            st.subheader("👁️ Preview")
            preview_img = get_preview_image(uploaded_file.getvalue(), header_height, footer_height, text_input, match_case)
            if preview_img:
                st.image(preview_img, width=450)
            else:
                st.info("Preview unavailable.")

# --- FOOTER ---
st.markdown("""
<div style="text-align: center; margin-top: 60px; border-top: 1px solid #E5E7EB; padding-top: 20px;">
    <img src="https://visitor-badge.laobi.icu/badge?page_id=pdfwatermarkremover.streamlit.app&left_text=Total%20Visits&left_color=%231F2937&right_color=%232563EB" alt="Visitor Count">
</div>
""", unsafe_allow_html=True)
