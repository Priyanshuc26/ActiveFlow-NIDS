import yaml
from IDS_Pipeline.exception.exception import CustomException
from IDS_Pipeline.logging.logger import logging
# import dill
import os,sys
import numpy as np
import pandas as pd
import pickle
from sklearn.model_selection import RandomizedSearchCV, train_test_split
from sklearn.metrics import f1_score

def read_yaml_file(file_path: str) -> dict:
    try:
        with open(file_path, "rb") as yaml_file:
            return yaml.safe_load(yaml_file)
    except Exception as e:
        raise CustomException(e, sys)

def write_yaml_file(file_path: str, content: object, replace: bool = False) -> None:
    try:
        if replace:
            if os.path.exists(file_path):
                os.remove(file_path)
        os.makedirs (os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as file:
            yaml.dump(content, file)
            
    except Exception as e:
        raise CustomException(e, sys)

def save_numpy_array_data(file_path: str, array: np.array):
    """
    Save numpy array data to file
    file_path: str location of file to save
    array: np.array data to save
    """
    try:
        dir_path = os.path.dirname(file_path)
        os.makedirs (dir_path, exist_ok=True)
        with open(file_path, "wb") as file_obj:
            np.save(file_obj,array)
    except Exception as e:
        raise CustomException(e,sys) from e


def load_numpy_array_data(file_path: str) -> np.array:
    """
    load numpy array data from file
    file_path: str location of file to load
    return: np.array data loaded
    """
    try:
        with open(file_path, "rb") as file_obj:
            return np.load(file_obj)
    except Exception as e:
        raise CustomException(e, sys) from e


def save_object(file_path: str, obj: object) -> None:
    try:
        logging.info("Entered the save_object method of MainUtils class")
        os.makedirs (os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as file_obj:
            pickle.dump(obj, file_obj)
        logging.info("Exited the save_object method of Main Utils class")
    except Exception as e:
        raise CustomException(e, sys) from e



def load_object(file_path: str,) -> object:
    try:
        if not os.path.exists(file_path):
            raise Exception(f"The file: {file_path} is not exists")
        with open(file_path, "rb") as file_obj:
            print(file_obj)
            return pickle.load(file_obj)
    except Exception as e:
        raise CustomException(e, sys) from e


def custom_train_test_split(master_df: pd.DataFrame,random_state:int):
    try:
        day_col = master_df["day"].str.lower()

        monday_to_thursday = master_df[
            day_col.isin(["monday", "tuesday", "wednesday", "thursday"])
        ].copy()
        logging.info(f"Shape of dataframe containing days as Monday to Thursday: {monday_to_thursday.shape}")
        friday_data = master_df[day_col == "friday"].copy()
        logging.info(f"Shape of dataframe containing days as Friday: {friday_data.shape}")

        # Flow-level labels
        flow_labels = friday_data.groupby("flow_id")["label"].first().reset_index()
        logging.info(f"flow labels: {flow_labels.head(10)}")

        # Safety check
        label_counts = flow_labels["label"].value_counts()
        rare_classes = label_counts[label_counts < 2]

        if not rare_classes.empty:
            raise ValueError(f"Classes too small for stratified split: {rare_classes.to_dict()}")

        # Stratified split
        train_flows, test_flows = train_test_split(
            flow_labels,
            test_size=0.35,
            stratify=flow_labels["label"],
            random_state=random_state
        )

        # Map back
        train_friday = friday_data[friday_data["flow_id"].isin(train_flows["flow_id"])]
        test_friday  = friday_data[friday_data["flow_id"].isin(test_flows["flow_id"])]
        logging.info(f"Train friday shape: {train_friday.shape} and Test friday shape: {test_friday.shape}")

        train_set = pd.concat([monday_to_thursday, train_friday])
        test_set  = test_friday

        # Shuffle
        # train_set = train_set.sample(frac=1, random_state=42)
        # test_set = test_set.sample(frac=1, random_state=42)
        # train_set.drop(columns=['day'],inplace=True)
        # test_set.drop(columns=['day'],inplace=True)

        return train_set.reset_index(drop=True), test_set.reset_index(drop=True)
    except Exception as e:
        raise CustomException(e,sys)
    

def evaluate_models(X_train, y_train,X_test,y_test,models,param):
    try:
        model_report = {}
        fitted_models = {} #returns a dictionarary of already fitted and trained model from hyperparameter tuning

        for i in range(len(list(models))):
            model_name = list(models.keys())[i]
            logging.info(f"Running Hyperparameter Tuning for: {model_name}")
            model = list(models.values())[i]
            para = param[model_name]

            rs = RandomizedSearchCV(estimator=model, param_distributions=para, cv=3, n_iter=7, n_jobs=1, random_state=42, scoring='f1_macro')     # RandomizedSearchCV does not train original model. It creates an internal clone of the model, trains the clone, and evaluates it. 
            rs.fit(X_train,y_train)

            best_model = rs.best_estimator_
            logging.info(f"Best Parameter for {model_name} are: {best_model}")
            y_test_pred = best_model.predict(X_test)
            
            
            test_model_score = f1_score(y_test, y_test_pred, average='macro')     #calculates the F1-score for each class and averages them equally, regardless of size
            logging.info(f"f1_score of {model_name} is {test_model_score}")

            model_report[model_name] = test_model_score
            fitted_models[model_name] = rs.best_estimator_

        return model_report,fitted_models

    except Exception as e:
        raise CustomException(e, sys)