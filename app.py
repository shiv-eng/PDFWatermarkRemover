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

# --- 2. SAFE CSS (No Slider Hacks) ---
st.markdown("""
    <style>
    /* FORCE LIGHT THEME */
    [data-testid="stAppViewContainer"] { background-color: #FFFFFF !important; }
    [data-testid="stHeader"] { background-color: #FFFFFF !important; }
    
    /* FONTS & TEXT */
    * { font-family: 'Inter', sans-serif !important; color: #111111; }
    
    /* TITLE */
    h1 {
        font-weight: 800 !important;
        background: -webkit-linear-gradient(45deg, #820AD1, #B220E8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem !important;
        padding-top: 1rem;
    }

    /* UPLOAD AREA */
    [data-testid="stFileUploader"] {
        background-color: #FAFAFA;
        border: 2px dashed #E5E7EB;
        border-radius: 12px;
        padding: 20px;
    }

    /* HIDE STREAMLIT MENU */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIC ---

def clean_page_logic(page, header_height, footer_height, text_input, match_case):
    """Core cleaning logic"""
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

@st.cache_data(show_spinner=False)
def get_preview_image(file_bytes, header_h, footer_h, txt, case):
    """Fast Cached Preview (Page 1 Only)"""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    if len(doc) < 1: return None
    page = doc[0]
    clean_page_logic(page, header_h, footer_h, txt, case)
    pix = page.get_pixmap(dpi=72)
    return Image.open(io.BytesIO(pix.tobytes("png")))

def process_full_document(file_bytes, header_h, footer_h, txt, case):
    """Process Entire PDF"""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    output_buffer = io.BytesIO()
    doc.set_metadata({}) 
    
    for page in doc:
        clean_page_logic(page, header_h, footer_h, txt, case)
    
    doc.save(output_buffer)
    output_buffer.seek(0)
    return output_buffer

# --- 4. UI LAYOUT ---

st.markdown('<h1>DocPolish</h1>', unsafe_allow_html=True)
st.markdown('<div style="color: #666; margin-bottom: 30px;">Professional Document Sanitization</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 1. Upload")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")
    
    if uploaded_file:
        st.write("---")
        st.markdown("### 2. Controls")
        
        st.markdown("**🪄 Magic Text Eraser**")
        st.caption("Remove specific words (comma separated).")
        text_input = st.text_input("Text to remove", placeholder="e.g. Confidential, Draft")
        match_case = st.checkbox("Match Case", value=False)
        
        st.write("")
        st.markdown("**📏 Area Wipers**")
        
        # SLIDERS (Native Streamlit = Bug Free)
        header_height = st.slider("Top Header Height", 0, 150, 0)
        footer_height = st.slider("Bottom Footer Height", 0, 150, 0)

with col2:
    if uploaded_file:
        st.markdown("### 3. Live Preview")
        preview_img = get_preview_image(uploaded_file.getvalue(), header_height, footer_height, text_input, match_case)
        if preview_img:
            st.image(preview_img, use_container_width=True)

# --- 5. ACTION AREA (Single Flow) ---
if uploaded_file:
    st.write("---")
    
    # Center the button area
    c_action1, c_action2, c_action3 = st.columns([1, 2, 1])
    
    with c_action2:
        # Initialize session state for the download
        if "clean_pdf_data" not in st.session_state:
            st.session_state.clean_pdf_data = None

        # IF we haven't processed yet, show the Process Button
        if st.session_state.clean_pdf_data is None:
            if st.button("⚡ Process & Download", type="primary", use_container_width=True):
                with st.status("Processing Document...", expanded=True) as status:
                    st.write("Reading file...")
                    data = process_full_document(
                        uploaded_file.getvalue(),
                        header_height,
                        footer_height,
                        text_input,
                        match_case
                    )
                    st.session_state.clean_pdf_data = data
                    status.update(label="Complete!", state="complete", expanded=False)
                st.rerun()
        
        # IF processed, show the Download Button instead
        else:
            st.success("✅ Document Ready!")
            st.download_button(
                label="⬇️ Save Clean PDF",
                data=st.session_state.clean_pdf_data,
                file_name=f"Clean_{uploaded_file.name}",
                mime="application/pdf",
                use_container_width=True
            )
            
            # Button to reset and process again (e.g. if they changed settings)
            if st.button("↻ Process Again (New Settings)"):
                st.session_state.clean_pdf_data = None
                st.rerun()
