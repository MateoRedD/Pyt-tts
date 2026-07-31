import sys
from pathlib import Path

from pdf_reader import extract_text
from tts_engine import text_to_mp3

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_pdf> [output_path.mp3]")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    output_path = sys.argv[2] if len(sys.argv) > 2 else "output.mp3"

    if not pdf_path.exists():
        print(f"[error] File not found: {pdf_path}")
        sys.exit(1)

    print(f"Extracting text from {pdf_path}...")
    try:
        text = extract_text(str(pdf_path))
    except Exception as e:
        print(f"[error] Failed to read PDF: {e}")
        sys.exit(1)

    if not text or not text.strip():
        print("[error] Could not extract text from PDF (scanned/image-based PDF?)")
        sys.exit(1)

    print(f"Text extraced: {len(text)} characters")
    print(f"Generating audio at {output_path}...")

    try:
        text_to_mp3(text, output_path)
    except Exception as e:
        print(f"[error] Failed to generate audio: {e}")
        sys.exit(1)

    print(f"Done. Audio saved to: {output_path}")

if __name__ == "__main__":
    main()