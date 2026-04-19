import pandas as pd
import sys
import time
import requests

from IDS_Pipeline.logging.logger import logging
from IDS_Pipeline.exception.exception import CustomException

try:
    df = pd.read_csv('./pcap_processed_csv/Friday-WorkingHours.pcap_lycos.csv') 
    df.drop(columns=['flow_id','label'],inplace=True)
    df = df.iloc[350000:]
    
    for rows in df.itertuples(index=False):
        packets = rows._asdict()
        requests.post(url='http://192.168.29.83:8000/predict',json=packets)
        # print(packets,'\n')
        time.sleep(0.001)
except Exception as e:
    raise CustomException(e,sys)