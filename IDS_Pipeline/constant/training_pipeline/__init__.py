import os
import sys
import numpy as np
import pandas as pd

"""
defining common constant variable for training pipeline
"""
TARGET_COLUMN: str = 'label'
PIPELINE_NAME: str = "Intrusion_Detection_System"
ARTIFACT_DIR: str = "Artifacts"
FILE_NAME: str = "master_dataset.csv"
TRAIN_FILE_NAME: str = "train.csv"
TEST_FILE_NAME: str = "test.csv"
RAW_DATA_FILE_PATH: str = "raw_data/lycos-ids2017.zip"
PCAP_FILE_PATH: str = os.path.join("pcap_folder","Friday-WorkingHours.pcap")
PCAP_CSV_FILE_PATH: str = os.path.join("pcap_folder","Friday-pcap.csv")
CONNECTION_NAME:str = "eth0"
FINAL_MODEL_DIR:str =  "final_model"

SAVED_MODEL_DIR =os.path.join("saved_models")
MODEL_FILE_NAME = "model.pkl"
MANUAL_SEED = 42



"""
Data Ingestion related constant start with DATA_INGESTION VAR NAME
"""

DATA_INGESTION_DIR_NAME: str = "data_ingestion"

DATA_INGESTION_FEATURE_STORE_DIR: str = "feature_store"
DATA_INGESTION_INGESTED_DIR: str = "ingested"
DATA_INGESTION_TRAIN_TEST_SPLIT_RATIO: float = 0.25


SCHEMA_FILE_PATH = os.path.join("data_schema", "schema.yaml")
TOP_FEATURE_SCHEMA_FILE_PATH = os.path.join("data_schema", "top_features.yaml")



"""
Data Validation related constant start with DATA VALIDATION VAR NAME
"""
DATA_VALIDATION_DIR_NAME: str = "data_validation"
DATA_VALIDATION_VALID_DIR: str = "validated"
DATA_VALIDATION_INVALID_DIR: str = "invalid"
DATA_VALIDATION_DRIFT_REPORT_DIR: str = "drift_report"
DATA_VALIDATION_DRIFT_REPORT_FILE_NAME: str = "report.yaml"



"""
Data Transformation related constant start with DATA TRANSFORMATION VAR NAME
"""
DATA_TRANSFORMATION_DIR_NAME: str = "data_transformation"
DATA_TRANSFORMATION_TRANSFORMED_DATA_DIR: str = "transformed"
DATA_TRANSFORMATION_TRANSFORMED_OBJECT_DIR: str = "transformed_object"
PREPROCESSING_OBJECT_FILE_NAME = "preprocessor.pkl"

# imputer to replace nan value
DATA_TRANSFORMATION_IMPUTER_PARAMS:dict = {"missing_values": np.nan,
                                        "strategy": "median" }

UNDER_SAMPLER_PARAMS:dict = {
    0 : 350000
}

ST_SAMPLER_PARAMS:dict = {
    0 : 350000,
    1 : 176293,
    2 : 104073,
    3 : 82000,
    4 : 40000,
    5 : 14000,
    6 : 6000
    }

LABEL_MAPPING_DICT:dict = {
    'benign': 0,
    'dos_hulk': 1,
    'dos_goldeneye': 1,
    'dos_slowloris': 1,
    'dos_slowhttptest': 1,
    'portscan': 2,
    'ddos': 3,
    'ftp_patator': 4,
    'ssh_patator': 4,
    'webattack_bruteforce': 5,
    'webattack_xss': 5,
    'webattack_sql_injection': 5,
    'bot': 6,
    'heartbleed': np.nan
}


"""
Model Trainer related constant start with MODE TRAINER VAR NAME
"""
MODEL_TRAINER_DIR_NAME: str = "model_trainer"
MODEL_TRAINER_TRAINED_MODEL_DIR: str = "trained_model"
MODEL_TRAINER_TRAINED_MODEL_NAME: str = "model.pkl"
MODEL_TRAINER_EXPECTED_SCORE: float = 0.6
MODEL_TRAINER_OVER_FITTING_UNDER_FITTING_THRESHOLD: float = 0.05


"""
Simulation Engine related constant
"""

SIMULATION_FILE_PATH:str = os.path.join("simulation_file","Friday-WorkingHours.pcap_lycos.csv")
API_POST_REQ_IP:str = "http://192.168.29.83:8000/predict"


"""
Inference API related constant
"""

NUMBER_LABEL_MAPPING_DICT:dict = {
    0: 'benign',
    1: 'dos',
    2: 'portscan',
    3: 'ddos',
    4: 'brute_force',
    5: 'web_attack',
    6: 'bots'
}

#  list of public IPs from around the world to test our map
SPOOF_IPS = [
    "8.8.8.8",        # USA
    "212.58.244.20",  # UK 
    "1.1.1.1",        # Australia 
    "114.114.114.114",# China
    "82.165.177.154", # Germany
    "103.10.197.212"  # India
]