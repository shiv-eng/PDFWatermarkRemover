import streamlit as st
import fitz  # PyMuPDF
import io
import time

# --- 1. PAGE SETUP ---
st.set_page_config(
    page_title="DocPolish",
    page_icon="✨",
    layout="centered"
)

# --- 2. HIGH-END CSS (THE "BEAUTIFUL" PART) ---
st.markdown("""
    <style>
    /* IMPORT INTER FONT */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

    /* GLOBAL RESET */
    * {
        font-family: 'Inter', sans-serif !important;
        -webkit-font-smoothing: antialiased;
    }

    /* BACKGROUND & CANVAS */
    .stApp {
        background-color: #FFFFFF;
    }

    /* HIDE STREAMLIT CHROME */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* --- TYPOGRAPHY --- */
    h1 {
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
        color: #171717 !important;
        font-size: 48px !important;
        text-align: center;
        margin-bottom: 0px !important;
        padding-top: 40px !important;
    }
    
    p.subtitle {
        text-align: center;
        color: #737373;
        font-size: 18px;
        margin-top: 8px;
        margin-bottom: 40px;
        font-weight: 400;
    }

    /* --- THE "MAIN CARD" --- */
    /* We style the file uploader container to look like a premium drop zone */
    [data-testid="stFileUploader"] {
        background-color: #FAFAFA;
        border: 1px dashed #E5E5E5;
        border-radius: 16px;
        padding: 40px 20px;
        text-align: center;
        transition: all 0.2s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #A3A3A3;
        background-color: #F5F5F5;
    }
    
    /* The small "Drag and drop" text inside uploader */
    [data-testid="stFileUploader"] section > div {
        color: #737373;
    }

    /* --- DOWNLOAD BUTTON --- */
    /* Minimalist Black Button */
    .stDownloadButton > button {
        background-color: #171717 !important;
        color: #FFFFFF !important;
        border: 1px solid #171717 !important;
        border-radius: 8px !important;
        padding: 0.6rem 2rem !important;
        font-weight: 500 !important;
        font-size: 16px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        width: 100%;
        margin-top: 10px;
    }
    
    .stDownloadButton > button:hover {
        background-color: #262626 !important;
        border-color: #262626 !important;
        transform: translateY(-1px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05) !important;
    }

    /* --- SUCCESS MESSAGE --- */
    .success-badge {
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #F0FDF4;
        color: #15803D;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #DCFCE7;
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 16px;
    }

    /* --- FOOTER TRUST SIGNALS --- */
    .trust-footer {
        display: flex;
        justify-content: center;
        gap: 32px;
        margin-top: 60px;
        border-top: 1px solid #F5F5F5;
        padding-top: 32px;
    }
    
    .trust-item {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #A3A3A3;
        font-size: 13px;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. PROCESSING ENGINE ---
def process_pdf(input_bytes, footer_height):
    doc = fitz.open(stream=input_bytes, filetype="pdf")
    output_buffer = io.BytesIO()
    
    for page in doc:
        rect = page.rect
        # 1. Smart Color Detection
        clip_rect = fitz.Rect(0, rect.height - 10, 1, rect.height - 9)
        pix = page.get_pixmap(clip=clip_rect)
        r, g, b = pix.pixel(0, 0)
        dynamic_color = (r/255, g/255, b/255)
        
        # 2. Draw Cover Box
        footer_rect = fitz.Rect(0, rect.height - footer_height, rect.width, rect.height)
        shape = page.new_shape()
        shape.draw_rect(footer_rect)
        shape.finish(color=dynamic_color, fill=dynamic_color, width=0)
        shape.commit()
    
    doc.save(output_buffer)
    output_buffer.seek(0)
    return output_buffer, len(doc)

# --- 4. THE UI LAYOUT ---

# A. Header
st.markdown('<h1>DocPolish</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Minimalist document sanitization. 100% Private.</p>', unsafe_allow_html=True)

# B. Main Interaction Area
# We use a spacer to center the column visually on wide screens
c1, c2, c3 = st.columns([1, 6, 1]) 

with c2:
    uploaded_file = st.file_uploader("Drop your PDF here", type="pdf")
    
    if uploaded_file:
        st.write("") # Spacer
        
        # Minimalist Slider (Standard Streamlit)
        # We hide the label visually but keep it accessible
        footer_height = st.slider("Cleaning Depth (px)", 10, 100, 30)
        st.caption("Adjust cleaning depth if needed.")
        
        st.write("---") # Subtle divider
        
        # Auto-Process
        with st.spinner("Polishing..."):
            # Fast processing simulation
            cleaned_data, page_count = process_pdf(uploaded_file.getvalue(), footer_height)
            time.sleep(0.3) # Just enough to feel the "work" happen
        
        # Success Badge
        st.markdown(
            f"""
            <div class="success-badge">
                <span style="margin-right: 8px;">✨</span> 
                Ready for download ({page_count} pages processed)
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # The Primary Action
        st.download_button(
            label="Download Clean PDF",
            data=cleaned_data,
            file_name=f"Clean_{uploaded_file.name}",
            mime="application/pdf"
        )

# C. Minimalist Footer
st.markdown("""
<div class="trust-footer">
    <div class="trust-item">
        <span>🔒</span> Local Processing
    </div>
    <div class="trust-item">
        <span>⚡</span> Instant
    </div>
    <div class="trust-item">
        <span>💎</span> High Quality
    </div>
</div>
""", unsafe_allow_html=True)
