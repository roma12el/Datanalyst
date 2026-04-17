import pandas as pd
import numpy as np


def compute_profile(df):
    rows = []
    for col in df.columns:
        s = df[col]
        dtype = str(s.dtype)
        n_missing = int(s.isnull().sum())
        missing_pct = round(100 * n_missing / len(s), 2)
        n_unique = s.nunique()
        row = {
            "column": col,
            "dtype": dtype,
            "count": int(s.count()),
            "missing": n_missing,
            "missing_pct": missing_pct,
            "unique": n_unique,
        }
        if pd.api.types.is_numeric_dtype(s):
            row.update({
                "mean": round(s.mean(), 4),
                "std": round(s.std(), 4),
                "min": round(s.min(), 4),
                "25%": round(s.quantile(0.25), 4),
                "50%": round(s.median(), 4),
                "75%": round(s.quantile(0.75), 4),
                "max": round(s.max(), 4),
                "skew": round(s.skew(), 4),
                "kurt": round(s.kurtosis(), 4),
            })
        else:
            top = s.value_counts()
            row.update({
                "top_value": str(top.index[0]) if len(top) > 0 else "",
                "top_freq": int(top.iloc[0]) if len(top) > 0 else 0,
            })
        rows.append(row)
    return pd.DataFrame(rows)


def compute_missing_heatmap_data(df, max_rows=200, max_cols=50):
    sample = df.sample(min(max_rows, len(df)), random_state=42)
    return sample.isnull().astype(int)
