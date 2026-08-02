from pathlib import Path

from chart_generator import generate_chart
from table_reader import extract_table
from table_stats import describe_table
from tts_engine import text_to_mp3

def process_table(file_path: str, output_folder: str, filename: str) -> tuple[str, str]:
    df = extract_table(file_path)

    if df.empty:
        raise ValueError("The table is empty, nothin to describe.")

    description = describe_table(df)

    mp3_path = str(Path(output_folder) / f"{filename}.mp3")
    png_path = str(Path(output_folder) / f"{filename}.png")

    text_to_mp3(description, mp3_path)
    generate_chart(df, png_path)

    return mp3_path, png_path

if __name__ == "__main__":
    for test_file in ["sample_sales.csv", "sample_sales.xlsx", "sample_sales.pdf"]:
        print(f"\nProcessing {test_file}...")
        mp3_path, png_path = process_table(test_file, ".", Path(test_file).stem)
        print(f" MP3: {mp3_path}")
        print(f" PNG: {png_path}")

    