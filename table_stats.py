import statistics

import pandas as pd

FULL_DETAIL_THRESHOLD = 3

def describe_table(df: pd.DataFrame) -> str:
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(exclude="number").columns.tolist()

    parts = [_describe_structure(df)]

    if not numeric_cols:
        parts.append("No numeric columns were found to analyze.")
        return " ".join(parts)

    if len(numeric_cols) <= FULL_DETAIL_THRESHOLD:
        for col in numeric_cols:
            parts.append(_describe_column_full(df, col, categorical_cols))

    else:
        parts.append(_describe_columns_compact(df, numeric_cols))

    return " ".join(parts)

def _describe_structure(df: pd.DataFrame) -> str:
    row_count = len(df)
    col_names = ", ".join(df.columns)
    return f"this table has {row_count} rows and {len(df.columns)} columns: {col_names}"

def _describe_column_full(df: pd.DataFrame, col: str, categorical_cols: list) -> str:
    series = df[col].dropna()
    mean = series.mean()
    median = series.median()
    std_dev = series.std()
    minimun = series.min()
    maximun = series.max()

    value_counts = series.value_counts()
    mode = None
    if not value_counts.empty and value_counts.iloc[0] > 1:
        mode = value_counts.index[0]

    text = (
        f"For {col}, the average was {mean:,.2f}, the median was {median:,.2f}, "
        f"and values ranged from {minimun:,.2f} to {maximun:,.2f}, "
        f"with a standard desviation of {std_dev:,.2f}."
    )

    if mode is not None:
        text += f" The most common value was {mode:,.2f}."

    if categorical_cols:
        label_col = categorical_cols[0]
        total = series.sum()
        top_idx = series.idxmax()
        top_label = df.loc[top_idx, label_col]
        top_value = series.loc[top_idx]
        pct = (top_value / total) * 100 if total else 0
        text += f" {top_label} had the highest {col} at {pct:.1f} percent of the total"

    return text

def _describe_columns_compact(df: pd.DataFrame, numeric_cols: list) -> str:
    sentences = []
    for col in numeric_cols:
        series = df[col].dropna()
        mean = series.mean()
        minimun = series.min()
        maximum = series.max()
        sentences.append(
            f"{col} averaged {mean:,.2f}, ranging from {minimun:,.2f} to {maximum:,.2f}."
        )
    return " ".join(sentences)


if __name__ == "__main__":
    from table_reader import extract_table

    df = extract_table("sample_sales.csv")
    print(describe_table(df))

