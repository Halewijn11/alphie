import pandas as pd
import os, json
import zipfile
import io
from Bio import SeqIO


def create_alphafold_json_files(
    df,
    output_repository_path="./",
    batch_size=30,
    output_prefix="alphafold_batch",
    prediction_id_col_name="prediction_id",
    sequence_col_name="sequence",
    count_col_name='copies',
    type_col_name='entity_type',
):
    # df = df.copy()
    # if count_col is None:
    #     df['count'] = 1
    #     count_col = 'count'
    # if type_col is None:
    #     df['type'] = 'proteinChain'
    #     type_col = 'type'

    """
    Converts a flexible DataFrame into AlphaFold-style JSON job files.

    Args:
        df (pd.DataFrame): DataFrame with columns ['jobid', 'sequence', 'count', 'type'].
        batch_size (int): Number of jobs per JSON file.
        output_prefix (str): Prefix for output file names.
    """
    df = df.copy()

    type_mapping = {
        'protein': 'proteinChain',
        'dna': 'dnaChain',      # You can add others here too!
        'rna': 'rnaChain'
    }

    # Apply mapping. .get(x, x) ensures if it's not in the dict, it stays original
    df[type_col_name] = df[type_col_name].apply(lambda x: type_mapping.get(x, x))

    # Group by jobid
    grouped = df.groupby(prediction_id_col_name)


    jobs = []
    for jobid, group in grouped:
        job = {
            "name": str(jobid),
            "modelSeeds": [],
            "sequences": [
                {
                    row[type_col_name]: {
                        "sequence": row[sequence_col_name],
                        "count": int(row[count_col_name])
                    }
                }
                for _, row in group.iterrows()
            ]
        }
        jobs.append(job)

    # Ensure output path exists
    os.makedirs(output_repository_path, exist_ok=True)

    # Write to JSON in batches
    for i in range(0, len(jobs), batch_size):
        batch = jobs[i:i + batch_size]
        output_file = os.path.join(output_repository_path, f"{output_prefix}_{i // batch_size + 1}.json")
        with open(output_file, "w") as f:
            json.dump(batch, f, indent=2)



def create_alphafold_json_files_streamlit(
    df,
    output_repository_path="./",
    batch_size=30,
    output_prefix="alphafold_batch",
    prediction_id_col_name="prediction_id",
    sequence_col_name="sequence",
    count_col_name='copies',
    type_col_name='entity_type',
):
    # df = df.copy()
    # if count_col is None:
    #     df['count'] = 1
    #     count_col = 'count'
    # if type_col is None:
    #     df['type'] = 'proteinChain'
    #     type_col = 'type'

    """
    Converts a flexible DataFrame into AlphaFold-style JSON job files.

    Args:
        df (pd.DataFrame): DataFrame with columns ['jobid', 'sequence', 'count', 'type'].
        batch_size (int): Number of jobs per JSON file.
        output_prefix (str): Prefix for output file names.
    """
    df = df.copy()

    type_mapping = {
        'protein': 'proteinChain',
        'dna': 'dnaChain',      # You can add others here too!
        'rna': 'rnaChain'
    }

    # Apply mapping. .get(x, x) ensures if it's not in the dict, it stays original
    df[type_col_name] = df[type_col_name].apply(lambda x: type_mapping.get(x, x))

    # Group by jobid
    grouped = df.groupby(prediction_id_col_name)


    jobs = []
    for jobid, group in grouped:
        job = {
            "name": str(jobid),
            "modelSeeds": [],
            "sequences": [
                {
                    row[type_col_name]: {
                        "sequence": row[sequence_col_name],
                        "count": int(row[count_col_name])
                    }
                }
                for _, row in group.iterrows()
            ]
        }
        jobs.append(job)

    # Ensure output path exists
    os.makedirs(output_repository_path, exist_ok=True)

    # Instead of writing to disk, store in a dictionary
    output_files = {}
    for i in range(0, len(jobs), batch_size):
        batch = jobs[i:i + batch_size]
        filename = f"{output_prefix}_{i // batch_size + 1}.json"
        output_files[filename] = json.dumps(batch, indent=2)
    
    return output_files


