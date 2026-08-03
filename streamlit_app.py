import streamlit as st
import tempfile

from pathlib import Path
from pdf_reader import extract_text
from smart_pdf import process_smart_pdf
from table_reader import NoTableFoundError
from table_to_audio import process_table
from tts_engine import text_to_mp3

st.set_page_config(page_title="pyt-tts", page_icon="🎙️", layout="centered")

st.title("🎙️ pyt-tts")
st.caption("Turn text, PDFs, or tables into MP3 audio.")

tab_text, tab_pdf, tab_table, tab_smart = st.tabs(
    ["Text to Audio", "PDF to Audio", "Table to Audio", "Smart PDF"]
)

def _save_uploaded_file(uploaded_file) -> str:
    suffix = Path(uploaded_file.name).suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded_file.getvalue())
    tmp.close()
    return tmp.name

def _offer_audio(mp3_path: str, download_name: str):
    audio_bytes = Path(mp3_path).read_bytes()
    st.audio(audio_bytes, format="audio/mp3")
    st.download_button(
        "⬇️ Download MP3", data=audio_bytes, file_name=download_name, mime="audio/mpeg"
    )

def _offer_chart(png_path: str, download_name: str, caption: str = ""):
    png_bytes = Path(png_path).read_bytes()
    st.image(png_bytes, caption=caption)
    st.download_button(
        "⬇️ Download chart (PNG)",
        data=png_bytes,
        file_name=download_name,
        mime="image/png",
        key=download_name,
    )


with tab_text:
    st.subheader("Text to Audio")

    text_input = st.text_area("Enter text", height=200, placeholder="Paste or type text here...")
    uploaded_txt = st.file_uploader("...or upload a .txt file", type=["txt"])
    filename = st.text_input("Output file name", value="text_output", key="text_filename")

    if st.button("Generate MP3", key="text_generate"):
        text = text_input.strip()
        if uploaded_txt is not None:
            text = uploaded_txt.getvalue().decode("utf-8").strip()

        if not text:
            st.warning("Please enter or upload some text first.")
        else:
            with st.spinner("Generating audio..."):
                try:
                    with tempfile.TemporaryDirectory() as tmp_dir:
                        mp3_path = str(Path(tmp_dir) / f"{filename or "text_output"}.mp3")
                        text_to_mp3(text, mp3_path)
                        _offer_audio(mp3_path, f"{filename or "text_output"}.mp3 ")
                except Exception as e:
                    st.error(f"Error: {e}")


with tab_pdf:
    st.subheader("PDF to Audio")

    uploaded_pdf = st.file_uploader("Choose a PDF file", type=["pdf"], key="pdf_uploader")
    pdf_filename = st.text_input(
        "Output file name",
        value=Path(uploaded_pdf.name).stem if uploaded_pdf else "pdf_output",
        key="pdf_filename",
    )

    if st.button("Generate MP3", key="pdf_generate"):
        if uploaded_pdf is None:
            st.warning("Please choose a PDF file first.")
        else:
            with st.spinner("Extracting text and generating audio..."):
                try:
                    pdf_path = _save_uploaded_file(uploaded_pdf)
                    text = extract_text(pdf_path)
                    if not text or not text.strip():
                        st.error(
                            "Could not extract text from PDF "
                            "(Scanned/image-based PDF?) in that case use SMART"
                        )
                    else:
                        with tempfile.TemporaryDirectory() as tmp_dir:
                            mp3_path = str(Path(tmp_dir) / f"{pdf_filename}.mp3")
                            text_to_mp3(text, mp3_path)
                            _offer_audio(mp3_path, f"{pdf_filename}.mp3")
                except Exception as e:
                    st.error(f"Error: {e}")


with tab_table:
    st.subheader("Table to Audio")

    uploaded_table = st.file_uploader(
        "Choose a table file (.csv, .xlsx, .pdf)",
        type=["csv", "xlsx", "pdf"],
        key="table_uploader",
    )
    table_filename = st.text_input(
        "Output file name",
        value=Path(uploaded_table.name).stem if uploaded_table else "table_output",
        key="table_filename",
    )

    if st.button("Generate MP3", key="table_generate"):
        if uploaded_table is None:
            st.warning("Please choose a table file first.")
        else:
            with st.spinner("Reading table and generating audio + chart"):
                try:
                    table_path = _save_uploaded_file(uploaded_table)
                    with tempfile.TemporaryDirectory() as tmp_dir:
                        mp3_path, png_path = process_table(
                            table_path, tmp_dir, table_filename
                        )
                        _offer_audio(mp3_path, f"{table_filename}.mp3")
                        _offer_chart(png_path, f"{table_filename}.png")
                except NoTableFoundError:
                    st.error(
                        "No table could be found in that file "
                        "(it may be and image_based table, use SMART in that case)."
                    )
                except Exception as e:
                    st.error(f"Error: {e}")


with tab_smart:
    st.subheader("Smart PDF")
    st.caption(
        "Detects text, tables, and image-based tables automatically."
        "Image tables are read using GEMINI"
    )

    uploaded_smart_pdf = st.file_uploader(
        "Choose a PDF file", type=["pdf"], key="smart_pdf_uploader"
    )
    smart_filename = st.text_input(
        "Output file name",
        value=Path(uploaded_smart_pdf.name).stem if uploaded_smart_pdf else "smart_output",
        key="smart_filename",
    )

    if st.button("Generate MP3", key="smart_generate"):
        if uploaded_smart_pdf is None:
            st.warning("Please choose a PDF file first.")
        else:
            with st.spinner("Processing PDF (text, tables, and images)..."):
                try:
                    pdf_path = _save_uploaded_file(uploaded_smart_pdf)
                    with tempfile.TemporaryDirectory() as tmp_dir:
                        result = process_smart_pdf(pdf_path, tmp_dir, smart_filename)
                        _offer_audio(result["mp3_path"], f"{smart_filename}.mp3")

                        for i, chart_path in enumerate(result["chart_paths"], start=1):
                            _offer_chart(
                                chart_path,
                                f"{smart_filename}_table{i}.png",
                                caption=f"Table {i}",
                            )
                except Exception as e:
                    st.error(f"Error: {e}")