from networksecurity.components.data_ingestion import DataIngestion
from networksecurity.components.data_validation import DataValidation
from networksecurity.components.data_transformation import DataTransformation

from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.entity.config_entity import DataIngestionConfig, TrainingPipelineConfig, DataValidationConfig, DataTransformationConfig
import sys

if __name__ == "__main__":
    try:
        trainingpipelineconfig=TrainingPipelineConfig()
        dataingestionconfig=DataIngestionConfig(trainingpipelineconfig)
        data_ingestion = DataIngestion(dataingestionconfig)
        logging.info("Initiate the data ingestion")
        dataingestionartifact = data_ingestion.initiate_data_ingestion()
        logging.info("Data ingestion complete")


        datavalidationconfig = DataValidationConfig(trainingpipelineconfig)
        data_validation = DataValidation(dataingestionartifact, datavalidationconfig)
        logging.info("Data validation initiated")
        data_validation_artifacts = data_validation.initiate_data_validation()
        logging.info("Data validation completed")
        print(data_validation_artifacts)


        datatransformationconfig = DataTransformationConfig(trainingpipelineconfig)
        data_transformation = DataTransformation(data_validation_artifacts, datatransformationconfig)
        logging.info("Data transformation initiated")
        data_transformation_artifacts = data_transformation.initiate_data_transformation()
        logging.info("Data transformation completed")
        print(data_transformation_artifacts)

    except Exception as e:
        raise NetworkSecurityException(e,sys)