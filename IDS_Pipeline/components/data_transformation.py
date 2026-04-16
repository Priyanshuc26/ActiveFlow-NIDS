import pandas as pd
import numpy as np
import sys
import os

from IDS_Pipeline.constant.training_pipeline import TOP_FEATURE_SCHEMA_FILE_PATH, DATA_TRANSFORMATION_IMPUTER_PARAMS, TARGET_COLUMN, LABEL_MAPPING_DICT, UNDER_SAMPLER_PARAMS, ST_SAMPLER_PARAMS
from IDS_Pipeline.entity.artifact_entity import DataValidationArtifact,DataTransformationArtifact
from IDS_Pipeline.entity.config_entity import DataTransformationConfig,TrainingPipelineConfig
from IDS_Pipeline.logging.logger import logging
from IDS_Pipeline.exception.exception import CustomException
from IDS_Pipeline.utils.main_utils.utils import save_numpy_array_data, save_object, read_yaml_file

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler
from sklearn.impute import  SimpleImputer

from imblearn.under_sampling import RandomUnderSampler
from imblearn.combine import SMOTETomek


class ColumnNameCleaner(BaseEstimator, TransformerMixin):
    def __init__(self):
        try:
            logging.info(" Cleaning Column Name...")
        except Exception as e:
            raise CustomException(e,sys)
        
    # There is nothing to learn here for fit() function(It do the mathematics like in StandardScaler, it calculates the mean ans std. deviation), so we just return the object itself (return self) and move on to the transformation.    
    def fit(self, df: pd.DataFrame, y=None):
        try:
            return self
        except Exception as e:
            raise CustomException(e,sys)
        
    def transform(self, df: pd.DataFrame, y=None):
        try:
            df = df.copy()    # If we manipulate the dataframe directly without copying it first, Pandas will frequently throw a massive red SettingWithCopyWarning. In somecase it can also corrupt original data
            df.columns = [col.strip().lower().replace(' ', '_').replace('(', '').replace(')', '') for col in df.columns]
            return df
        except Exception as e:
            raise CustomException(e,sys)
     
        
class FeatureDropper(BaseEstimator,TransformerMixin):
    def __init__(self, top_feature_yaml_path):
        try:
            self.top_feature_yaml_path = top_feature_yaml_path
        except Exception as e:
            raise CustomException(e,sys)
        
    def fit(self, df: pd.DataFrame, y=None):
        try:
            # We are reading yaml file in fit func. because we want yaml file to load only once and be saved. If we access it in transform() function it will lead to I/O crash as during every single packet transformation, it will load yaml file creating Bottleneck
            self.top_feature_dict = read_yaml_file(file_path=self.top_feature_yaml_path)    # fix
            self.top_feature_columns = list(self.top_feature_dict.keys())
            logging.info(f" Dropping features that are not important... Top features: {self.top_feature_columns}")
            return self      # The pipeline expects the fit() method to return the transformer object itself so it can instantly chain into the transform() method.
        except Exception as e:
            raise CustomException(e,sys)
    
    def transform(self, df: pd.DataFrame, y=None):
        try:
            df = df.copy()  
            # Finding columns that are in BOTH the YAML file AND the current dataframe
            # valid_columns = [col for col in self.top_feature_columns if col in df.columns]
            
            # previously we checked Selectively, but now we have a strict check on the columns
            missing = [col for col in self.top_feature_columns if col not in df.columns]
            if missing:
                raise ValueError(f"Missing expected columns: {missing}") 
            df = df.loc[:, self.top_feature_columns]
            return df
        except Exception as e:
            raise CustomException(e,sys)
   
        
class InfinityToNanConverter(BaseEstimator,TransformerMixin):
    def __init__(self):
        try:
            logging.info(" Converting infinity values to NaN...")
        except Exception as e:
            raise CustomException(e,sys)
    
    def fit(self, df: pd.DataFrame, y=None):
        try:
            return self
        except Exception as e:
            raise CustomException(e,sys)
        
    def transform(self, df: pd.DataFrame, y=None):
        try:
            df = df.copy()
            df = df.replace([np.inf, -np.inf], np.nan)
            return df
        except Exception as e:
            raise CustomException(e,sys)
    
    
