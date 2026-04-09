import os
import sys

from IDS_Pipeline.exception.exception import CustomException
from IDS_Pipeline.logging.logger import logging

from IDS_Pipeline.entity.artifact_entity import DataTransformationArtifact, ModelTrainerArtifact
from IDS_Pipeline.entity.config_entity import ModelTrainerConfig, TrainingPipelineConfig

from IDS_Pipeline.components.data_transformation import ColumnNameCleaner, FeatureDropper, InfinityToNanConverter
#Importing our custom transformer classes, so that pickle file can map the variable present in transformer pipeline with actual pipeline's code
#When pickle saves an object like StandardScaler, it saves its absolute library path (e.g., sklearn.preprocessing._data.StandardScaler).
# When loading the file later, pickle automatically looks inside the installed sklearn library, follows that exact directory path, and imports it under the hood. we don't need to import it manually because its location is statically mapped in your environment.
#For standard tools like StandardScaler, Python already knows where to find the code inside the installed sklearn library. For custom transfomer class like ColumnNameCleaner, Python has no idea where the code is until you explicitly provide it by using an import statement.

from IDS_Pipeline.utils.ml_utils.model.estimator import NetworkModel
from IDS_Pipeline.utils.main_utils.utils import save_object, load_object, evaluate_models
from IDS_Pipeline.utils.main_utils.utils import load_numpy_array_data
from IDS_Pipeline.utils.ml_utils.metric.classification_metric import get_classification_score

from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

import mlflow
import dagshub


