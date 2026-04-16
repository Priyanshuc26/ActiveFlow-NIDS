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
CONNECTION_NAME:str = "Wi-Fi"
FINAL_MODEL_DIR:str =  "final_model"

SAVED_MODEL_DIR =os.path.join("saved_models")
MODEL_FILE_NAME = "model.pkl"
MANUAL_SEED = 42



"""
Data Ingestion related constant start with DATA_INGESTION VAR NAME
"""

# DATA_INGESTION_COLLECTION_NAME: str = "Network_Data"
# DATA_INGESTION_DATABASE_NAME: str = "MY_DATABASE"
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
    0 : 300000
}

ST_SAMPLER_PARAMS:dict = {
    0 : 300000,
    1 : 110000,
    2 : 94000,
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

NUMBER_LABEL_MAPPING_DICT = {
    0: 'BENIGN',
    1: 'DDoS',
    2: 'PortScan',
    3: 'DoS Attack',
    4: 'Brute Force',
    5: 'Botnet',
    6: 'Web Attack'
}

"""
Model Trainer related constant start with MODE TRAINER VAR NAME
"""
MODEL_TRAINER_DIR_NAME: str = "model_trainer"
MODEL_TRAINER_TRAINED_MODEL_DIR: str = "trained_model"
MODEL_TRAINER_TRAINED_MODEL_NAME: str = "model.pkl"
MODEL_TRAINER_EXPECTED_SCORE: float = 0.6
MODEL_TRAINER_OVER_FITTING_UNDER_FITTING_THRESHOLD: float = 0.05