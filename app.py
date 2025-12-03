import streamlit as st
import fitz  # PyMuPDF
import io
import time
from PIL import Image

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="DocPolish",
    page_icon="✨",
    layout="wide"
)

# --- 2. CLEAN CSS ---
st.markdown("""
    <style>
    /* GLOBAL SETTINGS */
    * { font-family: 'Inter', sans-serif !important; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }

    /* TITLE STYLE */
    h1 {
        font-weight: 800 !important;
        background: -webkit-linear-gradient(45deg, #820AD1, #B220E8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    .subtitle {
        color: #6B7280;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    /* UPLOAD AREA */
    [data-testid="stFileUploader"] {
        background-color: #FAFAFA;
        border: 2px dashed #E5E7EB;
        border-radius: 15px;
        padding: 20px;
        transition: border 0.2s ease;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #820AD1;
        background-color: #F8F5FF;
    }

    /* PREVIEW CARD */
    .preview-card {
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 15px;
        background-color: #ffffff;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        text-align: center;
    }
    
    /* SUCCESS TOAST */
    .success-toast {
        background-color: #F0FDF4;
        color: #15803D;
        padding: 12px;
        border-radius: 10px;
        border: 1px solid #DCFCE7;
        text-align: center;
        font-weight: 600;
        margin-top: 1rem;
    }

    /* DOWNLOAD BUTTON */
    .stDownloadButton > button {
        background-color: #820AD1 !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 0.8rem 2rem !important;
        font-weight: 600 !important;
        width: 100%;
        border: none !important;
        transition: transform 0.1s;
    }
    .stDownloadButton > button:hover {
        transform: scale(1.01);
        background-color: #6D08AF !important;
    }
    
    /* INPUTS & SLIDERS */
    .stTextInput input { border-radius: 10px; border: 1px solid #E5E7EB; }
    .stTextInput input:focus { border-color: #820AD1; box-shadow: 0 0 0 2px rgba(130,10,209,0.1); }
    
    /* HIDE CHROME */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIC ---
def clean_page(page, header_height, footer_height, text_input, match_case):
    """Applies cleaning logic to a single page"""
    
    # 1. MAGIC ERASER (Multi-Target)
    if text_input:
        # Split by comma to handle multiple phrases (e.g. "Draft, Confidential")
        keywords = [k.strip() for k in text_input.split(',')]
        
        for keyword in keywords:
            if not keyword: continue
            
            # Use search_for (Robust Phrase Finding)
            quads = page.search_for(keyword)
            
            # Apply Redactions
            for quad in quads:
                # Case Sensitivity Check (Manual)
                if match_case:
                    # Get the actual text under this quad to check case
                    res = page.get_text("text", clip=quad).strip()
                    if keyword not in res: # Strict case check
                        continue
                        
                page.add_redact_annot(quad, fill=None)
                
        page.apply_redactions()

    # 2. AREA WIPERS
    rect = page.rect
    clip_rect = fitz.Rect(0, rect.height - 10, 1, rect.height - 9)
    pix = page.get_pixmap(clip=clip_rect)
    r, g, b = pix.pixel(0, 0)
    dynamic_color = (r/255, g/255, b/255)

    if footer_height > 0:
        footer_rect = fitz.Rect(0, rect.height - footer_height, rect.width, rect.height)
        shape = page.new_shape()
        shape.draw_rect(footer_rect)
        shape.finish(color=dynamic_color, fill=dynamic_color, width=0)
        shape.commit()

    if header_height > 0:
        header_rect = fitz.Rect(0, 0, rect.width, header_height)
        shape = page.new_shape()
        shape.draw_rect(header_rect)
        shape.finish(color=dynamic_color, fill=dynamic_color, width=0)
        shape.commit()
        
    return page

def generate_preview(input_bytes, header_height, footer_height, text_input, match_case):
    """Generates preview image of Page 1"""
    doc = fitz.open(stream=input_bytes, filetype="pdf")
    if len(doc) < 1: return None
    page = doc[0]
    clean_page(page, header_height, footer_height, text_input, match_case)
    pix = page.get_pixmap(dpi=100)
    return Image.open(io.BytesIO(pix.tobytes("png")))

def process_all_pages(input_bytes, header_height, footer_height, text_input, match_case):
    """Processes full document"""
    doc = fitz.open(stream=input_bytes, filetype="pdf")
    output_buffer = io.BytesIO()
    doc.set_metadata({}) 
    
    for page in doc:
        clean_page(page, header_height, footer_height, text_input, match_case)
    
    doc.save(output_buffer)
    output_buffer.seek(0)
    return output_buffer, len(doc)

# --- 4. THE UI LAYOUT ---

st.markdown('<h1>DocPolish</h1>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Intelligent Document Cleanser</div>', unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown("### 1. Upload")
    uploaded_file = st.file_uploader("Drop PDF Document", type="pdf")
    
    if uploaded_file:
        st.write("")
        st.markdown("### 2. Controls")
        
        # MAGIC ERASER
        with st.expander("🪄 Magic Text Eraser", expanded=True):
            st.caption("Remove specific words/phrases from anywhere. Separate by commas.")
            text_input = st.text_input("Words to remove", placeholder="e.g. Confidential, Sample Watermark, Draft")
            match_case = st.checkbox("Match Case", value=False)
        
        # SLIDERS
        st.write("")
        st.markdown("**📏 Area Wipers**")
        header_height = st.slider("Header Height (Top)", 0, 150, 0)
        footer_height = st.slider("Footer Height (Bottom)", 0, 150, 0)

with col_right:
    if uploaded_file:
        st.markdown("### 3. Live Preview")
        
        with st.container():
            with st.spinner("Refreshing preview..."):
                preview_img = generate_preview(
                    uploaded_file.getvalue(), 
                    header_height, 
                    footer_height, 
                    text_input, 
                    match_case
                )
                
                if preview_img:
                    st.image(preview_img, use_container_width=True)
                    st.caption("Page 1 Preview")

# --- 5. ACTION BAR ---
if uploaded_file:
    st.write("---")
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("⚡ Process & Download", type="primary"):
            
            with st.status("Processing Document...", expanded=True) as status:
                st.write("🔍 Scanning pages...")
                time.sleep(0.5)
                st.write("🪄 Removing watermarks...")
                time.sleep(0.5)
                
                cleaned_data, page_count = process_all_pages(
                    uploaded_file.getvalue(), 
                    header_height, 
                    footer_height, 
                    text_input, 
                    match_case
                )
                
                status.update(label="✅ Ready!", state="complete", expanded=False)
            
            st.balloons()
            st.markdown(f'<div class="success-toast">Successfully Cleaned {page_count} Pages</div>', unsafe_allow_html=True)
            
            st.download_button(
                label="⬇️ Click to Download PDF",
                data=cleaned_data,
                file_name=f"Clean_{uploaded_file.name}",
                mime="application/pdf"
            )
