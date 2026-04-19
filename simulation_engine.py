import pandas as pd
import sys
import time
import requests

from IDS_Pipeline.logging.logger import logging
from IDS_Pipeline.exception.exception import CustomException
from IDS_Pipeline.constant.training_pipeline import SIMULATION_FILE_PATH,API_POST_REQ_IP

try:
    df = pd.read_csv(SIMULATION_FILE_PATH) 
    df.drop(columns=['flow_id','label'],inplace=True)
    df = df.iloc[350000:]
    
    for rows in df.itertuples(index=False):
        packets = rows._asdict()      # NamedTuple has _asdict() method to convert the dta into a dictionary
        requests.post(url=API_POST_REQ_IP,json=packets)
        # print(packets,'\n')
        time.sleep(0.001)
except Exception as e:
    raise CustomException(e,sys)