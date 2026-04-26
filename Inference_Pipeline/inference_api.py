import os
import sys
import pandas as pd
from collections import deque, Counter
import geoip2.database
import ipaddress
import random

from fastapi import FastAPI,Request
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

from IDS_Pipeline.exception.exception import CustomException
from IDS_Pipeline.logging.logger import logging

from IDS_Pipeline.components.data_transformation import ColumnNameCleaner, FeatureDropper, InfinityToNanConverter
from IDS_Pipeline.constant.training_pipeline import TOP_FEATURE_SCHEMA_FILE_PATH, NUMBER_LABEL_MAPPING_DICT, SPOOF_IPS

from IDS_Pipeline.utils.ml_utils.model.estimator import NetworkModel
from IDS_Pipeline.utils.main_utils.utils import load_object, read_yaml_file

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

stats = {
    "packets_processed": 0,
    "prediction_count": {
        "benign": 0,
        "dos": 0,
        "portscan": 0,
        "ddos": 0,
        "brute_force": 0,
        "web_attack": 0,
        "bots": 0
    }
}


# The Memory Buffer (Holds the last 100 packets for Streamlit)
# traffic_buffer = []    #traffic_buffer is a plain Python list. Under concurrent requests (multiple packets arriving simultaneously), appending and popping from it without a lock can cause race conditions. Also, it resets every time the server restarts
traffic_buffer = deque(maxlen=100)


# Intializing our model outside of get_packets() because every time packet is received, it will again load model, which consume all the memory
preprocessor = load_object("./final_model/preprocessor.pkl")
final_model = load_object("./final_model/model.pkl")
network_model = NetworkModel(preprocessor=preprocessor, model=final_model)


# with geoip2.database.Reader('Inference_Pipeline/GeoLite2-City.mmdb') as reader:    #If we define context manager in function it will run each time when the function is called(as context manager opens and closes file when file operation is completed), creating I/O bottleneck
reader = geoip2.database.Reader('Inference_Pipeline/GeoLite2-City.mmdb')         #To prevent closing of file, we will not use context manager(preious bid mistake was too intialize this function in function which can lead to massive memmory leak as file are opening at each itireation, but not closing which can lead to crash of server)
def get_geographical_info(src_ip):
    try:
        response = reader.city(src_ip)
        geographical_info_dict = {
            "country":response.country.name,
            # "represented_country":response.represented_country.name,
            "city":response.city.name,
            "latitude":response.location.latitude,
            "longitude":response.location.longitude,
            # "postal_code":response.postal.code
        }
        return geographical_info_dict
    except Exception as e:
        raise CustomException(e,sys)
        # return {
        #     "country":None,
        #     "city":None,
        #     "latitude":None,
        #     "longitude":None,
        #     }      #Manytimes an IP address maybe missing from mmdb, so to prevent sudden crash we will return dict with None value



@app.get("/")
def health_check():
    return {"status": "IDS Server is live and watching."}

@app.post("/predict")
async def get_packets(request:Request):
    try:
        packet_data = await request.json()
        
        #Ensuring that flow is not empty
        # if not packet_data.get("flows") or len(packet_data["flows"]) == 0:
        if not packet_data or len(packet_data) == 0:
            raise Exception("Empty or missing flows in packet data")
        
        # extracted_flow = packet_data["flows"][0]
        
        df = pd.DataFrame([packet_data])  #json dont have index value in it, but pandas needs index to create a Dataframe, that why we are wrapping our data into list([])
        
        # print(df.columns)
        prediction = network_model.predict(df,explain=False) 
        
        ## Extracting Shap Values
        # class_index = int(prediction[0])
        # shap_dict = shap_values.values[0,:,class_index]
        # packet_data["shap_values"] = shap_dict     #appending shape values to packet data
        
        #Converting Back number (from predictions) to label
        prediction = NUMBER_LABEL_MAPPING_DICT[int(prediction[0])]
        
        # Attach the prediction to the packet data
        packet_data["prediction"] = str(prediction)
        
        
        # global total_packet_processed  #Using global keyword is generally considered as bad practice - coz it becomes hard to debug when code becomes huge, and function are dependent on external variable causing reproduciblity issue
        # total_packet_processed=total_packet_processed + 1
        stats["packets_processed"] += 1
        
        
        #Storing counts of each prediction and sending to our dashboard for visualizing
        stats["prediction_count"][prediction] += 1   
        #Counter almost works same as dict, with main aim of counting
        
        
        #-------  GEO-SPOOFING Injection Starts(needed to do because Simulation file contains private IP "192.168.x.x" and private IP is missing from mmdb)
        src_ip = packet_data.get('src_addr', '127.0.0.1')
        
        try:
            ip_obj = ipaddress.ip_address(src_ip)
            # Overwriting IP with random public IP, if the src_addr in the packet is private IP or localhost 
            if ip_obj.is_private or ip_obj.is_loopback:
                src_ip = random.choice(SPOOF_IPS)
        except ValueError:
            # Assigning random IP if IP is corrupted
            src_ip = random.choice(SPOOF_IPS)
        #Adding geographical data(extracted using src_addr) directly to packet data
        geographical_info = get_geographical_info(src_ip)
        packet_data.update(geographical_info)
        
        # Saving to  memory buffer
        traffic_buffer.append(packet_data)
        
        return {"status": "success", "prediction": str(prediction)}
        # return {"status": "success"}
    
    except Exception as e:
        raise CustomException(e,sys)
    
    
@app.get("/metrics")
def get_metrics():
    return {"live_traffic": list(traffic_buffer), **stats}
    

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
## Updates to be done in upcoming versions:
#  1. Use fastapi's state for managing global state of variables and also use of Redis