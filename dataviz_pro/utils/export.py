import pandas as pd
import io


def df_to_excel_bytes(df):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return buf.getvalue()


def df_to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")


def export_report():
    pass
