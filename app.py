import streamlit as st
import fitz  # PyMuPDF
import io
import time

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="DocPolish",
    page_icon="✨",
    layout="centered"
)

# --- 2. ENHANCED CSS ---
st.markdown("""
    <style>
    /* IMPORT BETTER FONT */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    /* FORCE LIGHT THEME */
    [data-testid="stAppViewContainer"] { 
        background: linear-gradient(135deg, #FFFFFF 0%, #F9FAFB 100%) !important;
    }
    [data-testid="stHeader"] { background-color: transparent !important; }
    
    /* GLOBAL FONTS */
    * { 
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important; 
        color: #111111; 
    }

    /* ANIMATED TITLE */
    h1 {
        font-weight: 800 !important;
        letter-spacing: -0.04em !important;
        background: linear-gradient(135deg, #820AD1 0%, #B44EE8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3.5rem !important;
        text-align: center;
        margin-bottom: 0px !important;
        padding-top: 20px !important;
        animation: fadeInDown 0.6s ease-out;
    }
    
    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    p.subtitle {
        text-align: center;
        color: #6B7280 !important;
        font-size: 1.15rem;
        margin-top: 8px;
        margin-bottom: 40px;
        font-weight: 500;
        letter-spacing: 0.01em;
        animation: fadeIn 0.8s ease-out 0.2s both;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    /* ENHANCED UPLOAD CARD */
    [data-testid="stFileUploader"] {
        background: linear-gradient(135deg, #FAFAFA 0%, #F5F5F7 100%);
        border: 2.5px dashed #D1D5DB;
        border-radius: 24px;
        padding: 40px 30px;
        text-align: center;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        animation: slideUp 0.6s ease-out 0.3s both;
    }
    
    @keyframes slideUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #820AD1;
        background: linear-gradient(135deg, #FAF5FF 0%, #F3E8FF 100%);
        box-shadow: 0 8px 25px rgba(130, 10, 209, 0.15);
        transform: translateY(-2px);
    }
    
    /* FILE UPLOAD TEXT */
    [data-testid="stFileUploader"] label {
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        color: #374151 !important;
    }

    /* SECTION LABELS */
    .stMarkdown strong {
        color: #1F2937 !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        letter-spacing: -0.01em;
    }
    
    .stMarkdown .stCaption {
        color: #6B7280 !important;
        font-size: 0.9rem !important;
        line-height: 1.5 !important;
        margin-top: 4px !important;
    }

    /* ENHANCED SLIDER */
    .stSlider {
        padding: 10px 0;
    }
    
    [data-testid="stSlider"] {
        animation: fadeIn 0.5s ease-out 0.4s both;
    }

    /* SUCCESS BUBBLE - ENHANCED */
    .success-box {
        background: linear-gradient(135deg, #F3E8FF 0%, #E9D5FF 100%);
        color: #6D08AF;
        padding: 18px 24px;
        border-radius: 16px;
        font-weight: 700;
        font-size: 1.05rem;
        text-align: center;
        margin-bottom: 16px;
        border: 2px solid #D8B4FE;
        width: 100%; 
        box-sizing: border-box;
        box-shadow: 0 4px 20px rgba(130, 10, 209, 0.15);
        animation: successPop 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        letter-spacing: -0.01em;
    }
    
    @keyframes successPop {
        0% { opacity: 0; transform: scale(0.8) translateY(20px); }
        100% { opacity: 1; transform: scale(1) translateY(0); }
    }

    /* ENHANCED DOWNLOAD BUTTON */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #820AD1 0%, #6D08AF 100%) !important;
        color: white !important;
        border-radius: 16px !important;
        padding: 1rem 1.5rem !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        border: none !important;
        box-shadow: 0 6px 25px rgba(130, 10, 209, 0.35) !important;
        width: 100%;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        letter-spacing: -0.01em;
        animation: fadeIn 0.5s ease-out 0.2s both;
    }
    
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #6D08AF 0%, #5A0891 100%) !important;
        transform: translateY(-3px);
        box-shadow: 0 12px 35px rgba(130, 10, 209, 0.45) !important;
    }
    
    .stDownloadButton > button:active {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(130, 10, 209, 0.35) !important;
    }

    /* DIVIDER STYLING */
    hr {
        margin: 24px 0 !important;
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, #E5E7EB, transparent) !important;
    }

    /* SPINNER ENHANCEMENT */
    [data-testid="stSpinner"] > div {
        border-top-color: #820AD1 !important;
    }

    /* HIDE CHROME */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* UPLOADED FILE DISPLAY */
    [data-testid="stFileUploader"] section {
        background: white !important;
        border-radius: 12px !important;
        border: 1px solid #E5E7EB !important;
        padding: 12px !important;
        transition: all 0.2s ease;
    }
    
    [data-testid="stFileUploader"] section:hover {
        border-color: #820AD1 !important;
        box-shadow: 0 2px 8px rgba(130, 10, 209, 0.1) !important;
    }
    
    /* CONTAINER SPACING */
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 3rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. PROCESSING LOGIC (UNCHANGED) ---
def process_pdf(input_bytes, footer_height):
    doc = fitz.open(stream=input_bytes, filetype="pdf")
    output_buffer = io.BytesIO()
    
    for page in doc:
        rect = page.rect
        # Smart detection
        clip_rect = fitz.Rect(0, rect.height - 10, 1, rect.height - 9)
        pix = page.get_pixmap(clip=clip_rect)
        r, g, b = pix.pixel(0, 0)
        dynamic_color = (r/255, g/255, b/255)
        
        # Draw box
        footer_rect = fitz.Rect(0, rect.height - footer_height, rect.width, rect.height)
        shape = page.new_shape()
        shape.draw_rect(footer_rect)
        shape.finish(color=dynamic_color, fill=dynamic_color, width=0)
        shape.commit()
    
    doc.save(output_buffer)
    output_buffer.seek(0)
    return output_buffer, len(doc)

# --- 4. THE UI ---

# Header with icon
st.markdown('<h1>✨ DocPolish</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Simple. Transparent. Clean.</p>', unsafe_allow_html=True)

# Main Container
c1, c2, c3 = st.columns([1, 8, 1])

with c2:
    uploaded_file = st.file_uploader("📄 Drop your PDF here", type="pdf")
    
    if uploaded_file:
        st.write("") 
        
        # Context + Slider
        st.markdown("**🎯 Cleaning Depth**")
        st.caption("Controls how many pixels are removed from the bottom of the page. Increase this only if footer text is still visible.")
        
        # Slider
        footer_height = st.slider("", 10, 100, 30, label_visibility="collapsed")
        
        st.write("---") 
        
        # Auto-Process with enhanced spinner
        with st.spinner("✨ Polishing pixels..."):
            cleaned_data, page_count = process_pdf(uploaded_file.getvalue(), footer_height)
            time.sleep(0.5)
        
        # --- RESULTS ---
        # 1. Success Message
        st.markdown(f'<div class="success-box">✨ {page_count} Pages Cleaned Successfully!</div>', unsafe_allow_html=True)
        
        # 2. Download Button
        st.download_button(
            label="⬇️ Download Cleaned PDF",
            data=cleaned_data,
            file_name=f"Clean_{uploaded_file.name}",
            mime="application/pdf"
        )
