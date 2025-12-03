import streamlit as st
import fitz  # PyMuPDF
import io
import time

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="DocPolish | Nu Edition",
    page_icon="🟣",
    layout="centered"
)

# --- 2. HIGH-END NU CSS ---
st.markdown("""
    <style>
    /* IMPORT MODERN FONT */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

    /* GLOBAL RESET */
    * {
        font-family: 'Inter', sans-serif !important;
    }

    /* APP BACKGROUND */
    .stApp {
        background-color: #FFFFFF;
    }

    /* --- TYPOGRAPHY --- */
    h1 {
        font-weight: 800 !important;
        letter-spacing: -0.03em !important;
        color: #820AD1 !important; /* Nu Purple */
        font-size: 3.5rem !important;
        text-align: center;
        margin-bottom: 0px !important;
        padding-top: 20px !important;
    }
    
    p.subtitle {
        text-align: center;
        color: #737373;
        font-size: 1.1rem;
        margin-top: 5px;
        margin-bottom: 40px;
        font-weight: 400;
    }

    /* --- THE PREMIUM UPLOAD CARD --- */
    [data-testid="stFileUploader"] {
        background-color: #F8F9FA; /* Very light grey */
        border: 2px dashed #E5E7EB;
        border-radius: 24px;
        padding: 40px 20px;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #820AD1; /* Purple border on hover */
        background-color: #F3E8FF; /* Light purple tint */
        box-shadow: 0 10px 30px -10px rgba(130, 10, 209, 0.15);
    }
    
    /* Small text inside uploader */
    [data-testid="stFileUploader"] section > div {
        color: #6B7280;
    }

    /* --- CENTERED DOWNLOAD BUTTON --- */
    .stDownloadButton > button {
        background-color: #820AD1 !important;
        color: white !important;
        border-radius: 50px !important; /* Pill Shape */
        padding: 0.8rem 3rem !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(130, 10, 209, 0.3) !important;
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important; /* Bouncy animation */
        width: 100%;
    }
    
    .stDownloadButton > button:hover {
        background-color: #6D08AF !important;
        transform: translateY(-4px) scale(1.02);
        box-shadow: 0 10px 25px rgba(130, 10, 209, 0.4) !important;
    }

    /* --- SLIDER COLOR --- */
    div[data-baseweb="slider"] div {
        background-color: #820AD1 !important;
    }

    /* --- SUCCESS NOTIFICATION --- */
    .success-bubble {
        text-align: center;
        background-color: #F3E8FF; /* Light Purple */
        color: #6D08AF;
        padding: 12px 24px;
        border-radius: 30px;
        font-weight: 600;
        font-size: 0.95rem;
        display: inline-block;
        margin-bottom: 20px;
        border: 1px solid #D8B4FE;
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

# --- 4. THE UI LAYOUT ---

# Header
st.markdown('<h1>DocPolish</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">The simplest way to clean your documents.</p>', unsafe_allow_html=True)

# Main Area
c_outer_1, c_outer_2, c_outer_3 = st.columns([1, 8, 1])

with c_outer_2:
    uploaded_file = st.file_uploader("Drop PDF here", type="pdf")
    
    if uploaded_file:
        st.write("") # Spacer
        
        # Purple Slider
        st.markdown("**Cleaning Depth**")
        footer_height = st.slider("", 10, 100, 30, label_visibility="collapsed")
        
        st.write("---") # Visual Divider
        
        # Processing
        with st.spinner("Polishing pixels..."):
            cleaned_data, page_count = process_pdf(uploaded_file.getvalue(), footer_height)
            time.sleep(0.5)
        
        # Success Badge (Centered)
        st.markdown(
            f"""
            <div style="text-align: center;">
                <div class="success-bubble">
                    ✨ {page_count} Pages Processed Successfully
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # CENTERED BUTTON LAYOUT
        # We use columns inside columns to pinch the button into the center
        b1, b2, b3 = st.columns([1, 2, 1])
        with b2:
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
<div style="display: flex; justify-content: center; gap: 40px; margin-top: 50px; opacity: 0.7;">
    <div style="text-align: center;">
        <span style="font-size: 1.5rem; color: #820AD1;">🔒</span>
        <div style="font-size: 0.8rem; font-weight: 600; color: #111;">Private</div>
    </div>
    <div style="text-align: center;">
        <span style="font-size: 1.5rem; color: #820AD1;">⚡</span>
        <div style="font-size: 0.8rem; font-weight: 600; color: #111;">Instant</div>
    </div>
    <div style="text-align: center;">
        <span style="font-size: 1.5rem; color: #820AD1;">💎</span>
        <div style="font-size: 0.8rem; font-weight: 600; color: #111;">Free</div>
    </div>
</div>
""", unsafe_allow_html=True)
