from IDS_Pipeline.entity.artifact_entity import ClassificationMetricArtifact
from IDS_Pipeline.exception.exception import CustomException
from IDS_Pipeline.logging.logger import logging
from sklearn.metrics import f1_score,precision_score,recall_score,confusion_matrix
import sys
import numpy as np


def get_classification_score(y_true,y_pred) -> ClassificationMetricArtifact:
    try:
        # model_f1_score = f1_score(y_true, y_pred, average='macro')
        
        # ----------- FPR for BENIGN (class 0) ----------- 
        model_confusion_matrix = confusion_matrix(y_true, y_pred)
        # TN = correctly predicted benign
        TN = model_confusion_matrix[0, 0]
        # FP = benign misclassified as any attack
        FP = np.sum(model_confusion_matrix[0, :]) - TN
        false_positive_rate = FP / (FP + TN) if (FP + TN) > 0 else 0.0
        
        model_recall_score = recall_score(y_true, y_pred, average=None, zero_division=0)
        model_precision_score=precision_score(y_true,y_pred, average='weighted', zero_division=0)
        classification_metric = ClassificationMetricArtifact(false_positive_rate=false_positive_rate,
                                                             precision_score=model_precision_score,
                                                             recall_score=model_recall_score,
                                                             confusion_matrix=model_confusion_matrix
                                                             )
        return classification_metric
    except Exception as e:
        raise CustomException(e,sys)


