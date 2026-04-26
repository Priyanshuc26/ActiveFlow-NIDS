from IDS_Pipeline.constant.training_pipeline import SAVED_MODEL_DIR, MODEL_FILE_NAME, TOP_FEATURE_SCHEMA_FILE_PATH
from IDS_Pipeline.components.data_transformation import ColumnNameCleaner, FeatureDropper, InfinityToNanConverter
from IDS_Pipeline.utils.main_utils.utils import read_yaml_file

import os, sys
import shap
from IDS_Pipeline.exception.exception import CustomException
from IDS_Pipeline.logging.logger import logging

top_features_list = list(read_yaml_file(TOP_FEATURE_SCHEMA_FILE_PATH).keys())

class NetworkModel:
    def __init__(self, preprocessor, model):
        try:
            self.preprocessor = preprocessor
            self.model = model
            self.explainer = shap.TreeExplainer(model=model, feature_names=top_features_list)
        except Exception as e:
            raise CustomException(e,sys)


    def predict(self,x,explain=False):
        try:
            x_transform = self.preprocessor.transform(x)
            y_hat = self.model.predict(x_transform)
            
            if explain:
                shap_values = self.explainer(X=x_transform)
                return y_hat,shap_values
                
            return y_hat

        except Exception as e:
            raise CustomException(e,sys)
