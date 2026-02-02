import streamlit as st
import importlib
import pandas as pd
import utils
importlib.reload(utils)
# from streamlit_extras.metric_cards import style_metric_cards
import altair as alt
import numpy as np
import io
import os
# from streamlit_gsheets import GSheetsConnection
from datetime import datetime

debug = 0
cached_time = 0
time_window_hours = 1
time_window_filtering_mode = 'last_session'
current_dir = os.path.dirname(__file__)
asset_path = os.path.join(current_dir, "..", "assets")

st.title("Alphafold server tools")



# 1. File Uploader
seq_file = st.file_uploader("Upload your gene annotation file ", type=["fasta", "faa", "gbk", "gb"])
if seq_file:
    # 2. Run the conversion from your utils
    # This returns raw bytes (utf-8 encoded CSV)
    csv_bytes = utils.convert_sequence_to_csv(seq_file)
        
    if csv_bytes:
        df = pd.read_csv(io.BytesIO(csv_bytes))
        df['entity_type'] = 'protein'
        df['copies'] = 1

        st.dataframe(df)
        
        # # 3. Create a clean filename using the original file's name
        base_name = os.path.splitext(seq_file.name)[0]
        new_filename = f"{base_name}_converted.csv"

# --- DOWNLOAD SECTION ---
        st.write("### Export Options")
        col1, col2 = st.columns(2)

        # 1. CSV Download Button
        csv_data = df.to_csv(index=False).encode('utf-8')
        col1.download_button(
            label="Download as CSV",
            data=csv_data,
            file_name=f"{base_name}_converted.csv",
            mime="text/csv"
        )

        # 2. XLSX Download Button
        # Create an in-memory buffer for the Excel file
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='AlphaFold_Input')
        
        col2.download_button(
            label="Download as Excel (XLSX)",
            data=excel_buffer.getvalue(),
            file_name=f"{base_name}_converted.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("No valid sequences or translations found in file.")
