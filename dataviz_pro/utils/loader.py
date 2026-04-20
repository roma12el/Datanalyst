import pandas as pd
import numpy as np


def load_data(uploaded_file):
    name = uploaded_file.name.lower()
    sheet_info = {}
    try:
        if name.endswith((".xlsx", ".xls")):
            xls = pd.ExcelFile(uploaded_file)
            sheet_info["sheets"] = xls.sheet_names
            import streamlit as st
            chosen = xls.sheet_names[0]
            if len(xls.sheet_names) > 1:
                chosen = st.sidebar.selectbox("Feuille Excel", xls.sheet_names)
            sheet_info["active"] = chosen
            df = pd.read_excel(uploaded_file, sheet_name=chosen)
        elif name.endswith(".csv"):
            raw = uploaded_file.read(); uploaded_file.seek(0)
            sample = raw[:2048].decode("utf-8", errors="replace")
            sep = ";" if sample.count(";") > sample.count(",") else ","
            df = pd.read_csv(uploaded_file, sep=sep, encoding="utf-8", on_bad_lines="skip")
        elif name.endswith(".tsv"):
            df = pd.read_csv(uploaded_file, sep="\t", encoding="utf-8", on_bad_lines="skip")
        else:
            return None, {}
        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(how="all").reset_index(drop=True)
        return df, sheet_info
    except Exception as e:
        import streamlit as st
        st.error(f"Erreur : {e}")
        return None, {}
