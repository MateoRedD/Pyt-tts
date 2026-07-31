import pdfplumber

SAME_LINE_TOLERANCE = 3

def extract_text(pdf_path: str) -> str:
    pages_text = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            words = page.extract_words()

            if not words:
                print(f"[warning] Page {page_num}: no extractable text (image-based page?)")
                continue
            pages_text.append(_reconstruct_page(words))

        return "\n\n".join(pages_text)

def _reconstruct_page(words: list) -> str:
    lines = []
    current_line = [words[0]]

    for word in words[1:]:
        same_line = abs(word["top"] - current_line[-1]["top"]) < SAME_LINE_TOLERANCE
        if same_line:
            current_line.append(word)
        else:
            lines.append(current_line)
            current_line = [word]
    lines.append(current_line)

    line_texts = [" ".join(w["text"] for w in line) for line in lines]
    return " ".join(line_texts)

if __name__ == "__main__":
    text = extract_text("english_text_two_pages.pdf")
    print(text[:500])
    print(f"\n\nTotal characters extracted: {len(text)}")