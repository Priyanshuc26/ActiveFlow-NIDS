import pandas as pd
import numpy as np

from IDS_Pipeline.constant.training_pipeline import TOP_FEATURE_SCHEMA_FILE_PATH
from IDS_Pipeline.entity.artifact_entity import DataValidationArtifact,DataTransformationArtifact
from IDS_Pipeline.entity.config_entity import DataTransformationConfig
from IDS_Pipeline.logging.logger import logging
from IDS_Pipeline.exception.exception import CustomException
from IDS_Pipeline.utils.main_utils.utils import save_numpy_array_data, save_object, read_yaml_file

from sklearn.base import BaseEstimator, TransformerMixin

from sklearn.base import BaseEstimator, TransformerMixin
import pandas as pd

class ColumnNameCleaner(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass
    
    # There is nothing to learn here for fit() function(It do the mathematics like in StandardScaler, it calculates the mean ans std. deviation), so we just return the object itself (return self) and move on to the transformation.    
    def fit(self, df: pd.DataFrame, y=None):
        return self
        
    def transform(self, df: pd.DataFrame, y=None):
        df = df.copy()    # If we manipulate the dataframe directly without copying it first, Pandas will frequently throw a massive red SettingWithCopyWarning. In somecase it can also corrupt original data
        df.columns = [col.strip().lower().replace(' ', '_').replace('(', '').replace(')', '') for col in df.columns]
        return df
     
        
class FeatureDropper(BaseEstimator,TransformerMixin):
    def __init__(self, top_feature_yaml_path):
        # We are reading yaml file init func. because we want yaml file to load once and be saved. If we access it in transform() function it will lead to I/O crash as during every single packet transformation, it will load yaml file creating Bottleneck
        self.top_feature_dict = read_yaml_file(file_path=top_feature_yaml_path)
        
    def fit(self, df: pd.DataFrame, y=None):
        return self
    
    def transform(self, df: pd.DataFrame, y=None):
        df = df.copy()
        top_feature_columns = self.top_feature_dict.keys()
        df = df.loc[:,list(top_feature_columns)]
        # df = df.drop(columns=[df.columns not in top_feature_columns],axis=1)
        return df
   
        
class InfinityToNanConverter(BaseEstimator,TransformerMixin):
    def __init__(self):
        pass 
    
    def fit(self, df: pd.DataFrame, y=None):
        return self
        
    def transform(self, df: pd.DataFrame, y=None):
        df = df.copy()
        df = df.replace([np.inf, -np.inf], np.nan)
        return df