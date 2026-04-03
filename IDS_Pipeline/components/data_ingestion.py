import pandas as pd
import hashlib
import zipfile
import os
import sys
import datetime
import glob

from IDS_Pipeline.exception.exception import CustomException
from IDS_Pipeline.logging.logger import logging

#Loading Entities
from IDS_Pipeline.entity.config_entity import DataIngestionConfig
from IDS_Pipeline.entity.artifact_entity import DataIngestionArtifact
from IDS_Pipeline.entity.config_entity import TrainingPipelineConfig

from dotenv import load_dotenv
load_dotenv()

ORIGINAL_MD5_CODE = os.getenv('ORIGINAL_MD5_CODE')

class DataIngestion:
    def __init__(self,data_ingestion_config: DataIngestionConfig):
        try:
            self.data_ingestion_config = data_ingestion_config
        except Exception as e:
            raise CustomException(e,sys)
        
        
    def check_raw_data_integrity(self, original_md5_code):
        try:
            raw_data_file_path = self.data_ingestion_config.raw_data_file_path
            status = False
            
            logging.info("Checking for Data Integrity")
            with open(raw_data_file_path, "rb") as f:
                digest = hashlib.file_digest(f, "md5")
            print(digest.hexdigest())

            if digest.hexdigest() == original_md5_code:
                logging.info('Raw Data Integrity Checked')
            else:
                raise Exception("Corrupted File Detected!") 
            
        except Exception as e:
            raise CustomException(e,sys)
        
        
    def zip_file_extractor(self):
        try:
            raw_data_file_path = self.data_ingestion_config.raw_data_file_path
            
            with zipfile.ZipFile (raw_data_file_path) as zip_ref:
                logging.info("\n\n --------------Raw Data All CSV file information-----------------")
                for file in zip_ref.infolist():
                    logging.info(f"Filename: {file.filename}")
                    logging.info(f"Modified: {datetime.datetime(*file.date_time)}")
                    logging.info(f"Normal size: {file.file_size} bytes")
                    logging.info(f"Compressed size: {file.compress_size} bytes")
                    logging.info("-" * 20)
                logging.info("------------------------------------------------------------------ \n\n")
                
                
                csv_files = [name for name in zip_ref.namelist() if name.endswith('.csv')]
                print(type(csv_files))
                
                                       
        except Exception as e:
            raise CustomException(e,sys)
        
        
 
if __name__ == '__main__':    
    data_ingestion_config = DataIngestionConfig(training_pipeline_config=TrainingPipelineConfig())
    data_ingestion = DataIngestion(data_ingestion_config=data_ingestion_config)
    data_ingestion.check_raw_data_integrity(ORIGINAL_MD5_CODE)
    data_ingestion.zip_file_extractor()

            