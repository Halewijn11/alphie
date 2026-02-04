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
import af_analysis
from af_analysis import analysis

st.title("AlphaFold Metrics Extractor")

documentation_test = """
Upload your AlphaFold results as a ZIP file only. If you have already unzipped your data, please re-zip the folder before uploading, as the tool cannot process raw folders. You can upload either a single prediction ZIP or a bulk download containing multiple jobs.

Once processed, your ipSAE, pTM, and ipTM scores will appear in the table below. You can download these results as a CSV or Excel file for your records. Additionally, you can download a consolidated ZIP containing only the CIF files for all your predictions, perfect for quick viewing in PyMOL or ChimeraX.

Happy Folding!
"""
st.write(documentation_test)

# 1. File Uploader
uploaded_file = st.file_uploader(
    "Upload AlphaFold ZIP", 
    type=["zip"],
    accept_multiple_files=False 
)

if uploaded_file:
    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = os.path.join(tmp_dir, "upload.zip")
        extract_path = os.path.join(tmp_dir, "extracted")
        
        with open(zip_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        try:
            with st.spinner("Extracting score metrics..."):
                # Identify prediction folders by looking for the 'msas' subfolder
                prediction_paths = []
                for root, dirs, files in os.walk(extract_path):
                    if "msas" in dirs:
                        # This 'root' is a valid prediction folder
                        prediction_paths.append(root)
                
                if not prediction_paths:
                    st.error("No valid AlphaFold 3 prediction folders (containing 'msas') found.")
                    st.stop()

                df_array = []
                for p_path in prediction_paths:
                    # Initialize your data object
                    # p_path will be the folder containing the .cif and .json files
                    my_data = af_analysis.Data(p_path, format='AF3_webserver')
                    analysis.ipSAE(my_data)
                    
                    if hasattr(my_data, 'df') and not my_data.df.empty:
                        df_array.append(my_data.df)

                if df_array:
                    df_metrics = pd.concat(df_array, ignore_index=True)
                    st.subheader(f"Extracted Metrics ({len(prediction_paths)} predictions found)")
                    st.dataframe(df_metrics)

                    # --- DOWNLOAD SECTION ---
                    col1, col2, col3 = st.columns(3)
                    base_name = os.path.splitext(uploaded_file.name)[0]

                    # CSV
                    csv_data = df_metrics.to_csv(index=False).encode('utf-8')
                    col1.download_button("Download CSV", csv_data, f"{base_name}_metrics.csv")

                    # Excel
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df_metrics.to_excel(writer, index=False, sheet_name='AF3_Metrics')
                    col2.download_button("Download Excel", buffer.getvalue(), f"{base_name}_metrics.xlsx")
                    
                    # CIF ZIP
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as new_zip:
                        for _, row in df_metrics.iterrows():
                            file_path = row['pdb']
                            if os.path.exists(file_path):
                                # Use the query name for the filename inside the zip
                                arc_name = f"{row['query']}.cif"
                                new_zip.write(file_path, arcname=arc_name)
                    
                    col3.download_button("Download Best CIFs", zip_buffer.getvalue(), f"best_models_{base_name}.zip")
                
        except Exception as e:
            st.error(f"Processing error: {e}")


# # 1. File Uploader for ZIP
# zip_file = st.file_uploader("Upload AlphaFold Predictions (ZIP)", type=["zip"])

# if zip_file:
#     # Use a temporary directory so we don't leave a mess
#     with tempfile.TemporaryDirectory() as tmp_dir:
#         zip_path = os.path.join(tmp_dir, "upload.zip")
#         extract_path = os.path.join(tmp_dir, "extracted")
        
#         # Save the uploaded bytes to the temp zip file
#         with open(zip_path, "wb") as f:
#             f.write(zip_file.getbuffer())
        
#         # Unzip the contents
#         with zipfile.ZipFile(zip_path, 'r') as zip_ref:
#             zip_ref.extractall(extract_path)
        
#         # 2. Run your existing function
#         # Replace 'utils.extract_metrics' with your actual function name
#         try:
#             with st.spinner("Extracting metrics..."):
#                 prediction_names_list = [
#                     d for d in os.listdir(extract_path) 
#                     if os.path.isdir(os.path.join(extract_path, d))
#                 ] 
#                 df_array = []
#                 for prediction_name in prediction_names_list: 
#                     prediction_path = os.path.join(extract_path, prediction_name)
#                     # st.write(f"Processing: {prediction_name} at {prediction_path}")
#                     my_data = af_analysis.Data(prediction_path, format = 'AF3_webserver')
#                     analysis.ipSAE(my_data)
#                     df = my_data.df
#                     # st.dataframe(df)
#                     df_array.append(df)
            
#             df_metrics = pd.concat(df_array, ignore_index=True)
#             if not df_metrics.empty:
#                 st.subheader("Extracted Metrics")
#                 st.dataframe(df_metrics)

#                 # Create two columns for side-by-side buttons
#                 col1, col2, col3 = st.columns(3)

#                 # 1. CSV Download
#                 csv_data = df_metrics.to_csv(index=False).encode('utf-8')
#                 col1.download_button(
#                     label="Download as CSV",
#                     data=csv_data,
#                     file_name=f"{zip_file.name}_metrics.csv",
#                     mime="text/csv",
#                 )

#                 # 2. Excel Download
#                 buffer = io.BytesIO()
#                 with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
#                     df_metrics.to_excel(writer, index=False, sheet_name='AlphaFold_Metrics')
                
#                 col2.download_button(
#                     label="Download as Excel",
#                     data=buffer.getvalue(),
#                     file_name=f"{os.path.splitext(zip_file.name)[0]}_metrics.xlsx",
#                     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#                 )
                
#                 # 3. ZIP Download (Best CIF files only)
#                 zip_buffer = io.BytesIO()
#                 with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as new_zip:
#                     for _, row in df_metrics.iterrows():
#                         file_path = row['pdb']
#                         file_name = row['query']
#                         if os.path.exists(file_path):
#                             # Add file to zip: (actual path on disk, name inside the zip)
#                             new_zip.write(file_path, arcname=file_name)
                
#                 col3.download_button(
#                     label="Download Best .cif Files",
#                     data=zip_buffer.getvalue(),
#                     file_name=f"best_models_{os.path.splitext(zip_file.name)[0]}.zip",
#                     mime="application/zip"
#                 )
    
#         except Exception as e:
#             st.error(f"An error occurred during processing: {e}")