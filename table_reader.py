from pathlib import Path

import pandas as pd
import pdfplumber

class NoTableFoundError(Exception):
    pass

def extract_table(file_path: str) -> pd.DataFrame:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        return _extract_from_csv(path)
    elif suffix == ".xlsx":
        return _extract_from_excel(path)
    elif suffix == ".pdf":
        return _extract_from_pdf(path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

def _extract_from_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    return _clean_dataframe(df)

def _extract_from_excel(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path)
    return _clean_dataframe(df)

def _extract_from_pdf(path: Path) -> pd.DataFrame:
    with pdfplumber.open(path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            for table in tables:
                if table and len(table) > 1:
                    header, *rows = table
                    df = pd.DataFrame(rows, columns=header)
                    return _clean_dataframe(df)

    raise NoTableFoundError(
        f"No extractable table found in {path.name}."
        "This may be a scanned/image-based table"
    )

def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip() for c in df.columns]

    for col in df.columns:
        converted = pd.to_numeric(
            df[col].astype(str).str.replace(",", "").str.strip(), errors="coerce"
        )
        if converted.notna().sum() >= len(df) * 0.8:
            df[col] = converted

    return df

if __name__ == "__main__":
    for test_file in ["sample_sales.csv", "sample_sales.xlsx", "sample_sales.pdf"]:
        print(f"\n--- {test_file} ---")
        df = extract_table(test_file)
        print(df)
        print(df.dtypes)