class DataTransformation:
    def __init__(self,data_validation_artifact:DataValidationArtifact,data_transformation_config:DataTransformationConfig):
        try:
            self.data_validation_artifact = data_validation_artifact
            self.data_transformation_config = data_transformation_config
        except Exception as e:
            raise CustomException(e, sys)
       
        
    @staticmethod
    def read_data(file_path) -> pd.DataFrame:
        try:
            logging.info(f"Reading csv file from path: {file_path}")
            return pd.read_csv(file_path)

        except Exception as e:
            raise CustomException(e, sys)
        
        
    def get_data_transformer_object(self) -> Pipeline:
        try:
            logging.info("Starting Data Preprocessing Pipeline")
            preprocessor:Pipeline = Pipeline([
                ('ColumnNameCleaner',ColumnNameCleaner()),
                ('FeatureDropper',FeatureDropper(top_feature_yaml_path=TOP_FEATURE_SCHEMA_FILE_PATH)),
                ('InfinityToNanConverter',InfinityToNanConverter()),
                ('Imputer',SimpleImputer(**DATA_TRANSFORMATION_IMPUTER_PARAMS)),  # using simple imputer to reduce bottleneck (avoid repitative calculations done in KNNImputer)
                ('Scaler',RobustScaler())   # robust scaler ignores outliers and calculate mean and std. deviation between Q1 & Q3
            ])
            
            return preprocessor
        except Exception as e:
            raise CustomException(e,sys)
    
    
    def hybrid_sampling(self,X_train,y_train):
        try:
            logging.info("Starting Hybrid Sampling")
            
            #Choose Hybrid sampling over simply SMOTETomek, because SMOTETomek only oversample the data based upon majority class number which can be computationally expensive if majority class is present in large number
            under_sampler = RandomUnderSampler(sampling_strategy=UNDER_SAMPLER_PARAMS,random_state=42)
            X_under_sampled,y_under_sampled = under_sampler.fit_resample(X_train,y_train)
            logging.info(f"  Under sampling done.X_under_sampled shape: {X_under_sampled.shape},y_under_sampled shape: {y_under_sampled.shape}")
            
            # Fix - Previously we were creating too much synthetic data(300k for each label), which may have lead to distorted pattern and not train model properly on the real life class imbalance, so this time we will apply Smotetomek in controlled manner to avoid overfitting and preventing high synthetic data. We will increase the number of minority significantly but not to the level of majority.
            over_sampler = SMOTETomek(sampling_strategy=ST_SAMPLER_PARAMS)
            X_resampled,y_resampled = over_sampler.fit_resample(X_under_sampled,y_under_sampled)
            logging.info(f"  SMOTETomek applied. X_resampled shape: {X_resampled.shape}, y_resampled shape: {y_resampled.shape}")
            
            return X_resampled,y_resampled
        except Exception as e:
            raise CustomException(e,sys)
        
    
    def initiate_data_transformation(self) -> DataTransformationArtifact:
        try:
            logging.info("*******************Starting Data Transformation Stage*******************")
            #Loading validated train and test df 
            train_df = DataTransformation.read_data(self.data_validation_artifact.valid_train_file_path)
            test_df = DataTransformation.read_data(self.data_validation_artifact.valid_test_file_path)
            
            logging.info("Preprocessing target column name")
            # Globally cleaning all column names so TARGET_COLUMN can be extracted safely
            # train_df.columns = [col.strip().lower().replace(' ', '_').replace('(', '').replace(')', '') for col in train_df.columns]
            # test_df.columns = [col.strip().lower().replace(' ', '_').replace('(', '').replace(')', '') for col in test_df.columns]

            logging.info("Splitting Train and Test Dataframe into input features(X) and target features(y)")
            #Training Dataframe
            train_df[TARGET_COLUMN] = train_df[TARGET_COLUMN].replace(LABEL_MAPPING_DICT) #Mapping labels to number (encoding)
            train_df.dropna(subset=[TARGET_COLUMN], inplace=True)  #droping rows with help of labels which has nan value
            train_df.reset_index(drop=True, inplace=True)   # (Fix) Removing index because the data will be dropped from anywhere which will lead to improper index, leading to crash
            
            input_feature_train_df = train_df.drop(columns=[TARGET_COLUMN], axis=1)   #Splitting into X and y
            target_feature_train_df = train_df[TARGET_COLUMN]


            # Testing dataframe
            test_df[TARGET_COLUMN] = test_df[TARGET_COLUMN].replace(LABEL_MAPPING_DICT)   #label mapping
            test_df.dropna(subset=[TARGET_COLUMN], inplace=True)
            test_df.reset_index(drop=True, inplace=True)
            
            input_feature_test_df = test_df.drop(columns=[TARGET_COLUMN], axis=1)   #Splitting into X and y
            target_feature_test_df = test_df[TARGET_COLUMN]

            ## Preprocessing the input_feature of both train and test df
            preprocessor_object = self.get_data_transformer_object()
            transformed_input_train_feature = preprocessor_object.fit_transform(input_feature_train_df)
            transformed_input_test_feature = preprocessor_object.transform(input_feature_test_df)
            logging.info(f"Preprocessing Complete.")

            # Applying hybrid sampling
            transformed_input_train_feature,transformed_target_train_feature = self.hybrid_sampling(transformed_input_train_feature,target_feature_train_df)

            # Concatinating input features and target features
            train_arr = np.c_[transformed_input_train_feature, np.array(transformed_target_train_feature)]
            test_arr = np.c_[transformed_input_test_feature, np.array(target_feature_test_df)]
            logging.info(f"final train_arr shape: {train_arr.shape} and final test_arr shape shape: {test_arr.shape}")
            
            # save numpy array data
            save_numpy_array_data(self.data_transformation_config.transformed_train_file_path, array=train_arr)
            save_numpy_array_data(self.data_transformation_config.transformed_test_file_path, array=test_arr)
            save_object(self.data_transformation_config.transformed_object_file_path, preprocessor_object)
            logging.info("numpy array saved")


            # model pusher
            logging.info("saving preprocessor object")
            final_model_dir_path = os.path.dirname(self.data_transformation_config.final_preprocessor_object_file_path)
            os.makedirs(final_model_dir_path, exist_ok=True)
            save_object(self.data_transformation_config.final_preprocessor_object_file_path, preprocessor_object)

            #Preparing Data Transformation Artifacts
            logging.info("Data Transformation Final Step: Preparing Data Transformation Artifacts")
            data_transformation_artifact = DataTransformationArtifact(
                transformed_object_file_path = self.data_transformation_config.transformed_object_file_path,
                transformed_train_file_path = self.data_transformation_config.transformed_train_file_path,
                transformed_test_file_path = self.data_transformation_config.transformed_test_file_path
            )

            return data_transformation_artifact

        except Exception as e:
            raise CustomException(e, sys)
        
        
if __name__ == "__main__":
    data_validation_artifact = DataValidationArtifact(
        validation_status=True,
        valid_train_file_path="Artifacts/data_validation/validated/train.csv",
        valid_test_file_path="Artifacts/data_validation/validated/test.csv",
        invalid_train_file_path= None,
        invalid_test_file_path=None,
        drift_report_file_path=None
    )
    data_transformation_config = DataTransformationConfig(training_pipeline_config=TrainingPipelineConfig())
    
    data_transformation = DataTransformation(data_transformation_config=data_transformation_config,data_validation_artifact=data_validation_artifact) 
    data_transformation.initiate_data_transformation()
    
    
    
    
# Upcoming updates in newer versions

# 1. Instead of realying on Hybrid Sampling(Which Creates a lot of synthetic data) for handling imbalance class, we will rely on model to handle, which doesn't need to populate data, This will be done by:
    # a. class weights
    # b. threshold tuning
    # c. cost-sensitive learning
# 2. Strict + More Robust (Dosen't crashes pipeline incase of missing features - handle minor issues, fail only on major ones)