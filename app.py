import streamlit as st
import fitz  # PyMuPDF
import io
from PIL import Image
from collections import Counter

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="DocPolish",
    page_icon="✨",
    layout="wide"
)

# --- 2. ADVANCED CSS STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    /* 1. Global Font - applied gently */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* 2. PROTECT ICONS (CRITICAL FIX) */
    /* This forces the arrow icons to use their correct internal font, overriding our 'Inter' font */
    [data-testid="stExpander"] svg, [class*="material-symbols"], .st-emotion-cache-1pbqwg9 {
        font-family: 'Material Symbols Rounded' !important;
    }

    /* 3. Uploader Styling */
    [data-testid="stFileUploader"] {
        background-color: #FFFFFF;
        border: 2px dashed #E5E7EB;
        border-radius: 20px;
        padding: 30px;
        transition: all 0.3s ease;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #764BA2;
        background-color: #FDFBFF;
    }

    /* 4. Notification Box */
    .auto-detect-box {
        background: linear-gradient(to right, #ECFDF5, #F0FDF4);
        border: 1px solid #A7F3D0;
        color: #065F46;
        padding: 12px 20px;
        border-radius: 12px;
        font-size: 0.95rem;
        margin-bottom: 20px;
    }

    /* 5. Headers */
    .hero-container {
        text-align: center;
        margin-bottom: 40px;
        padding: 20px 0;
    }
    .hero-title {
        font-weight: 800;
        background: linear-gradient(135deg, #667EEA 0%, #764BA2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        letter-spacing: -1px;
        margin-bottom: 8px;
    }
    .hero-subtitle {
        color: #6B7280;
        font-size: 1.2rem;
        font-weight: 400;
    }

    /* 6. Button Styling */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #667EEA 0%, #764BA2 100%);
        color: white !important;
        border: none;
        padding: 0.6rem 2rem;
        border-radius: 10px;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
    }
    .stDownloadButton > button:hover {
        box-shadow: 0 10px 15px -3px rgba(118, 75, 162, 0.4);
        transform: translateY(-2px);
    }
    
    /* 7. Hide default elements */
    [data-testid="stHeader"], footer { display: none !important; }
    .block-container { padding-top: 2rem !important; }
    
    /* 8. Center Image in Preview Column */
    div[data-testid="stImage"] {
        display: flex;
        justify-content: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIC ---

def detect_watermark_candidates(file_bytes):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    page_limit = min(5, len(doc))
    text_counts = Counter()
    
    for i in range(page_limit):
        page = doc[i]
        text_blocks = [b[4].strip() for b in page.get_text("blocks")]
        filtered_blocks = [t for t in text_blocks if len(t) > 3]
        text_counts.update(filtered_blocks)

    threshold = max(2, page_limit - 1)
    suggestions = [text for text, count in text_counts.items() if count >= threshold]
    return ", ".join(suggestions)

def clean_page_logic(page, header_h, footer_h, text_input, match_case):
    if text_input:
        keywords = [k.strip() for k in text_input.split(',')]
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
    # Smart color detection
    clip = fitz.Rect(0, rect.height-10, 1, rect.height-9)
    pix = page.get_pixmap(clip=clip)
    r, g, b = pix.pixel(0, 0)
    dynamic_color = (r/255, g/255, b/255)

    if footer_h > 0:
        page.draw_rect(fitz.Rect(0, rect.height - footer_h, rect.width, rect.height), color=dynamic_color, fill=dynamic_color)
    if header_h > 0:
        page.draw_rect(fitz.Rect(0, 0, rect.width, header_h), color=dynamic_color, fill=dynamic_color)

def get_pdf_info(file_bytes):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    return len(doc)

@st.cache_data(show_spinner=False)
def get_preview_image(file_bytes, header_h, footer_h, txt, case):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    if len(doc) < 1: return None
    page = doc[0]
    clean_page_logic(page, header_h, footer_h, txt, case)
    # Kept DPI high (150) for readability, we control size via display width
    pix = page.get_pixmap(dpi=150) 
    return Image.open(io.BytesIO(pix.tobytes("png")))

@st.cache_data
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

# HERO SECTION
st.markdown("""
<div class="hero-container">
    <div class="hero-title">DocPolish</div>
    <div class="hero-subtitle">Intelligent Document Cleanser & Sanitizer</div>
</div>
""", unsafe_allow_html=True)

# UPLOAD SECTION
c1, c2, c3 = st.columns([1, 6, 1])
with c2:
    uploaded_file = st.file_uploader("Drop your PDF here", type="pdf", label_visibility="collapsed")

# --- LOGIC HANDLING ---
if uploaded_file:
    file_bytes = uploaded_file.getvalue()
    
    # Auto-Detect Logic (Run Once)
    if "current_file" not in st.session_state or st.session_state.current_file != uploaded_file.name:
        st.session_state.current_file = uploaded_file.name
        with st.spinner("🤖 AI is scanning document structure..."):
            detected_keywords = detect_watermark_candidates(file_bytes)
            st.session_state.auto_keywords = detected_keywords
            st.session_state.header_h = 0
            st.session_state.footer_h = 0

# --- STATE 1: LANDING PAGE (No File) ---
if not uploaded_file:
    st.write("")
    st.write("")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('### ⚡ Auto-Detection')
        st.caption("Smart algorithms instantly find repeated watermarks.")
    with col2:
        st.markdown('### 🎨 Smart Inpainting')
        st.caption("Fills gaps with dynamic background color matching.")
    with col3:
        st.markdown('### 🔒 Secure & Private')
        st.caption("All processing happens in memory. No data storage.")

# --- STATE 2: WORKSPACE (File Loaded) ---
else:
    # Retrieve State
    default_keywords = st.session_state.get("auto_keywords", "")
    
    # 1. NOTIFICATION
    if default_keywords:
        st.markdown(f"""
        <div class="auto-detect-box">
            ✨ <b>AI Detected Watermarks:</b> Found potential watermarks: <u>{default_keywords}</u>
        </div>
        """, unsafe_allow_html=True)

    # 2. MAIN CARD LAYOUT (Using native st.container for border)
    with st.container(border=True):
        
        # Changed Layout: 3 parts Settings, 2 parts Preview (Preview is smaller)
        col_settings, col_preview = st.columns([3, 2], gap="large")
        
        # LEFT: SETTINGS
        with col_settings:
            st.subheader("🛠️ Controls")
            
            # Simple Expander for Advanced
            with st.expander("Adjust Cleaning Settings", expanded=False):
                st.markdown("**📝 Text Removal**")
                text_input = st.text_input("Keywords", value=default_keywords, label_visibility="collapsed")
                match_case = st.checkbox("Match Case", value=False)
                
                st.markdown("---")
                
                st.markdown("**📐 Boundary Removal**")
                header_height = st.slider("Header Size", 0, 150, st.session_state.get("header_h", 0))
                footer_height = st.slider("Footer Size", 0, 150, st.session_state.get("footer_h", 0))

            # DOWNLOAD ACTION
            st.write("")
            final_pdf_data = process_full_document(
                uploaded_file.getvalue(), 
                header_height, 
                footer_height, 
                text_input, 
                match_case
            )
            st.download_button(
                label="🚀 Process & Download PDF",
                data=final_pdf_data,
                file_name=f"Clean_{uploaded_file.name}",
                mime="application/pdf"
            )

        # RIGHT: PREVIEW
        with col_preview:
            st.subheader("👁️ Live Preview")
            preview_img = get_preview_image(uploaded_file.getvalue(), header_height, footer_height, text_input, match_case)
            if preview_img:
                # Fixed Width to 450px to prevent it from being "too large"
                st.image(preview_img, width=450)
            else:
                st.info("Preview unavailable for this file.")
