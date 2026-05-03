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
    df = df.iloc[100000:]
    # 1,50,000
    # 3,50,000
    
    ## Checking if Inference API is live(Since Simulation Engine sends a post request to API and if API is not live it will give ConnectionError)
    while True:
        try:
            if requests.get("http://127.0.0.1:8000/health").ok:
                logging.info("API ready, starting simulation...")
                break
        except:
            print('Waiting For Inference API to get started')
            time.sleep(1.5)
    
    for rows in df.itertuples(index=False):
        packets = rows._asdict()      # NamedTuple has _asdict() method to convert the dta into a dictionary
        requests.post(url=API_POST_REQ_IP,json=packets)
        # print(packets,'\n')
        time.sleep(0.01)
except Exception as e:
    raise CustomException(e,sys)