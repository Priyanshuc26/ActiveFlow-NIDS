import pandas as pd
import hashlib
import zipfile
import os
import sys
import datetime
import glob
from sklearn.model_selection import train_test_split

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
            
            #Logging basic information about all the files present in zip file
            with zipfile.ZipFile (raw_data_file_path) as zip_ref:
                logging.info("\n\n --------------Raw Data All CSV file information-----------------")
                for file in zip_ref.infolist():
                    logging.info(f"Filename: {file.filename}")
                    logging.info(f"Modified: {datetime.datetime(*file.date_time)}")
                    logging.info(f"Normal size: {file.file_size} bytes")
                    logging.info(f"Compressed size: {file.compress_size} bytes")
                    logging.info("-" * 20)
                logging.info("------------------------------------------------------------------ \n\n")
                
                #Extracting files that have .csv as extension
                csv_files = [name for name in zip_ref.namelist() if name.endswith('.csv')]
                
                #Concatinating all the csv files into one single list
                concated_list = []
                for csv_file in csv_files:
                    with zip_ref.open(csv_file,mode='r') as df_file:
                        concated_list.append(pd.read_csv(df_file))
            
            #Concatinating all the csv files into one CSV file from a list            
            master_dataset = pd.concat(concated_list)
            logging.info(f"Shape of Master Dataset: {master_dataset.shape}")
            return master_dataset
                
                                       
        except Exception as e:
            raise CustomException(e,sys)
        
        
    def save_and_split_data(self,master_dataset:pd.DataFrame):
        try:
            #Saving Master Data into local storage(feature store)
            feature_store_file_path = self.data_ingestion_config.feature_store_file_path
            dir_path = os.path.dirname(feature_store_file_path)
            os.makedirs(dir_path, exist_ok=True)
            master_dataset.to_csv(feature_store_file_path, index=False, header=True)
            logging.info(f"Master Dataset stored at file path: {feature_store_file_path}")  
            
            #Splitting Master data into train and test data
            train_set, test_set = train_test_split(
                master_dataset, test_size=self.data_ingestion_config.train_test_split_ratio
            )

            logging.info("Performed train test split on the dataframe")
            
            logging.info(f"Train set shape: {train_set.shape} and Test set shape: {test_set.shape}")
            dir_path = os.path.dirname(self.data_ingestion_config.training_file_path)
            os.makedirs(dir_path, exist_ok=True)
            logging.info(f"Exporting train and test file path.")

            train_set.to_csv(self.data_ingestion_config.training_file_path, index=False, header=True)
            test_set.to_csv(self.data_ingestion_config.testing_file_path, index=False, header=True)
            logging.info(f"Exported train and test file path.")
            
        except Exception as e:
            raise CustomException(e,sys)    
        
        
    def initiate_data_ingestion(self):
        try:
            logging.info("*******************Starting Data Ingestion Stage*******************")
            
            self.check_raw_data_integrity(ORIGINAL_MD5_CODE)
            df = self.zip_file_extractor()
            self.save_and_split_data(df)
            
            logging.info("Data ingestion final step: Storing Data Ingestion Artifact")
            dataingestionartifact = DataIngestionArtifact(trained_file_path=self.data_ingestion_config.training_file_path,
                                                          test_file_path=self.data_ingestion_config.testing_file_path)
            return dataingestionartifact

        except Exception as e:
            raise CustomException(e,sys)
        
 
if __name__ == '__main__':    
    data_ingestion_config = DataIngestionConfig(training_pipeline_config=TrainingPipelineConfig())
    data_ingestion = DataIngestion(data_ingestion_config=data_ingestion_config)
    data_ingestion.initiate_data_ingestion()         