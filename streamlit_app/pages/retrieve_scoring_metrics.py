import streamlit as st
import pandas as pd
import importlib
import zipfile
import tempfile
import os
import shutil
import io
import utils # Assuming your extraction logic is in here
importlib.reload(utils)

st.title("AlphaFold Metrics Extractor")

# 1. File Uploader for ZIP
zip_file = st.file_uploader("Upload AlphaFold Predictions (ZIP)", type=["zip"])

if zip_file:
    # Use a temporary directory so we don't leave a mess
    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = os.path.join(tmp_dir, "upload.zip")
        extract_path = os.path.join(tmp_dir, "extracted")
        
        # Save the uploaded bytes to the temp zip file
        with open(zip_path, "wb") as f:
            f.write(zip_file.getbuffer())
        
        # Unzip the contents
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        # 2. Run your existing function
        # Replace 'utils.extract_metrics' with your actual function name
        try:
            with st.spinner("Extracting metrics..."):
                df_metrics = utils.get_structome_best_model_metadata(extract_path)
                print(df_metrics)
            
            if not df_metrics.empty:
                st.subheader("Extracted Metrics")
                st.dataframe(df_metrics)

                # Create two columns for side-by-side buttons
                col1, col2 = st.columns(2)

                # 1. CSV Download
                csv_data = df_metrics.to_csv(index=False).encode('utf-8')
                col1.download_button(
                    label="Download as CSV",
                    data=csv_data,
                    file_name=f"{zip_file.name}_metrics.csv",
                    mime="text/csv",
                )

                # 2. Excel Download
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_metrics.to_excel(writer, index=False, sheet_name='AlphaFold_Metrics')
                
                col2.download_button(
                    label="Download as Excel",
                    data=buffer.getvalue(),
                    file_name=f"{os.path.splitext(zip_file.name)[0]}_metrics.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
        except Exception as e:
            st.error(f"An error occurred during processing: {e}")