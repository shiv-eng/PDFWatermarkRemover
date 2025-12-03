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

# --- 2. OPTIMIZED CSS (No Glitches) ---
st.markdown("""
    <style>
    /* FORCE LIGHT THEME */
    [data-testid="stAppViewContainer"] { background-color: #FFFFFF !important; }
    [data-testid="stHeader"] { background-color: #FFFFFF !important; }
    
    /* GLOBAL FONTS - Standard System Fonts for Readability */
    * { color: #111111; }

    /* TITLE */
    h1 {
        font-weight: 800 !important;
        background: -webkit-linear-gradient(45deg, #820AD1, #B220E8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem !important;
        margin-bottom: 0px !important;
        padding-top: 10px !important;
    }
    
    .subtitle {
        color: #6B7280;
        font-size: 1.1rem;
        margin-bottom: 30px;
    }

    /* UPLOAD CARD */
    [data-testid="stFileUploader"] {
        background-color: #FAFAFA;
        border: 2px dashed #E5E7EB;
        border-radius: 15px;
        padding: 20px;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #820AD1;
        background-color: #F8F5FF;
    }

    /* PREVIEW CARD */
    .preview-container {
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 10px;
        background-color: #FAFAFA;
        text-align: center;
    }

    /* SLIDER (Standard Streamlit Color) */
    div[data-baseweb="slider"] div { background-color: #820AD1 !important; }

    /* HIDE CHROME */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. CORE LOGIC (With Caching for Speed) ---

def clean_page_logic(page, header_height, footer_height, text_input, match_case):
    """Core cleaning logic applied to a page object"""
    # 1. MAGIC ERASER
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

    # 2. AREA WIPERS
    rect = page.rect
    # Smart color detection (Bottom Left)
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

# CACHED PREVIEW FUNCTION (This makes it fast!)
# We cache based on inputs so it doesn't re-run heavy logic unnecessarily
@st.cache_data(show_spinner=False)
def get_preview_image(file_bytes, header_h, footer_h, txt, case):
    """Extracts Page 1 and applies cleaning for preview"""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    if len(doc) < 1: return None
    
    page = doc[0] # Only process page 1
    clean_page_logic(page, header_h, footer_h, txt, case)
    
    # Render low DPI for super fast preview
    pix = page.get_pixmap(dpi=72) 
    return Image.open(io.BytesIO(pix.tobytes("png")))

def process_full_document(file_bytes, header_h, footer_h, txt, case):
    """Processes the entire file"""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    output_buffer = io.BytesIO()
    doc.set_metadata({}) 
    
    for page in doc:
        clean_page_logic(page, header_h, footer_h, txt, case)
    
    doc.save(output_buffer)
    output_buffer.seek(0)
    return output_buffer

# --- 4. THE UI ---

st.markdown('<h1>DocPolish</h1>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Professional Document Studio</div>', unsafe_allow_html=True)

# Layout: 40% Controls | 60% Preview
col_controls, col_preview = st.columns([2, 3], gap="large")

with col_controls:
    st.markdown("### 1. Upload")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")
    
    if uploaded_file:
        st.write("---")
        st.markdown("### 2. Controls")
        
        # MAGIC ERASER (No Expander - Cleaner)
        st.markdown("**🪄 Magic Text Eraser**")
        st.caption("Remove specific words (comma separated).")
        text_input = st.text_input("Text to remove", placeholder="e.g. Confidential, Draft")
        match_case = st.checkbox("Match Case", value=False)
        
        st.write("")
        
        # SLIDERS
        st.markdown("**📏 Area Wipers**")
        header_height = st.slider("Top Header Height", 0, 150, 0)
        footer_height = st.slider("Bottom Footer Height", 0, 150, 0)

with col_preview:
    if uploaded_file:
        st.markdown("### 3. Live Preview (Page 1)")
        
        # LIVE PREVIEW CONTAINER
        with st.container():
            # This runs fast because of caching
            preview_img = get_preview_image(
                uploaded_file.getvalue(), 
                header_height, 
                footer_height, 
                text_input, 
                match_case
            )
            
            if preview_img:
                st.image(preview_img, use_container_width=True)
            else:
                st.error("Could not load preview.")

# --- 5. SINGLE ACTION BUTTON ---
if uploaded_file:
    st.write("---")
    
    # We use a placeholder to swap buttons
    action_col1, action_col2, action_col3 = st.columns([1, 2, 1])
    
    with action_col2:
        # LOGIC: 
        # Since calculating full PDF is heavy, we put it behind a button.
        # Once clicked, we show the download button immediately.
        
        if "processed_data" not in st.session_state:
            st.session_state.processed_data = None

        # The "Trigger" Button
        if st.button("⚡ Process & Prepare Download", type="primary", use_container_width=True):
            with st.spinner("Processing full document..."):
                # Run full process
                st.session_state.processed_data = process_full_document(
                    uploaded_file.getvalue(),
                    header_height,
                    footer_height,
                    text_input,
                    match_case
                )
                st.rerun() # Refresh to show download button

        # If data is ready, show the Download Button
        if st.session_state.processed_data:
            st.download_button(
                label="⬇️ Download Clean PDF Now",
                data=st.session_state.processed_data,
                file_name=f"Clean_{uploaded_file.name}",
                mime="application/pdf",
                use_container_width=True
            )
            # Optional: Reset button to start over
            if st.button("Start Over"):
                st.session_state.processed_data = None
                st.rerun()
