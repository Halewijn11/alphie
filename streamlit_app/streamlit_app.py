import streamlit as st
import importlib
import utils
import pandas as pd
importlib.reload(utils)

# --- PAGE SETUP ---
genome_file_conversion = st.Page(
    "pages/genome_file_to_dataframe.py",
    title="Genome file to dataframe",
    icon=":material/table:",
    # default=True,
)

alphafold_server_tools = st.Page(
    "pages/alphafold_server_tools.py",
    title="Alphafold server tools",
    icon=":material/bar_chart:",
)
# status_page = st.Page(
#     "pages/status.py",
#     title="Status",
#     icon=":material/memory:",
# )

retrieve_scoring_metrics = st.Page(
    "pages/retrieve_scoring_metrics.py",
    title="Retrieve scoring metrics",
    icon=":material/analytics:",
)


info_page = st.Page(
    "pages/info.py",
    title="info",
    icon=":material/info:",
    default=True,
)


# project_2_page = st.Page(
#     "views/chatbot.py",
#     title="Chat Bot",
#     # icon=":material/smart_toy:",
# )

# --- NAVIGATION SETUP [WITHOUT SECTIONS] ---
pg = st.navigation(pages=[info_page, genome_file_conversion, alphafold_server_tools, retrieve_scoring_metrics])

# --- RUN NAVIGATION ---
pg.run()