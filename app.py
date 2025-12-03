import streamlit as st
import fitz  # PyMuPDF
import io
from PIL import Image

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="DocPolish",
    page_icon="✨",
    layout="wide"
)

# --- 2. CLEAN & BALANCED CSS ---
st.markdown("""
    <style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    /* 1. LAYOUT RESET */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 1100px !important;
        margin: 0 auto !important;
    }
    
    /* 2. UI CLEANUP */
    [data-testid="stHeader"] { display: none !important; }
    #MainMenu, footer { visibility: hidden; }
    [data-testid="stAppViewContainer"] { background-color: #FFFFFF !important; }
    
    /* 3. TYPOGRAPHY */
    * { font-family: 'Inter', sans-serif !important; color: #111111; }

    .hero-title {
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #820AD1, #B220E8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        text-align: center;
        margin-bottom: 10px;
    }
    .hero-subtitle {
        color: #6B7280;
        font-size: 1.1rem;
        text-align: center;
        margin-bottom: 40px;
        font-weight: 400;
    }

    /* 4. UPLOAD BOX (Balanced Width) */
    [data-testid="stFileUploader"] {
        background-color: #FAFAFA;
        border: 2px dashed #E5E7EB;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #820AD1;
        background-color: #F8F5FF;
    }

    /* 5. DOWNLOAD BUTTON */
    .stDownloadButton > button {
        background: linear-gradient(90deg, #820AD1 0%, #6D08AF 100%);
        color: white !important;
        border-radius: 12px;
        padding: 0.8rem 2rem;
        font-weight: 700;
        width: 100%;
        border: none;
        box-shadow: 0 4px 15px rgba(130, 10, 209, 0.2);
    }
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(130, 10, 209, 0.3);
    }
    
    /* 6. PREVIEW IMAGE */
    img {
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
    }
    
    /* 7. PAGE COUNT BADGE */
    .page-badge {
        background-color: #F3F4F6;
        color: #6B7280;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin-top: 5px;
    }
    
    /* 8. INPUTS (Clean) */
    .stTextInput input {
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 10px;
    }
    
    /* Feature Icons (No Box) */
    .feature-icon { font-size: 1.5rem; margin-bottom: 5px; }
    .feature-text { color: #666; font-size: 0.9rem; }
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIC ---

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
    pix = page.get_pixmap(dpi=120) 
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

# Header
st.markdown('<div class="hero-title">DocPolish</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">Professional Document Cleanser</div>', unsafe_allow_html=True)

# UPLOAD SECTION (Visual Balance: 1-2-1 columns)
c_up1, c_up2, c_up3 = st.columns([1, 2, 1])
with c_up2:
    uploaded_file = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")
    
    # Page Count Badge (Only visible if file exists)
    if uploaded_file:
        page_count = get_pdf_info(uploaded_file.getvalue())
        st.markdown(f'<div style="text-align: center;"><span class="page-badge">📄 {page_count} Pages Detected</span></div>', unsafe_allow_html=True)

# --- STATE 1: NO FILE ---
if not uploaded_file:
    st.write("")
    st.write("")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div style="text-align: center;"><div class="feature-icon">🪄</div><b>Magic Eraser</b><div class="feature-text">Type words to vanish them.</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div style="text-align: center;"><div class="feature-icon">📏</div><b>Area Wipers</b><div class="feature-text">Clean headers & footers.</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div style="text-align: center;"><div class="feature-icon">🔒</div><b>100% Private</b><div class="feature-text">Processed locally in browser.</div></div>', unsafe_allow_html=True)

# --- STATE 2: WORKSPACE ---
else:
    st.write("---")

    # MAIN STUDIO (Left Controls | Right Preview)
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown("### 🪄 Magic Text Eraser")
        text_input = st.text_input("keywords", placeholder="e.g. Confidential, Draft", label_visibility="collapsed")
        match_case = st.checkbox("Match Case", value=False)
        st.caption("Removes specific words/phrases.")
        
        st.write("") 
        
        st.markdown("### 📏 Area Wipers")
        
        st.caption("Top Header")
        header_height = st.slider("Header", 0, 150, 0, label_visibility="collapsed")
        
        st.caption("Bottom Footer")
        footer_height = st.slider("Footer", 0, 150, 0, label_visibility="collapsed")

    with col_right:
        st.markdown("###  Live Preview")
        preview_img = get_preview_image(uploaded_file.getvalue(), header_height, footer_height, text_input, match_case)
        if preview_img:
            # RESTRICTED WIDTH (Matches left column weight)
            st.image(preview_img, width=350)

    # ACTION AREA
    st.write("---")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        final_pdf_data = process_full_document(
            uploaded_file.getvalue(), 
            header_height, 
            footer_height, 
            text_input, 
            match_case
        )
        st.download_button(
            label="⚡ Process & Download PDF",
            data=final_pdf_data,
            file_name=f"Clean_{uploaded_file.name}",
            mime="application/pdf"
        )
