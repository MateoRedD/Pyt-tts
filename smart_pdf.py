import io
import pandas as pd
import pdfplumber

from pathlib import Path
from chart_generator import generate_chart
from gemini_table_reader import extract_table_from_image, is_table_image
from pdf_reader import _reconstruct_page
from table_reader import _clean_dataframe
from table_stats import describe_table
from tts_engine import text_to_mp3

def process_smart_pdf(pdf_path: str, output_folder: str, filename: str) -> dict:
    text_parts = []
    chart_paths = []
    table_count = 0

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            words = page.extract_words()
            combined_table = _combine_tables(tables)

            if combined_table and len(combined_table) > 1:
                df = _table_to_dataframe(combined_table)
                table_count += 1
                text_parts.append(f"The following tabke appears on page {page_num}. " + describe_table(df))
                chart_paths.append(
                    _save_chart(df, output_folder, filename, table_count)
                )

            elif words:
                text_parts.append(_reconstruct_page(words))

            else:
                image_bytes = _render_page_as_png(page)

                if is_table_image(image_bytes):
                    df = extract_table_from_image(image_bytes)
                    table_count += 1
                    text_parts.append(f"The following table appears on page {page_num}. " + describe_table(df))
                    chart_paths.append(
                        _save_chart(df, output_folder, filename, table_count)
                    )

    full_text = " ".join(text_parts)

    if not full_text.strip():
        raise ValueError("No text or tables could be extracted from this PDF.")

    mp3_path = str(Path(output_folder) / f"{filename}.mp3")
    text_to_mp3(full_text, mp3_path)

    return {"mp3_path": mp3_path, "chart_paths": chart_paths}

def _table_to_dataframe(raw_table: list) -> pd.DataFrame:
    header, *rows = raw_table
    df = pd.DataFrame(rows, columns=header)
    return _clean_dataframe(df)

def _combine_tables(tables: list) -> list:
    if not tables:
        return []

    if all(isinstance(t, list) and t and not isinstance(t[0], list) for t in tables):
        return tables

    return max(tables, key=len)

def _save_chart(df: pd.DataFrame, output_folder: str, filename: str, table_count: int) -> str:
    chart_path = str(Path(output_folder) / f"{filename}_table{table_count}.png")
    generate_chart(df, chart_path)
    return chart_path

def _render_page_as_png(page) -> bytes:
    image = page.to_image(resolution=150)
    buffer = io.BytesIO()
    image.original.save(buffer, format="PNG")
    return buffer.getvalue()

if __name__ == "__main__":
    result = process_smart_pdf("weather_report.pdf", ".", "smart_test")
    print(result)
