from xml.parsers.expat import model
import pandas as pd
import os, json
import zipfile
import io
from Bio import SeqIO
import numpy as np
import re


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

def get_summary_confidence_informations(json_summary_confidences_filepath, model = 'AF3'): 
    with open(json_summary_confidences_filepath, 'r') as f:
        data = json.load(f)
        iptm = data['iptm']
        ptm = data['ptm']
        ranking_score = data['ranking_score']
        chain_ptm = data['chain_ptm']
        chain_iptm = data['chain_iptm']
        
    return iptm, ptm, ranking_score,chain_ptm, chain_iptm


def get_AF3_summary_confidence_files(AF_prediction_path, title):
    # Define the regex pattern to match summary confidence files
    pattern =  rf'^fold_{re.escape(title)}_summary_confidences_\d+\.json$'
    
    # List files in the directory and filter those matching the pattern
    summary_confidence_files = [
        text for text in os.listdir(AF_prediction_path) if re.search(pattern, text)
    ]
    return summary_confidence_files

def get_best_AF3_model_info(model_repository_path, model_repository_name, sort_by = 'ranking_score', model='AF3'): 
    """
    Returns:
        best_cif_filename (str): The best CIF filename.
        best_model_nr (int): The best model number.
        best_iptm (float): The best inter-chain predicted TM-score.
        best_ptm (float): The best predicted TM-score.
        best_ranking_score (float): The best ranking score.
    """
    if not os.path.exists(model_repository_path):
        # print('been here')
        print(f"Warning: Model repository path '{model_repository_path}' does not exist. Skipping...")
        return '', None, None, None, None, None, None
    
    
    confidence_filename_list = get_AF3_summary_confidence_files(model_repository_path, model_repository_name)
        # confidence_filename_list = get_chai_summary_confidence_files(model_repository_path, model_repository_name)
    
    iptm_array = []
    ranking_score_array = []
    ptm_array = []
    model_nr_array = []
    chain_ptm_array = []
    chain_iptm_array = []
    for ii in range(len(confidence_filename_list)): 
        model_nr_array += [ii]
        confidence_filename = confidence_filename_list[ii]
        full_json_path = os.path.join(model_repository_path, confidence_filename)
        iptm, ptm, ranking_score, chain_ptm, chain_iptm = get_summary_confidence_informations(full_json_path, model=model)
        # iptm, ptm, ranking_score,chain_ptm, chain_iptm = get_summary_confidence_informations(model_repository_path + confidence_filename, model = model)
        iptm_array += [iptm]
        ptm_array += [ptm]
        ranking_score_array += [ranking_score]
        chain_ptm_array += [chain_ptm]
        chain_iptm_array += [chain_iptm]
    confidence_df = pd.DataFrame({'filename': confidence_filename_list,
                'model_nr': model_nr_array,
                 'iptm': iptm_array,
                 'ptm': ptm_array,
                 'ranking_score': ranking_score_array,
                'chain_ptm': chain_ptm_array,
                'chain_iptm': chain_iptm_array})
    ranked_confidence_df = confidence_df.copy().sort_values(sort_by, ascending = False).reset_index(drop = True)
    best_row = ranked_confidence_df.iloc[0]
    best_model_nr = best_row['model_nr']
    best_iptm = best_row['iptm']
    best_ptm = best_row['ptm']
    best_ranking_score = best_row['ranking_score']
    best_chain_ptm = best_row['chain_ptm']
    best_chain_iptm = best_row['chain_iptm']
    if model == 'AF3':
        best_cif_filename = 'fold_' + model_repository_name + '_model_' + str(best_model_nr) + '.cif'
    elif (model == 'boltz1'):
        best_cif_filename = 'abc_' + model_repository_name + '_mmseqs_model_' + str(best_model_nr) + '.cif'
    elif (model == 'chai1'):
        best_cif_filename = 'pred.model_idx_' +  str(best_model_nr) + '.cif'

    return best_cif_filename, best_model_nr, best_iptm, best_ptm, best_ranking_score,best_chain_ptm,best_chain_iptm


def get_structome_best_model_metadata(AF_structure_repository_path, model = 'AF3'): 
    prediction_names_list = [
        d for d in os.listdir(AF_structure_repository_path) 
        if os.path.isdir(os.path.join(AF_structure_repository_path, d))
    ] #only the ones that are directories
    cif_filename_array = []
    iptm_array = []
    ptm_array = []
    ranking_score_array = []
    chain_ptm_array = []
    chain_iptm_array = []
    cif_filepath_array = []
    prediction_type_array = []
    
    for ii in range(len(prediction_names_list)): 
        prediction_name = prediction_names_list[ii]

        prediction_repository = os.path.join(AF_structure_repository_path, prediction_name)


            # prediction_repository = AF_structure_repository_path + prediction_name + '/'
        cif_filename, best_model_nr, best_iptm, best_ptm, best_ranking_score,best_chain_ptm, best_chain_iptm =get_best_AF3_model_info(prediction_repository,prediction_name, model = model)
        cif_filepath_array += [os.path.join(prediction_repository, cif_filename)]
        cif_filename_array += [cif_filename]
        iptm_array += [best_iptm]
        ptm_array += [best_iptm]
        ranking_score_array += [best_ranking_score]
        chain_ptm_array += [best_chain_ptm]
        chain_iptm_array += [best_chain_iptm]
        prediction_type_array += [model]
    
    AF_repository_metadata = pd.DataFrame({'prediction_id': prediction_names_list,
                    'cif_filename': cif_filename_array,
                    'cif_filepath': cif_filepath_array,
                                           'iptm': iptm_array,
                                          'ptm': ptm_array,
                                          'ranking_score': ranking_score_array,
                                          'chain_ptm': chain_ptm_array,
                                          'chain_iptm': chain_iptm_array,
                                          'prediction_type': prediction_type_array
                                          })
    AF_repository_metadata['filepath'] = (
        AF_structure_repository_path +
        AF_repository_metadata['prediction_id'].astype(str) + '/' +
        AF_repository_metadata['cif_filename'].astype(str)
    )
    AF_repository_metadata = AF_repository_metadata[['prediction_id', 'iptm', 'ptm', 'chain_ptm', 'chain_iptm', 'cif_filepath', 'cif_filename']]
    return AF_repository_metadata

