from IDS_Pipeline.entity.artifact_entity import DataIngestionArtifact, DataValidationArtifact
from IDS_Pipeline.entity.config_entity import DataValidationConfig, TrainingPipelineConfig
from IDS_Pipeline.constant.training_pipeline import SCHEMA_FILE_PATH

from IDS_Pipeline.exception.exception import CustomException
from IDS_Pipeline.logging.logger import logging

from IDS_Pipeline.utils.main_utils.utils import read_yaml_file, write_yaml_file

# from scipy.stats import ks_2samp #Check two samples of data to find data drift occured or not
from evidently import Dataset
from evidently import DataDefinition
from evidently import Report
from evidently.presets.drift import DataDriftPreset
from evidently.metrics import *
from evidently.presets import *

import pandas as pd
import os,sys


class DataValidation:
    def __init__(self,data_ingestion_artifact:DataIngestionArtifact,
                 data_validation_config: DataValidationConfig,):
        try:
            self.data_ingestion_artifact = data_ingestion_artifact
            self.data_validation_config = data_validation_config
            self._schema_config = read_yaml_file(SCHEMA_FILE_PATH)

        except Exception as e:
            raise CustomException(e,sys)


    @staticmethod
    def read_data(file_path) -> pd.DataFrame:
        try:
            logging.info(f"Reading csv file from path: {file_path}")
            return pd.read_csv(file_path)
        except Exception as e:
            raise CustomException(e, sys)

    def validate_columns(self,dataframe:pd.DataFrame) -> bool:
        try:
            logging.info(f"Validating Column Name and Datatype of {dataframe}")
            schema_dict = self._schema_config
            df_column_dtype = {feature: f'{dataframe[feature].dtype}' for feature in dataframe.columns}
            if schema_dict == df_column_dtype:
                logging.info("Columns name and dtype of both dataframe and schema matched. Columns Validation Sucessful")
                return True
            else:
                logging.info("Columns of Dataframe and Schema mismatched")
                raise Exception("Columns mismatched. Column Validation Failed!")

        except Exception as e:
            raise CustomException(e,sys)
        

    def detect_dataset_drift(self, base_df, current_df) -> bool:
        try:
            logging.info("Calculating and Detecting Data Drift")
            ## Using Dataset and DataDefinition for automatically mapping columns to numerical or categorical
            base_data = Dataset.from_pandas(
                        base_df,
                        data_definition=DataDefinition()
                    )
            
            current_data = Dataset.from_pandas(
                        current_df,
                        data_definition=DataDefinition()
                    )
            
            report = Report([
                        DataDriftPreset()
                        ])

            ## Getting Detailed drift report
            my_eval = report.run(current_data=current_data, reference_data=base_data)
            data_drift_report = my_eval.dict()       #exporting report as dictionrary

            
            
            ## Getting Drift Status
            drift_threshold = data_drift_report["metrics"][0]["config"]["drift_share"]
            actual_drift_share = data_drift_report["metrics"][0]["value"]["share"]
            if actual_drift_share >= drift_threshold:
                raise Exception("Data Drift Occured")
            else:
                logging.info(f"Drift threshold: {drift_threshold} and Actual drift: {actual_drift_share}")
                logging.info("No Data Drift Detected")
                
                ## Creating directory for storing report.yaml (Happens only if no data drift is detected)
                drift_report_file_path = self.data_validation_config.drift_report_file_path  
                dir_path = os.path.dirname(drift_report_file_path)    # Create directory
                logging.info(f"Storing Data drift report: {dir_path}")
                os.makedirs(dir_path, exist_ok=True)
                write_yaml_file(file_path= drift_report_file_path, content=data_drift_report)
                
                return False

        except Exception as e:
            raise CustomException(e,sys)


    def initiate_data_validation(self) -> DataValidationArtifact:
        try:
            logging.info("*******************Starting Data Validation Stage*******************")
            train_file_path = self.data_ingestion_artifact.train_file_path
            test_file_path = self.data_ingestion_artifact.test_file_path

            #Read data the data from train and test
            train_dataframe =DataValidation.read_data(train_file_path)
            test_dataframe =DataValidation.read_data(test_file_path)

            status = self.validate_columns(train_dataframe)
            status = self.validate_columns(test_dataframe)

            #Let's check data drift and store report 
            status = self.detect_dataset_drift(base_df= train_dataframe, current_df= test_dataframe)
            
            #Storing valid train and test csv
            dir_path = os.path.dirname(self.data_validation_config.valid_train_file_path)
            os.makedirs(dir_path, exist_ok=True)
            train_dataframe.to_csv(self.data_validation_config.valid_train_file_path, index=False, header=True)
            test_dataframe.to_csv(self.data_validation_config.valid_test_file_path, index=False, header=True)

            logging.info("Data validation final step: Storing Data validation Artifact")
            data_validation_artifact = DataValidationArtifact(
                validation_status=status,
                valid_train_file_path=self.data_ingestion_artifact.train_file_path,
                valid_test_file_path=self.data_ingestion_artifact.test_file_path,
                invalid_train_file_path=None,
                invalid_test_file_path=None,
                drift_report_file_path=self.data_validation_config.drift_report_file_path,
            )
            return data_validation_artifact


        except Exception as e:
            raise CustomException(e,sys)



if __name__ == "__main__":
    mock_train_path = "Artifacts/data_ingestion/ingested/train.csv" 
    mock_test_path = "Artifacts/data_ingestion/ingested/test.csv"  
    
    ## Inputs for Data Validation
    data_ingestion_artifact = DataIngestionArtifact(
        train_file_path=mock_train_path,
        test_file_path=mock_test_path
    ) 
    #input required for data validation config
    data_validation_config = DataValidationConfig(training_pipeline_config=TrainingPipelineConfig())


    data_validation = DataValidation(data_ingestion_artifact,data_validation_config)

    data_validation.initiate_data_validation()



## Upgrades to be done in upcoming version:
#  * Missing Values (Null) Check -> (Rejecting Column which contains na values more than threshold level)
#  *  Value range check -> (For example: destination_port cannot mathematically be a negative number, and it cannot be greater than 65535)