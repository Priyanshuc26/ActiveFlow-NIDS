from legacy_code.data_ingestion import DataIngestion
from IDS_Pipeline.components.data_validation import DataValidation
from legacy_code.data_transformation import DataTransformation
from IDS_Pipeline.components.model_trainer import ModelTrainer

from IDS_Pipeline.exception.exception import NetworkSecurityException
from IDS_Pipeline.logging.logger import logging
from IDS_Pipeline.entity.config_entity import DataIngestionConfig, TrainingPipelineConfig, DataValidationConfig, DataTransformationConfig, ModelTrainerConfig
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

        logging.info("Model Training started")
        model_trainer_config = ModelTrainerConfig(trainingpipelineconfig)
        model_trainer = ModelTrainer(model_trainer_config=model_trainer_config,
                                     data_transformation_artifact=data_transformation_artifacts)
        model_trainer_artifact = model_trainer.initiate_model_trainer()
        logging.info("Model Training artifact created")


    except Exception as e:
        raise NetworkSecurityException(e,sys)