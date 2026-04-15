import pandas as pd
import hashlib
import zipfile
import os
import sys
import datetime
# import glob
from sklearn.model_selection import train_test_split

from IDS_Pipeline.exception.exception import CustomException
from IDS_Pipeline.logging.logger import logging

#Loading Entities
from IDS_Pipeline.entity.config_entity import DataIngestionConfig
from IDS_Pipeline.entity.artifact_entity import DataIngestionArtifact
from IDS_Pipeline.entity.config_entity import TrainingPipelineConfig
from IDS_Pipeline.constant.training_pipeline import TARGET_COLUMN
from IDS_Pipeline.utils.main_utils.utils import custom_train_test_split

from dotenv import load_dotenv
load_dotenv()



class DataIngestion:
    def __init__(self,data_ingestion_config: DataIngestionConfig):
        try:
            self.data_ingestion_config = data_ingestion_config
        except Exception as e:
            raise CustomException(e,sys)
        
        
    def check_raw_data_integrity(self):
        try:
            raw_data_file_path = self.data_ingestion_config.raw_data_file_path
            status = False
            ORIGINAL_MD5_CODE = os.getenv('ORIGINAL_MD5_CODE')   # Fix - only fetches the variable when the function is actively called.
            
            logging.info("Checking for Data Integrity")
            with open(raw_data_file_path, "rb") as f:
                digest = hashlib.file_digest(f, "md5")
            logging.info(f"Calculated MD5 Hash: {digest.hexdigest()}")

            if digest.hexdigest() == ORIGINAL_MD5_CODE:
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
                        df = pd.read_csv(df_file)
                        
                        # Fix - extracting day names(monday, tuesday, etc.) by using csv file name
                        df['day'] = os.path.basename(csv_file).split("-")[0].lower()
                        concated_list.append(df)
            
            #Concatinating all the csv files into one CSV file from a list            
            master_dataset = pd.concat(concated_list,ignore_index=True)   #Fix - This forces Pandas to seamlessly number the massive dataset from 0 to 1.8 Million saving RAM.
            
            # Fix - Shuffling the dataset. When we concat the data of different files, the data is still in sequential form, which cannot be purely resolved during train_test_split(using stratify method), which will lead to splitting of sequential rows into train and test df(which should not haoppen in case of network data bcoz rows are interdependent of each other[like in ddos attack]) this can lead model to overfit and memorize data
            master_dataset = master_dataset.sample(frac=1, random_state=42).reset_index(drop=True)
            
            logging.info(f"Shape of Master Dataset: {master_dataset.shape}")
            return master_dataset
                
                                       
        except Exception as e:
            raise CustomException(e,sys)
        
        
    def save_and_split_data(self,master_dataset:pd.DataFrame):
        try:
            #Saving Master Data into local storage(feature store)
            feature_store_file_path = self.data_ingestion_config.feature_store_file_path
            # target_column = TARGET_COLUMN
            random_state = self.data_ingestion_config.random_state
            
            dir_path = os.path.dirname(feature_store_file_path)
            os.makedirs(dir_path, exist_ok=True)
            master_dataset.to_csv(feature_store_file_path, index=False, header=True)
            logging.info(f"Master Dataset stored at file path: {feature_store_file_path}")  
            
            #Splitting Master data into train and test data
            # Major Fix - Splitting data with help of days and taking a part of friday.csv as our test data to check the model ability on completely predict new data.Before we were splitting the same data into train and test (eg. friday data was in train df also and test df also). As previously data was also sequential, it lead same type of data to split into train and test, which lead to model memorizing the data and predicting the same data in test as attack
            train_set, test_set = custom_train_test_split(master_df=master_dataset,random_state=random_state)

            logging.info("Performed custom flow-based + temporal train-test split")
            
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
            
            self.check_raw_data_integrity()
            df = self.zip_file_extractor()
            self.save_and_split_data(df)
            
            logging.info("Data ingestion final step: Storing Data Ingestion Artifact")
            dataingestionartifact = DataIngestionArtifact(train_file_path=self.data_ingestion_config.training_file_path,
                                                          test_file_path=self.data_ingestion_config.testing_file_path)
            return dataingestionartifact

        except Exception as e:
            raise CustomException(e,sys)
        
 
if __name__ == '__main__':    
    data_ingestion_config = DataIngestionConfig(training_pipeline_config=TrainingPipelineConfig())
    data_ingestion = DataIngestion(data_ingestion_config=data_ingestion_config)
    data_ingestion.initiate_data_ingestion()         