import streamlit as st
description = """
This platform provides a suite of utilities designed to streamline your structural biology workflow, from initial sequence preparation to post-prediction analysis. While each tab is built to function as a standalone tool, they are designed to work together in a seamless three-step pipeline:

1. Sequence Preparation Start by converting your raw genomic data (GenBank or FASTA) into a structured format. This stage extracts protein translations and locus tags, preparing a clean table that serves as the foundation for your experiment.

2. Batch Job Generation Take your structured sequence table and group entries into specific predictions (such as multimers or protein-ligand complexes). This tool automatically generates JSON batch files—limited to 30 jobs each to respect daily server constraints—which can be uploaded directly to the AlphaFold 3 web server.

3. Metrics Extraction & Analysis Once your folding is complete, upload the resulting ZIP file (single or bulk) to extract and compare results. This stage calculates advanced metrics like ipSAE scores alongside standard pTM and ipTM values, allowing you to sort your models and download a consolidated package of only the best-ranked CIF files.

Whether you are here just to convert a file or to perform a deep-dive analysis on a bulk run, these tools are here to simplify the "heavy lifting" so you can focus on the science.

Happy Folding!
"""

st.write(description)