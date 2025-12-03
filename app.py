import streamlit as st
import fitz  # PyMuPDF
import io
import time

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="DocPolish",
    page_icon="🟣",
    layout="centered"
)

# --- 2. STYLING ---
st.markdown("""
    <style>
    /* FORCE LIGHT THEME */
    [data-testid="stAppViewContainer"] { background-color: #FFFFFF !important; }
    [data-testid="stHeader"] { background-color: #FFFFFF !important; }
    
    /* GLOBAL FONTS */
    * { font-family: 'Inter', sans-serif !important; color: #111111; }

    /* TITLE */
    h1 {
        font-weight: 800 !important;
        letter-spacing: -0.03em !important;
        color: #820AD1 !important;
        font-size: 3rem !important;
        text-align: center;
        margin-bottom: 0px !important;
        padding-top: 10px !important;
    }
    
    p.subtitle {
        text-align: center;
        color: #6B7280 !important;
        font-size: 1.1rem;
        margin-top: 5px;
        margin-bottom: 30px;
        font-weight: 400;
    }

    /* UPLOAD CARD */
    [data-testid="stFileUploader"] {
        background-color: #F8F9FA; 
        border: 2px dashed #E5E7EB;
        border-radius: 20px;
        padding: 30px;
        text-align: center;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #820AD1;
        background-color: #F3E8FF;
    }

    /* SLIDER FIX */
    div[data-baseweb="slider"] div { background-color: #820AD1 !important; }

    /* SUCCESS BUBBLE (Full Width to match button) */
    .success-box {
        background-color: #F3E8FF;
        color: #6D08AF;
        padding: 12px;
        border-radius: 12px; /* Matches button curve slightly */
        font-weight: 600;
        text-align: center;
        margin-bottom: 12px;
        border: 1px solid #D8B4FE;
        width: 100%; /* Forces alignment */
    }

    /* DOWNLOAD BUTTON */
    .stDownloadButton > button {
        background-color: #820AD1 !important;
        color: white !important;
        border-radius: 12px !important; /* Consistent radius */
        padding: 0.8rem 1rem !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(130, 10, 209, 0.3) !important;
        width: 100%;
        transition: transform 0.2s;
    }
    .stDownloadButton > button:hover {
        background-color: #6D08AF !important;
        transform: scale(1.02);
    }

    /* HIDE CHROME */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIC ---
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

# Header
st.markdown('<h1>DocPolish</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Simple. Transparent. Clean.</p>', unsafe_allow_html=True)

# Main Area
c1, c2, c3 = st.columns([1, 8, 1])

with c2:
    uploaded_file = st.file_uploader("Drop your PDF here", type="pdf")
    
    if uploaded_file:
        st.write("") 
        
        # Context + Slider
        st.markdown("**Cleaning Depth**")
        st.caption("Controls how many pixels are removed from the bottom of the page. Increase this only if footer text is still visible.")
        
        # Standard Slider
        footer_height = st.slider("", 10, 100, 30, label_visibility="collapsed")
        
        st.write("---") 
        
        # Auto-Process
        with st.spinner("Polishing pixels..."):
            cleaned_data, page_count = process_pdf(uploaded_file.getvalue(), footer_height)
            time.sleep(0.5)
        
        # --- RESULTS AREA (Perfectly Aligned) ---
        # We create a new column set just for the results to pinch them in slightly
        res_col1, res_col2, res_col3 = st.columns([1, 2, 1])
        
        with res_col2:
            # 1. The Success Message (Full Width of this column)
            st.markdown(f'<div class="success-box">✨ {page_count} Pages Cleaned</div>', unsafe_allow_html=True)
            
            # 2. The Download Button (Full Width of this column)
            st.download_button(
                label="Download PDF",
                data=cleaned_data,
                file_name=f"Clean_{uploaded_file.name}",
                mime="application/pdf"
            )

# Footer Trust Signals
st.write("")
st.write("")
st.markdown("""

""", unsafe_allow_html=True)
