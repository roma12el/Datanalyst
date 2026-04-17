import pandas as pd
import numpy as np
import io


def load_data(uploaded_file):
    """Load Excel or CSV file, return (DataFrame, sheet_info_dict)."""
    name = uploaded_file.name.lower()
    sheet_info = {}

    try:
        if name.endswith((".xlsx", ".xls")):
            xls = pd.ExcelFile(uploaded_file)
            sheet_info["sheets"] = xls.sheet_names
            sheet_info["active"] = xls.sheet_names[0]
            # Let user pick sheet if multiple
            import streamlit as st
            if len(xls.sheet_names) > 1:
                chosen = st.sidebar.selectbox(
                    "📋 Feuille Excel",
                    xls.sheet_names,
                    help="Sélectionnez l'onglet à analyser"
                )
                sheet_info["active"] = chosen
            df = pd.read_excel(uploaded_file, sheet_name=sheet_info["active"])

        elif name.endswith(".csv"):
            # Auto-detect separator
            raw = uploaded_file.read()
            uploaded_file.seek(0)
            sample = raw[:2048].decode("utf-8", errors="replace")
            sep = ";" if sample.count(";") > sample.count(",") else ","
            df = pd.read_csv(uploaded_file, sep=sep, encoding="utf-8", on_bad_lines="skip")
            sheet_info["sheets"] = ["CSV"]
            sheet_info["active"] = "CSV"

        elif name.endswith(".tsv"):
            df = pd.read_csv(uploaded_file, sep="\t", encoding="utf-8", on_bad_lines="skip")
            sheet_info["sheets"] = ["TSV"]
            sheet_info["active"] = "TSV"

        else:
            return None, {}

        # Basic cleanup
        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(how="all").reset_index(drop=True)
        return df, sheet_info

    except Exception as e:
        import streamlit as st
        st.error(f"Erreur de lecture : {e}")
        return None, {}


def get_file_info(df):
    """Return dict with basic file statistics."""
    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    date_cols = df.select_dtypes(include=["datetime"]).columns.tolist()

    # Try to detect date columns in object dtype
    for c in cat_cols:
        try:
            pd.to_datetime(df[c], infer_datetime_format=True)
            date_cols.append(c)
        except Exception:
            pass

    return {
        "rows": len(df),
        "cols": len(df.columns),
        "num_cols": num_cols,
        "cat_cols": cat_cols,
        "date_cols": date_cols,
        "missing": int(df.isnull().sum().sum()),
        "missing_pct": round(100 * df.isnull().sum().sum() / (df.shape[0] * df.shape[1]), 2),
        "duplicates": int(df.duplicated().sum()),
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1e6, 3),
    }
