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

# --- 2. CLEAN CSS (Fixes Font Bugs) ---
st.markdown("""
    <style>
    /* GLOBAL SETTINGS - Targeted to avoid breaking icons */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* REMOVE DEFAULT PADDING */
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

    /* TITLE STYLE */
    h1 {
        font-weight: 800 !important;
        background: -webkit-linear-gradient(45deg, #820AD1, #B220E8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* SUBTITLE */
    .subtitle {
        color: #6B7280;
        font-size: 1rem;
        margin-bottom: 2rem;
    }

    /* UPLOAD AREA */
    [data-testid="stFileUploader"] {
        background-color: #FAFAFA;
        border: 2px dashed #E5E7EB;
        border-radius: 15px;
        padding: 15px;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #820AD1;
        background-color: #F8F5FF;
    }

    /* TOOL CARDS (Replaces Expanders) */
    .tool-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .tool-header {
        font-weight: 700;
        color: #111;
        margin-bottom: 5px;
        font-size: 1rem;
        display: flex;
        align-items: center;
        gap: 8px;
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
    
    /* HIDE STREAMLIT CHROME */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIC ---
def clean_page(page, header_height, footer_height, text_to_remove, match_case, whole_word):
    """Applies cleaning logic to a single page"""
    # 1. MAGIC ERASER (Text)
    if text_to_remove:
        words = page.get_text("words")
        for w in words:
            word_text = w[4]
            word_rect = fitz.Rect(w[0], w[1], w[2], w[3])
            
            if match_case:
                is_match = (text_to_remove == word_text) if whole_word else (text_to_remove in word_text)
            else:
                is_match = (text_to_remove.lower() == word_text.lower()) if whole_word else (text_to_remove.lower() in word_text.lower())

            if is_match:
                page.add_redact_annot(word_rect, fill=None)
        page.apply_redactions()

    # 2. AREA WIPERS (Header & Footer)
    rect = page.rect
    # Smart color detection (Bottom Left)
    clip_rect = fitz.Rect(0, rect.height - 10, 1, rect.height - 9)
    pix = page.get_pixmap(clip=clip_rect)
    r, g, b = pix.pixel(0, 0)
    dynamic_color = (r/255, g/255, b/255)

    # Footer Redaction
    if footer_height > 0:
        footer_rect = fitz.Rect(0, rect.height - footer_height, rect.width, rect.height)
        shape = page.new_shape()
        shape.draw_rect(footer_rect)
        shape.finish(color=dynamic_color, fill=dynamic_color, width=0)
        shape.commit()

    # Header Redaction
    if header_height > 0:
        header_rect = fitz.Rect(0, 0, rect.width, header_height)
        shape = page.new_shape()
        shape.draw_rect(header_rect)
        shape.finish(color=dynamic_color, fill=dynamic_color, width=0)
        shape.commit()
        
    return page

def generate_preview(input_bytes, header_height, footer_height, text_to_remove, match_case, whole_word):
    """Generates preview image of Page 1"""
    doc = fitz.open(stream=input_bytes, filetype="pdf")
    if len(doc) < 1: return None
    page = doc[0]
    clean_page(page, header_height, footer_height, text_to_remove, match_case, whole_word)
    pix = page.get_pixmap(dpi=120)
    return Image.open(io.BytesIO(pix.tobytes("png")))

def process_all_pages(input_bytes, header_height, footer_height, text_to_remove, match_case, whole_word):
    """Processes full document"""
    doc = fitz.open(stream=input_bytes, filetype="pdf")
    output_buffer = io.BytesIO()
    doc.set_metadata({}) 
    
    for page in doc:
        clean_page(page, header_height, footer_height, text_to_remove, match_case, whole_word)
    
    doc.save(output_buffer)
    output_buffer.seek(0)
    return output_buffer, len(doc)

# --- 4. THE UI LAYOUT ---

# Header Section
st.markdown('<h1>DocPolish</h1>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Professional Document Cleanser</div>', unsafe_allow_html=True)

# Two Column Layout
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown("### 1. Upload")
    uploaded_file = st.file_uploader("Drop PDF Document", type="pdf")
    
    if uploaded_file:
        st.write("")
        st.markdown("### 2. Controls")
        
        # --- MAGIC ERASER CARD ---
        st.markdown('<div class="tool-card"><div class="tool-header">🪄 Magic Text Eraser</div>', unsafe_allow_html=True)
        t_col1, t_col2 = st.columns([2,1])
        with t_col1:
            text_to_remove = st.text_input("Word to remove", placeholder="e.g. Confidential")
        with t_col2:
            match_case = st.checkbox("Match Case", value=False)
            whole_word = st.checkbox("Whole Word", value=True)
        st.caption("Removes specific words from anywhere on the page.")
        st.markdown('</div>', unsafe_allow_html=True) # End card
        
        # --- SLIDERS CARD ---
        st.markdown('<div class="tool-card"><div class="tool-header">📏 Area Wipers</div>', unsafe_allow_html=True)
        
        header_height = st.slider("Header Height (Top)", 0, 150, 0)
        footer_height = st.slider("Footer Height (Bottom)", 0, 150, 0)
        st.caption("Slide to cover persistent headers or footers.")
        st.markdown('</div>', unsafe_allow_html=True) # End card

with col_right:
    if uploaded_file:
        st.markdown("### 3. Live Preview")
        
        # PREVIEW BOX
        with st.container():
            with st.spinner("Refreshing preview..."):
                preview_img = generate_preview(
                    uploaded_file.getvalue(), 
                    header_height, 
                    footer_height, 
                    text_to_remove, 
                    match_case, 
                    whole_word
                )
                
                if preview_img:
                    st.image(preview_img, use_container_width=True)
                    st.caption("Page 1 Preview (Updates automatically)")

# --- 5. ACTION BAR ---
if uploaded_file:
    st.write("---")
    
    # Centered Download Area
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("⚡ Process & Download", type="primary"):
            
            # BEAUTIFUL LOADER
            with st.status("Processing Document...", expanded=True) as status:
                st.write("🔍 Scanning pages...")
                time.sleep(0.5)
                st.write("🪄 Removing watermarks...")
                time.sleep(0.5)
                st.write("💾 Compressing file...")
                
                # Actual Processing
                cleaned_data, page_count = process_all_pages(
                    uploaded_file.getvalue(), 
                    header_height, 
                    footer_height, 
                    text_to_remove, 
                    match_case, 
                    whole_word
                )
                
                status.update(label="✅ Ready!", state="complete", expanded=False)
            
            # Results
            st.balloons()
            st.success(f"Successfully Cleaned {page_count} Pages")
            
            st.download_button(
                label="⬇️ Click to Download PDF",
                data=cleaned_data,
                file_name=f"Clean_{uploaded_file.name}",
                mime="application/pdf"
            )
