import pandas as pd
import os, json
import zipfile
import io

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