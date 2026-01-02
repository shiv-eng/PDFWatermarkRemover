import streamlit as st
import fitz  # PyMuPDF
import io
import uuid
import time
from PIL import Image
from collections import Counter

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="PDF Watermark Remover",
    page_icon="💧",
    layout="wide"
)

# --- 2. CSS STYLING ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Clean Expander */
[data-testid="stExpander"] {
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    background-color: #FAFAFA;
}

/* File Uploader */
[data-testid="stFileUploader"] {
    background-color: #FFFFFF;
    border: 2px dashed #E5E7EB;
    border-radius: 20px;
    padding: 30px;
}

/* Auto-detect info box */
.auto-detect-box {
    background: linear-gradient(to right, #F0FDF4, #DCFCE7);
    border: 1px solid #BBF7D0;
    color: #166534;
    padding: 12px 20px;
    border-radius: 12px;
    margin-bottom: 20px;
    font-size: 0.95rem;
}

.hero-container { text-align: center; margin-bottom: 40px; padding: 20px 0; }

.hero-title {
    font-weight: 800;
    background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3.5rem;
    margin-bottom: 8px;
}

.hero-subtitle { color: #6B7280; font-size: 1.2rem; }

.stDownloadButton > button {
    background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%);
    color: white !important;
    border: none;
    padding: 0.6rem 2rem;
    border-radius: 10px;
    font-weight: 600;
    width: 100%;
}

[data-testid="stHeader"], footer { display: none !important; }
.block-container { padding-top: 2rem !important; }
div[data-testid="stImage"] { display: flex; justify-content: center; }
</style>
""", unsafe_allow_html=True)

# --- 3. CORE LOGIC ---

def detect_watermark_candidates(file_bytes):
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        page_limit = min(5, len(doc))
        text_counts = Counter()

        for i in range(page_limit):
            page = doc[i]
            blocks = [b[4].strip() for b in page.get_text("blocks") if len(b[4].strip()) > 3]
            text_counts.update(blocks)

        threshold = max(2, page_limit - 1)
        return ", ".join([t for t, c in text_counts.items() if c >= threshold])
    except:
        return ""

def clean_page_logic(page, header_h, footer_h, keywords_str, match_case):
    if keywords_str:
        keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
        for keyword in keywords:
            for quad in page.search_for(keyword):
                if match_case:
                    txt = page.get_text("text", clip=quad)
                    if keyword not in txt:
                        continue
                page.add_redact_annot(quad, fill=None)
        page.apply_redactions()

    rect = page.rect
    clip = fitz.Rect(0, rect.height - 10, 1, rect.height - 9)
    pix = page.get_pixmap(clip=clip)
    r, g, b = pix.pixel(0, 0)
    bg = (r / 255, g / 255, b / 255)

    if footer_h > 0:
        page.draw_rect(
            fitz.Rect(0, rect.height - footer_h, rect.width, rect.height),
            color=bg, fill=bg
        )

    if header_h > 0:
        page.draw_rect(
            fitz.Rect(0, 0, rect.width, header_h),
            color=bg, fill=bg
        )

@st.cache_data(show_spinner=False, ttl=3600)
def get_preview_image(file_bytes, header_h, footer_h, txt, case):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    if len(doc) == 0:
        return None
    page = doc[0]
    clean_page_logic(page, header_h, footer_h, txt, case)
    pix = page.get_pixmap(dpi=150)
    return Image.open(io.BytesIO(pix.tobytes("png")))

@st.cache_data(show_spinner=False, ttl=3600)
def process_full_document(file_bytes, header_h, footer_h, txt, case):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    out = io.BytesIO()
    doc.set_metadata({})
    for page in doc:
        clean_page_logic(page, header_h, footer_h, txt, case)
    doc.save(out)
    out.seek(0)
    return out

# --- 4. UI ---

st.markdown("""
<div class="hero-container">
    <div class="hero-title">PDF Watermark Remover</div>
    <div class="hero-subtitle">Clean, Professional, and Private Document Processing</div>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns([1, 6, 1])
with c2:
    uploaded_file = st.file_uploader("Drop your PDF here to start", type="pdf", label_visibility="collapsed")

if uploaded_file:
    file_bytes = uploaded_file.getvalue()
    sig = f"{uploaded_file.name}_{uploaded_file.size}"

    if st.session_state.get("current_file_signature") != sig:
        with st.spinner("🚀 Initializing auto-clean..."):
            st.session_state.detected_text = detect_watermark_candidates(file_bytes)
            st.session_state.current_file_signature = sig
            st.session_state.uid = uuid.uuid4().hex
            time.sleep(0.4)

if not uploaded_file:
    col1, col2, col3 = st.columns(3)
    col1.markdown("### ⚡ Auto-Detect")
    col1.caption("Identifies repetitive text automatically.")
    col2.markdown("### 🎨 Smart Fill")
    col2.caption("Replaces removed areas with background color.")
    col3.markdown("### 🛡️ Private")
    col3.caption("Files are processed in memory only.")

else:
    st.markdown(f"""
    <div class="auto-detect-box">
        ✨ <b>Auto-Clean Applied!</b> Detected watermarks:
        <i>{st.session_state.get("detected_text", "None")}</i>
    </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        col_s, col_p = st.columns([3, 2], gap="large")
        uid = st.session_state.uid

        with col_s:
            with st.expander("Advanced Options (Click to Edit)", expanded=False):
                txt = st.text_input("Keywords", value=st.session_state.detected_text, key=f"txt_{uid}")
                match_case = st.checkbox("Match Case", value=False, key=f"case_{uid}")
                header_h = st.slider("Top Margin Cut", 0, 150, 0, key=f"h_{uid}")
                footer_h = st.slider("Bottom Margin Cut", 0, 150, 25, key=f"f_{uid}")

            final_pdf = process_full_document(file_bytes, header_h, footer_h, txt, match_case)
            st.download_button(
                "📥 Download Clean PDF",
                data=final_pdf,
                file_name=f"Clean_{uploaded_file.name}",
                mime="application/pdf"
            )

        with col_p:
            st.subheader("👁️ Preview")
            preview = get_preview_image(file_bytes, header_h, footer_h, txt, match_case)
            if preview:
                st.image(preview, width=450)

# --- FOOTER (ORIGINAL – UNCHANGED) ---
st.markdown("""
<div style="text-align: center; margin-top: 60px; border-top: 1px solid #E5E7EB; padding-top: 20px;">
    <img src="https://visitor-badge.laobi.icu/badge?page_id=pdfwatermarkremover.streamlit.app&left_text=Total%20Visits&left_color=%231F2937&right_color=%232563EB" alt="Visitor Count">
</div>
""", unsafe_allow_html=True)
