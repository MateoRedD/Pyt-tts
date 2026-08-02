import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

def generate_chart(df: pd.DataFrame, output_path: str) -> None:
    categorical_cols = df.select_dtypes(exclude="number").columns.tolist()
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    if not numeric_cols:
        raise ValueError("No numeric columns available to chart.")

    value_col = numeric_cols[0]
    label_col  = categorical_cols[0] if categorical_cols else df.index.astype(str)

    labels = df[label_col] if categorical_cols else label_col
    values = df[value_col]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(labels, values, color="#3c9eff")
    ax.set_xlabel(label_col if categorical_cols else "Row")
    ax.set_ylabel(value_col)
    ax.set_title(f"{value_col} by {label_col if categorical_cols else "Row"}")
    plt.xticks(rotation=30, ha="right")
    fig.tight_layout()

    fig.savefig(output_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    from table_reader import extract_table

    df = extract_table("sample_sales.csv")
    generate_chart(df, "test_chart.png")
    print("chart saved to test_chart.png")

    