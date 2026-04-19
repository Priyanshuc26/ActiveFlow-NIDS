from IDS_Pipeline.constant.training_pipeline import SAVED_MODEL_DIR, MODEL_FILE_NAME
from IDS_Pipeline.components.data_transformation import ColumnNameCleaner, FeatureDropper, InfinityToNanConverter

import os, sys
from IDS_Pipeline.exception.exception import CustomException
from IDS_Pipeline.logging.logger import logging

class NetworkModel:
    def __init__(self, preprocessor, model):
        try:
            self.preprocessor = preprocessor
            self.model = model
        except Exception as e:
            raise CustomException(e,sys)


    def predict(self,x):
        try:
            x_transform = self.preprocessor.transform(x)
            y_hat = self.model.predict(x_transform)
            return y_hat

        except Exception as e:
            raise CustomException(e,sys)
