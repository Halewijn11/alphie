import streamlit as st
import importlib
import pandas as pd
import utils
importlib.reload(utils)
# from streamlit_extras.metric_cards import style_metric_cards
import altair as alt
import numpy as np
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

documentation_text ="""
This tool converts your sequence data into the specific JSON format required for AlphaFold 3 server submissions. To use it, upload a CSV file containing prediction_id and sequence columns; any rows sharing the same ID will be grouped into a single multimer or protein-ligand prediction. The tool automatically divides your data into batches of 30 jobs per JSON file to stay within the server's daily upload limit. Once generated, you can download these batches individually or as a ZIP file and upload them directly to the [AlphaFold 3 Server](https://alphafoldserver.com/) to begin your predictions.

Happy Folding!
"""
st.write(documentation_text)
df_example = pd.read_csv(asset_path + '/test.csv', sep=None, engine='python', encoding='utf-8-sig')
# 2. Convert the DataFrame to a CSV string (as bytes)
csv_bytes = df_example.to_csv(index=False).encode('utf-8')

st.download_button(
    label="Download Example CSV Template",
    data=csv_bytes,
    file_name="example_alphafold_input.csv",
    mime="text/csv"
)




# Create the file uploader widget
uploaded_file = st.file_uploader("Upload your data (CSV or Excel)", type=["csv", "xlsx"])

# if uploaded_file is not None:
#     # Check the file extension to determine the correct pandas reader
#     if uploaded_file.name.endswith('.csv'):
#         df = pd.read_csv(uploaded_file)
#     else:
#         df = pd.read_excel(uploaded_file)

#     # Display a success message and a preview of the data
#     st.success("File uploaded successfully!")
#     st.write("### Data Preview")
#     st.dataframe(df.head())
    
#     # Now you can use 'df' for your Alphafold tools logic
# else:
#     st.info("Please upload a CSV or Excel file to get started.")


# if uploaded_file:
#     # Handle the BOM/separator issues we discussed
#     df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8-sig')
#     st.write("Preview:", df)

#     if st.button("Generate JSON Batches"):
#         results = utils.create_alphafold_json_files_streamlit(df)
        
#         st.success(f"Generated {len(results)} file(s)!")
#         # --- Option 2: Individual Download Buttons ---
#         for filename, json_str in results.items():
#             st.download_button(
#                 label=f"Download {filename}",
#                 data=json_str,
#                 file_name=filename,
#                 mime="application/json"
#             )


# 1. Initialize session state for results if it doesn't exist
if 'json_results' not in st.session_state:
    st.session_state.json_results = None

if uploaded_file:
    try:
        # Check the file extension
        if uploaded_file.name.endswith('.csv'):
            # Try UTF-8 first, then Latin-1 for CSVs
            try:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8-sig')
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin1')
        
        elif uploaded_file.name.endswith(('.xlsx', '.xls')):
            # Excel files don't need 'encoding' or 'sep'
            df = pd.read_excel(uploaded_file)

        st.success("File loaded successfully!")

        # --- NEW SELECTION FEATURE START ---
        st.subheader("Select Rows for JSON Generation")
        
        # Add a selection column at the beginning
        if "select" not in df.columns:
            df.insert(0, "select", True) # Defaulting to True (all selected)

        # Display the interactive editor
        # 'column_config' makes the Select column a checkbox
        edited_df = st.data_editor(
            df,
            column_config={
                "select": st.column_config.CheckboxColumn(
                    "select",
                    help="Select rows to include in the JSON batch",
                    default=True,
                )
            },
            disabled=[col for col in df.columns if col != "select"], # Only allow editing the Checkbox
            hide_index=True,
        )

        # Filter the dataframe based on selection
        selected_df = edited_df[edited_df["select"] == True].drop(columns=["select"])
        
        st.write(f"Total rows selected: {len(selected_df)}")
        # --- NEW SELECTION FEATURE END ---


        # st.write("Preview:", df)
        
        # Save to session state for your JSON logic
        st.session_state.df = selected_df

    except Exception as e:
        st.error(f"Error loading file: {e}")

    # 2. When the button is clicked, save the output to session_state
    if st.button("Generate JSON Batches"):
        st.session_state.json_results = utils.create_alphafold_json_files_streamlit(selected_df)
        st.success(f"Generated {len(st.session_state.json_results)} file(s)!")

    # 3. Always check if we have results in state. If yes, show the buttons.
    if st.session_state.json_results:
        st.divider()
        st.subheader("Download Results")
        
        # Zip option
        if len(st.session_state.json_results) > 1:
            zip_data = utils.create_zip(st.session_state.json_results)
            st.download_button(
                label="Download All as ZIP",
                data=zip_data,
                file_name="alphafold_all_batches.zip",
                mime="application/zip"
            )

        # Individual files
        for filename, json_str in st.session_state.json_results.items():
            st.download_button(
                label=f"Download {filename}",
                data=json_str,
                file_name=filename,
                mime="application/json",
                key=filename # Adding a unique key is good practice in loops
            )