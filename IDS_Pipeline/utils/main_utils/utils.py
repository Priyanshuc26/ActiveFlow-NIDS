import yaml
from IDS_Pipeline.exception.exception import CustomException
from IDS_Pipeline.logging.logger import logging
# import dill
import os,sys
import numpy as np
import pickle
from sklearn.model_selection import RandomizedSearchCV
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


def evaluate_models(X_train, y_train,X_test,y_test,models,param):
    try:
        report = {}

        for i in range(len(list(models))):
            model = list(models.values())[i]
            para=param[list(models.keys())[i]]

            rs = RandomizedSearchCV(model,para,cv=3)
            rs.fit(X_train,y_train)

            #model.fit(X_train, y_train)  # Train model

            y_train_pred = rs.predict(X_train)

            y_test_pred = rs.predict(X_test)
            test_model_score = f1_score(y_test, y_test_pred, average='macro')

            report[list(models.keys())[i]] = test_model_score

        return report

    except Exception as e:
        raise CustomException(e, sys)