def create_zip(files_dict):
    """Bundles the JSON strings into a single ZIP file in memory."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for filename, content in files_dict.items():
            zip_file.writestr(filename, content)
    return zip_buffer.getvalue()




def fasta_to_dataframe_streamlit(fasta_input, genome_name=None):
    records = []
    for record in SeqIO.parse(fasta_input, "fasta"):
        records.append({"id": record.id, "sequence": str(record.seq)})
    df = pd.DataFrame(records)
    df= df.rename({'id': 'prediction_id'}, axis = 1)

    return df


def gbk_to_dataframe_streamlit(gbk_input, genome_filename, suffix = '.gbk'):
    """
    Parse a GenBank file and convert features (with qualifiers) to a pandas DataFrame.

    Parameters:
        gbk_path (str): Path to the GenBank (.gbk) file.
        genome_name (str): Name of the genome.

    Returns:
        pd.DataFrame: DataFrame containing feature metadata and qualifiers.
    """
    records = list(SeqIO.parse(gbk_input, "genbank"))
    data = []

    for record in records:
        for feature in record.features:
            feature_data = {
                "genome": genome_filename,
                "id": record.id,
                "record_description": record.description,
                "feature_type": feature.type,
                "start": int(feature.location.start),
                "end": int(feature.location.end),
                "strand": feature.location.strand,
            }

            # Explicitly extract common qualifiers
            common_keys = [
                "gene", "locus_tag", "product", "note", "db_xref",
                "translation", "protein_id", "codon_start"
            ]

            for key in common_keys:
                feature_data[key] = "; ".join(feature.qualifiers.get(key, []))

            # Optional: capture all other qualifiers too
            for key, value in feature.qualifiers.items():
                if key not in common_keys:
                    feature_data[f"qual_{key}"] = "; ".join(value)

            data.append(feature_data)

    df = pd.DataFrame(data)
    df = df[df['feature_type'] == 'CDS']
    df = df[['locus_tag', 'translation']]
    df = df.rename({"locus_tag": "prediction_id", 'translation': 'sequence'}, axis = 1)
    return df


def convert_sequence_to_csv(uploaded_file):
    # 1. Convert bytes to a text stream
    # .getvalue() gets the raw bytes, .decode("utf-8") makes it text
    string_data = uploaded_file.getvalue().decode("utf-8")
    file_buffer = io.StringIO(string_data)
    
    filename = uploaded_file.name
    ext = filename.split('.')[-1].lower()

    # 2. Route to your adapted functions
    if ext in ['fasta', 'fa', 'faa']:
        df = fasta_to_dataframe_streamlit(file_buffer, genome_name=filename)
        print(df.columns)
    elif ext in ['gbk', 'gb']:
        df = gbk_to_dataframe_streamlit(file_buffer, genome_filename=filename)
    else:
        return None

    # 3. Return the final CSV bytes
    return df.to_csv(index=False).encode('utf-8')








# def convert_sequence_to_csv(uploaded_file):
#     """
#     Adapts fasta_to_dataframe and gbk_to_dataframe logic for Streamlit.
#     Returns: bytes (CSV format)
#     """
#     # 1. Setup
#     filename = uploaded_file.name
#     file_ext = os.path.splitext(filename)[1].lower()
    
#     # Biopython needs a text stream for parsing
#     # We decode the uploaded bytes to string
#     stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
    
#     data = []

#     # 2. Handle FASTA
#     if file_ext in ['.fasta', '.fa']:
#         for record in SeqIO.parse(stringio, "fasta"):
#             data.append({
#                 "prediction_id": record.id,
#                 "sequence": str(record.seq),
#                 "entity_type": "protein",
#                 "copies": 1
#             })

#     # 3. Handle GenBank (Flattening Features)
#     elif file_ext in ['.gbk', '.gb']:
#         for record in SeqIO.parse(stringio, "genbank"):
#             for feature in record.features:
#                 # We usually only want 'CDS' or 'protein' features for AlphaFold
#                 # But here we keep it flexible like your gbk_to_dataframe logic
#                 if feature.type == "CDS" or "translation" in feature.qualifiers:
#                     translation = "; ".join(feature.qualifiers.get("translation", []))
#                     locus_tag = "; ".join(feature.qualifiers.get("locus_tag", [record.id]))
                    
#                     if translation: # Only add if there is a sequence
#                         data.append({
#                             "prediction_id": locus_tag,
#                             "sequence": translation,
#                             "entity_type": "protein",
#                             "copies": 1,
#                             "gene_name": "; ".join(feature.qualifiers.get("gene", []))
#                         })

#     if not data:
#         return None

#     # 4. Convert to DataFrame and then to CSV Bytes
#     df = pd.DataFrame(data)
#     return df.to_csv(index=False).encode('utf-8')