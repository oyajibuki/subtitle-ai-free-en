import streamlit as st
import sys
import os

# Workaround for sys.stdout/sys.stderr being None when using PyInstaller --noconsole
class DummyStream:
    def write(self, *args, **kwargs): pass
    def flush(self, *args, **kwargs): pass

if sys.stdout is None:
    sys.stdout = DummyStream()
if sys.stderr is None:
    sys.stderr = DummyStream()

import whisper
import pandas as pd
from datetime import timedelta
from moviepy import VideoFileClip
import streamlit.components.v1 as components

# --- FFmpeg Path Setup ---
os.environ["PATH"] = os.getcwd() + os.pathsep + os.environ["PATH"]

# --- Settings and Utility Functions ---

def format_timestamp(seconds):
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)"""
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

def create_srt_content(df):
    """Generate SRT format string from DataFrame"""
    # Free version: force a watermark ad at the beginning
    srt_content = "1\n00:00:00,000 --> 00:00:05,000\n[Created by AI Subtitle Free]\n\n"
    
    for idx, row in df.iterrows():
        start = format_timestamp(row['start'])
        end = format_timestamp(row['end'])
        text = row['text']
        srt_content += f"{idx + 2}\n{start} --> {end}\n{text}\n\n"
    return srt_content

def save_uploaded_file(uploaded_file):
    """Save uploaded file as a temporary file"""
    try:
        temp_dir = os.path.join(os.getcwd(), "temp_files")
        os.makedirs(temp_dir, exist_ok=True)
        
        file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    except Exception as e:
        st.error(f"File save error: {e}")
        return None

def get_video_duration(file_path):
    """Get the duration of a video/audio file (in seconds)"""
    try:
        with VideoFileClip(file_path) as clip:
            return clip.duration
    except Exception as e:
        return 0

# --- Model Loading (Cached) ---
@st.cache_resource
def load_model(model_size):
    return whisper.load_model(model_size)

# --- Application Main ---

st.set_page_config(page_title="AI Subtitle Generator (Free Edition)", layout="centered")

st.title("🎥 AI Subtitle Generator\n(Free Edition)")
st.info("This is a **free trial version** with limited features. [Contact us for Pro version](https://oyajibuki.github.io/form/)")

st.markdown("""
### ⚠️ Limitations
- **Video length**: Up to 5 minutes (300 seconds)
- **File size**: Up to 100MB
- **AI model**: tiny, base only
- **Output format**: SRT (subtitle file) only
""")

# Sidebar settings
with st.sidebar:
    st.header("⚙️ Speech Recognition Settings")
    # Free version: tiny and base only
    model_map = {
        "tiny (Fastest)": "tiny",
        "base (Standard)": "base"
    }
    model_label = st.selectbox(
        "AI Model Size",
        list(model_map.keys()),
        index=1,
        help="""
        - tiny (Fastest): Lightest and fastest. Lower accuracy.
        - base (Standard): Standard speed and accuracy.
        
        * Smart/Pro models are not available in the Free version.
        """
    )
    model_size = model_map[model_label]
    
    # English version: English only
    language = "English"
    lang_code = "en"
    st.caption(f"🌐 Language: {language}")

    st.divider()
    st.caption("🔒 Pro Version Features")
    st.markdown("""
    - High-accuracy models (Smart/Pro)
    - Font/color style editing
    - ASS format (styled subtitles) output
    - No video length or file size limits
    """)

    st.divider()
    
    # ---------------------------
    # GAS Visitor Counter
    # ---------------------------
    if 'visitor_count' not in st.session_state:
        try:
            import urllib.request
            import json
            url = "https://script.google.com/macros/s/AKfycbznxYkj5ixnK_pHkGR8LUYhEYdvSYpaiF3x4LaZy964wlu068oak1X1uuIiyqCEtGWF/exec?page=subtitle-ai-free-en"
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode('utf-8'))
                st.session_state['visitor_count'] = data['count']
        except Exception:
            st.session_state['visitor_count'] = None

    if st.session_state['visitor_count'] is not None:
        st.caption(f"👀 Visitors: {st.session_state['visitor_count']}")

# Main area

# JS to hide the file uploader "Limit ..." text
components.html(
    """
    <script>
    function hideLimitText() {
        const elements = window.parent.document.querySelectorAll('*');
        elements.forEach(el => {
            if (el.tagName !== 'BODY' && el.tagName !== 'HTML' && el.children.length === 0) {
                 if (el.textContent && (el.textContent.includes('Limit') && (el.textContent.includes('MB') || el.textContent.includes('GB')))) {
                    el.style.display = 'none';
                    el.style.visibility = 'hidden';
                    el.innerHTML = '';
                }
            }
        });
        
        const uploaders = window.parent.document.querySelectorAll('[data-testid="stFileUploader"] small');
        uploaders.forEach(el => el.style.display = 'none');
    }
    hideLimitText();
    setInterval(hideLimitText, 500);
    </script>
    """,
    height=0,
    width=0
)

# CSS backup and watermark
st.markdown(
    """
    <style>
    /* Full-screen diagonal watermark */
    .watermark-bg {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) rotate(-35deg);
        font-size: 6vw;
        color: rgba(150, 150, 150, 0.12);
        z-index: 999999;
        pointer-events: none;
        white-space: nowrap;
        user-select: none;
        font-weight: 900;
        letter-spacing: 5px;
    }
    
    /* Hide small text */
    [data-testid="stFileUploader"] small {
        display: none !important;
        opacity: 0 !important;
        visibility: hidden !important;
        font-size: 0 !important;
    }
    [data-testid="stFileUploader"] section > div > div > small {
        display: none !important;
    }
    [data-testid="stFileUploader"] span {
        font-size: 14px !important;
    }
    </style>
    <div class="watermark-bg">Created by AI Subtitle Free</div>
    """,
    unsafe_allow_html=True
)

st.caption("Supported formats: mp4, mov, wav, mp3, m4a, mk4")
uploaded_file = st.file_uploader("Drag & drop a video or audio file (up to 5 min / 100MB)", type=["mp4", "mov", "wav", "mp3", "m4a", "mk4"])

if uploaded_file is not None:
    # Size check (100MB)
    if uploaded_file.size > 100 * 1024 * 1024:
        st.error("⚠️ File size exceeds the limit (100MB).\nOnly files under 100MB are available in the Free version.")
    else:
        temp_file_path = save_uploaded_file(uploaded_file)
    
    if temp_file_path:
        # Media preview
        st.markdown("### Preview")
        col_preview, col_empty = st.columns([1, 2])
        with col_preview:
            if any(ext in uploaded_file.name for ext in ["mp4", "mov"]):
                st.video(temp_file_path)
            else:
                st.audio(temp_file_path)

        st.markdown("### Start Transcription")
        
        # Duration check
        duration = get_video_duration(temp_file_path)
        if duration > 300: # 5 min = 300 sec
            st.error(f"⚠️ Video length exceeds the limit ({int(duration)} seconds).\nOnly videos up to 5 minutes (300 seconds) can be processed in the Free version.")
        else:
            # Transcription button
            if st.button("🚀 Start Transcription (Free)", type="primary"):
                with st.spinner(f"Analyzing with {model_size} model..."):
                    try:
                        model = load_model(model_size)
                        result = model.transcribe(temp_file_path, language=lang_code)
                        
                        st.session_state['free_segments'] = result['segments']
                        st.success("Transcription complete!")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")

# Results display and editing area
if 'free_segments' in st.session_state:
    st.divider()
    st.header("📝 Review Subtitle Data")
    
    df = pd.DataFrame(st.session_state['free_segments'])
    if 'text' not in df.columns:
         st.error("Invalid data.")
    else:
        edit_df = df[['start', 'end', 'text']].copy()
        
        edited_df = st.data_editor(
            edit_df,
            column_config={
                "start": st.column_config.NumberColumn("Start", format="%.2f"),
                "end": st.column_config.NumberColumn("End", format="%.2f"),
                "text": st.column_config.TextColumn("Content", width="large"),
            },
            num_rows="dynamic",
            use_container_width=True
        )

        st.subheader("📥 Download")
        srt_content = create_srt_content(edited_df)
        
        st.download_button(
            label="Save SRT File",
            data=srt_content,
            file_name="subtitles_free.srt",
            mime="text/plain",
            use_container_width=True
        )
        
        st.info("💡 Tip: For ASS format output and advanced style settings, please use the Pro version.")
