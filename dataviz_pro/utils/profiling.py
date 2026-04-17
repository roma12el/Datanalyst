import pandas as pd
import numpy as np
from scipy import stats


def compute_profile(df):
    """Compute full column-level profiling."""
    profile = []
    for col in df.columns:
        s = df[col]
        info = {
            "column": col,
            "dtype": str(s.dtype),
            "count": int(s.count()),
            "missing": int(s.isnull().sum()),
            "missing_pct": round(100 * s.isnull().sum() / len(s), 1),
            "unique": int(s.nunique()),
            "unique_pct": round(100 * s.nunique() / len(s), 1),
        }

        if pd.api.types.is_numeric_dtype(s):
            info["type"] = "Numérique"
            info["min"] = round(float(s.min()), 4) if not s.empty else None
            info["max"] = round(float(s.max()), 4) if not s.empty else None
            info["mean"] = round(float(s.mean()), 4) if not s.empty else None
            info["median"] = round(float(s.median()), 4) if not s.empty else None
            info["std"] = round(float(s.std()), 4) if not s.empty else None
            info["q25"] = round(float(s.quantile(0.25)), 4) if not s.empty else None
            info["q75"] = round(float(s.quantile(0.75)), 4) if not s.empty else None
            info["skewness"] = round(float(stats.skew(s.dropna())), 3) if len(s.dropna()) > 2 else None
            info["kurtosis"] = round(float(stats.kurtosis(s.dropna())), 3) if len(s.dropna()) > 2 else None
            # Outliers using IQR
            q1, q3 = s.quantile(0.25), s.quantile(0.75)
            iqr = q3 - q1
            outliers = ((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum()
            info["outliers"] = int(outliers)
            info["zeros"] = int((s == 0).sum())
        else:
            info["type"] = "Catégorielle"
            info["top_value"] = str(s.mode()[0]) if not s.empty else None
            info["top_freq"] = int(s.value_counts().iloc[0]) if not s.empty else None
            info["top_pct"] = round(100 * s.value_counts().iloc[0] / s.count(), 1) if not s.empty else None
            info["min"] = info["max"] = info["mean"] = info["median"] = None
            info["std"] = info["q25"] = info["q75"] = None
            info["skewness"] = info["kurtosis"] = info["outliers"] = info["zeros"] = None

        profile.append(info)

    return pd.DataFrame(profile)


def detect_date_columns(df):
    """Return list of column names that look like dates."""
    date_cols = list(df.select_dtypes(include=["datetime"]).columns)
    for col in df.select_dtypes(include=["object"]).columns:
        try:
            parsed = pd.to_datetime(df[col], infer_datetime_format=True, errors="coerce")
            if parsed.notna().sum() / len(df) > 0.6:
                date_cols.append(col)
        except Exception:
            pass
    return date_cols


def compute_missing_heatmap_data(df):
    """Return binary DataFrame (1=missing, 0=present) for heatmap."""
    return df.isnull().astype(int)
