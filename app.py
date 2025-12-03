import streamlit as st
import fitz  # PyMuPDF
import io
import time

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="DocPolish",
    page_icon="🧠",
    layout="centered"
)

# --- 2. INTELLIGENT STYLING ---
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

    /* SMART INPUT FIELDS */
    .stTextInput input {
        border-radius: 10px;
        border: 1px solid #E5E7EB;
        padding: 10px 15px;
        color: #111;
    }
    .stTextInput input:focus {
        border-color: #820AD1;
        box-shadow: 0 0 0 1px #820AD1;
    }

    /* SLIDER COLOR */
    div[data-baseweb="slider"] div { background-color: #820AD1 !important; }

    /* SUCCESS BUBBLE */
    .success-box {
        background-color: #F3E8FF;
        color: #6D08AF;
        padding: 15px;
        border-radius: 12px;
        font-weight: 600;
        text-align: center;
        margin-bottom: 12px;
        border: 1px solid #D8B4FE;
        width: 100%; 
        box-sizing: border-box;
    }

    /* DOWNLOAD BUTTON */
    .stDownloadButton > button {
        background-color: #820AD1 !important;
        color: white !important;
        border-radius: 12px !important;
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

# --- 3. SMART ENGINE LOGIC ---
def process_pdf(input_bytes, footer_height, text_to_remove, match_case, whole_word):
    doc = fitz.open(stream=input_bytes, filetype="pdf")
    output_buffer = io.BytesIO()
    
    # 1. Privacy Scrub (Metadata Wipe)
    doc.set_metadata({}) 
    
    for page in doc:
        # --- ENGINE A: SMART TEXT HUNTER ---
        if text_to_remove:
            # Get every word with its location
            words = page.get_text("words")
            
            for w in words:
                word_text = w[4] # The text string
                word_rect = fitz.Rect(w[0], w[1], w[2], w[3]) # The coordinates
                
                # Check 1: Case Sensitivity
                if match_case:
                    # Strict: "Confidential" != "CONFIDENTIAL"
                    text_match = (text_to_remove == word_text)
                    if not whole_word:
                        text_match = (text_to_remove in word_text)
                else:
                    # Loose: "confidential" == "CONFIDENTIAL"
                    text_match = (text_to_remove.lower() == word_text.lower())
                    if not whole_word:
                        text_match = (text_to_remove.lower() in word_text.lower())

                # Fire Laser if matched
                if text_match:
                    page.add_redact_annot(word_rect, fill=None)
            
            # Apply redactions for this page
            page.apply_redactions()

        # --- ENGINE B: FOOTER POLISHER ---
        if footer_height > 0:
            rect = page.rect
            clip_rect = fitz.Rect(0, rect.height - 10, 1, rect.height - 9)
            pix = page.get_pixmap(clip=clip_rect)
            r, g, b = pix.pixel(0, 0)
            dynamic_color = (r/255, g/255, b/255)
            
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
st.markdown('<p class="subtitle">The Smartest Way to Clean PDFs.</p>', unsafe_allow_html=True)

# Main Container
c1, c2, c3 = st.columns([1, 8, 1])

with c2:
    uploaded_file = st.file_uploader("Drop PDF here", type="pdf")
    
    if uploaded_file:
        st.write("")
        
        # --- SECTION 1: MAGIC ERASER ---
        st.markdown("**🪄 Magic Text Eraser**")
        
        col_input, col_opt = st.columns([2, 1])
        with col_input:
            text_to_remove = st.text_input("Text to remove", placeholder="e.g. CONFIDENTIAL", label_visibility="collapsed")
        
        with col_opt:
            # Smart Toggles
            match_case = st.checkbox("Match Case", value=True, help="Strict matching. 'Draft' will NOT remove 'DRAFT'.")
            whole_word = st.checkbox("Whole Word", value=True, help="Safe mode. 'Draft' will NOT remove 'Drafting'.")
        
        st.write("")
        
        # --- SECTION 2: FOOTER POLISH ---
        st.markdown("**📏 Footer Polish**")
        st.caption("Slide to cover persistent footer text.")
        footer_height = st.slider("", 0, 100, 0, label_visibility="collapsed")
        
        st.write("---") 
        
        # --- PROCESSING ---
        if footer_height > 0 or text_to_remove:
            with st.spinner("🤖 AI Polishing in progress..."):
                cleaned_data, page_count = process_pdf(uploaded_file.getvalue(), footer_height, text_to_remove, match_case, whole_word)
                time.sleep(0.5)
            
            # Success Message
            st.markdown(f'<div class="success-box">✨ Smart-Cleaned {page_count} Pages</div>', unsafe_allow_html=True)
            
            # Download Button
            st.download_button(
                label="Download Result",
                data=cleaned_data,
                file_name=f"Clean_{uploaded_file.name}",
                mime="application/pdf"
            )

# Footer Trust Signals
st.write("")
st.write("")
st.markdown("""
<div style="display: flex; justify-content: center; gap: 40px; margin-top: 30px; opacity: 0.8;">
    <div style="text-align: center;">
        <span style="font-size: 1.5rem;">🧠</span>
        <div style="font-size: 0.8rem; font-weight: 600;">Smart Match</div>
    </div>
    <div style="text-align: center;">
        <span style="font-size: 1.5rem;">🛡️</span>
        <div style="font-size: 0.8rem; font-weight: 600;">Text Safe</div>
    </div>
    <div style="text-align: center;">
        <span style="font-size: 1.5rem;">🔒</span>
        <div style="font-size: 0.8rem; font-weight: 600;">Private</div>
    </div>
</div>
""", unsafe_allow_html=True)