class ModelTrainer:
    def __init__(self, model_trainer_config: ModelTrainerConfig, data_transformation_artifact: DataTransformationArtifact):
        try:
            self.model_trainer_config = model_trainer_config
            self.data_transformation_artifact = data_transformation_artifact
        except Exception as e:
            raise CustomException(e,sys)

    ## Track the mlflow
    def track_mlflow(self, best_model, classification_metric):
        try:
            dagshub.init(repo_owner='Priyanshuc26', repo_name='ActiveFlow_IDS', mlflow=True)
            with mlflow.start_run():
                f1_score = classification_metric.f1_score
                precision = classification_metric.precision_score
                recall = classification_metric.recall_score

                mlflow.log_metric("f1_score", f1_score)
                mlflow.log_metric("precision", precision)
                mlflow.log_metric("recall", recall)
                mlflow.sklearn.log_model(best_model, "model")
        except Exception as e:
            raise CustomException(e,sys)


    def train_model(self, x_train, y_train, x_test, y_test):
        try:
            logging.info("Starting Model Training")
            models = {
                "LightGBM": LGBMClassifier(n_jobs=-1, random_state=42), #Use all the core
                "XGBoost": XGBClassifier(n_jobs=-1, random_state=42, tree_method='hist'),
                # During Intial testing Random Forest performed worst among all with 88.07% f1 score, so we will not use it
                # "RandomForestClassifier": RandomForestClassifier(n_jobs=2,verbose=1) #use only 2 cores
            }

            params = {
                "LightGBM": {
                    'learning_rate': [0.01, 0.05, 0.1],
                    'n_estimators': [100, 200, 300],
                    'max_depth': [10, 20, -1],
                    'num_leaves': [31, 63, 127], # LightGBM grows leaf-wise, this is its most powerful dial
                    'subsample': [0.8, 0.9, 1.0] # Prevents overfitting by randomly dropping rows per tree
                },
                
                "XGBoost": {
                    'learning_rate': [0.01, 0.05, 0.1],
                    'n_estimators': [100, 200, 300],
                    'max_depth': [5, 10, 15], # XGBoost grows depth-wise, so we cap it lower than Random Forest
                    'subsample': [0.8, 0.9, 1.0],
                    'colsample_bytree': [0.8, 1.0] # Randomly drops features per tree to find hidden patterns
                }
                
                # "RandomForestClassifier": {
                # 'n_estimators': [100, 200, 300],
                # 'max_depth': [15, 25, None],
                # 'min_samples_split': [2, 5, 10],
                # 'criterion': ['gini', 'entropy']
                # },
            }

            logging.info("Starting Hyperparameter Tuning")
            model_report,fitted_models_dict = evaluate_models(X_train=x_train, y_train=y_train, X_test=x_test, y_test=y_test, models = models, param = params)


            ## To get the best model name from dict and best model score from dict
            best_model_name = max(model_report, key=model_report.get)
            best_model_score = max(sorted(model_report.values()))
            
            if best_model_score < 0.75:
                raise Exception("No acceptable model found. Best model scored below 75%.")

            logging.info(f"Best Model is {best_model_name} with score {best_model_score}")
            best_model = fitted_models_dict[best_model_name]

            y_train_pred = best_model.predict(x_train)
            classification_train_metric = get_classification_score(y_train, y_train_pred)
            logging.info(f'Classfication metrics based on X_train: {classification_train_metric}')
            
            ## Tracking mlflow
            logging.info("Tracking Model using MLflow")
            self.track_mlflow(best_model, classification_train_metric) #To track it by using UI, write mlflow ui on terminal

            y_test_pred = best_model.predict(x_test)
            classification_test_metric = get_classification_score(y_test, y_test_pred)
            logging.info(f'Classfication metrics based on X_test: {classification_test_metric}')

            logging.info("Loading Preprocessor Object")
            preprocessor = load_object(file_path=self.data_transformation_artifact.transformed_object_file_path)
            model_dir_path = os.path.dirname(self.model_trainer_config.trained_model_file_path)
            os.makedirs(model_dir_path, exist_ok=True)

            logging.info("Saving Preprocessor and model in NetworkModel object")
            Network_Model = NetworkModel(preprocessor=preprocessor,model= best_model)
            save_object(self.model_trainer_config.trained_model_file_path, obj=Network_Model)

            # model pusher
            logging.info("Pushing final model")
            save_object("final_model/model.pkl", best_model)

            ## Model Trainer Artifact
            
            model_trainer_artifact = ModelTrainerArtifact(trained_model_file_path= self.model_trainer_config.trained_model_file_path,
                                train_metric_artifact=classification_train_metric,
                                test_metric_artifact=classification_test_metric)

            logging.info(f"Model Trainer Final Step. Model Trainer artifact: {model_trainer_artifact}")
            return model_trainer_artifact

        except Exception as e:
            raise CustomException(e,sys)


    def initiate_model_trainer(self):
        try:
            logging.info("*******************Starting Model Training and Evaluation Stage*******************")
            train_file_path = self.data_transformation_artifact.transformed_train_file_path
            test_file_path = self.data_transformation_artifact.transformed_test_file_path

            logging.info("Loading Train and Test array")
            #Loading training and testing array
            train_arr = load_numpy_array_data(train_file_path)
            test_arr = load_numpy_array_data(test_file_path)

            logging.info("Dividing Train and Test array into X_train, y_train, X_test, y_test")
            X_train, y_train, X_test, y_test = (
                train_arr[:,:-1],
                train_arr[:,-1],
                test_arr[:,:-1],
                test_arr[:,-1],
            )

            model_trainer_artifact = self.train_model(X_train, y_train, X_test, y_test)
            return model_trainer_artifact

        except Exception as e:
            raise CustomException(e,sys)

if __name__ == "__main__":
    model_trainer_config = ModelTrainerConfig(training_pipeline_config=TrainingPipelineConfig())
    data_transformation_artifact = DataTransformationArtifact(
        transformed_object_file_path= "Artifacts/data_transformation/transformed_object/preprocessing.pkl",
        transformed_train_file_path= "Artifacts/data_transformation/transformed/train.npy",
        transformed_test_file_path= "Artifacts/data_transformation/transformed/test.npy"
    )
    
    model_trainer = ModelTrainer(model_trainer_config=model_trainer_config,data_transformation_artifact=data_transformation_artifact)
    model_trainer.initiate_model_trainer()