import os
import sys
import pandas as pd
from collections import deque

from fastapi import FastAPI,Request
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

from IDS_Pipeline.exception.exception import CustomException
from IDS_Pipeline.logging.logger import logging

from IDS_Pipeline.components.data_transformation import ColumnNameCleaner, FeatureDropper, InfinityToNanConverter
from IDS_Pipeline.constant.training_pipeline import TOP_FEATURE_SCHEMA_FILE_PATH, NUMBER_LABEL_MAPPING_DICT

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


# Mapping: { "Incoming_PyFlowMeter_Key": "TopFeature_Schema_Key" }
mapping_dict = {
    "psh_flag_cnt": "psh_flag_count",
    "fwd_header_len": "fwd_header_length",
    "tot_fwd_pkts": "total_fwd_packets",
    "totlen_fwd_pkts": "total_length_of_fwd_packets",
    "init_bwd_win_byts": "init_win_bytes_backward",
    "init_fwd_win_byts": "init_win_bytes_forward",
    "dst_port": "destination_port",
    "flow_byts_s": "flow_bytes/s",
    "flow_pkts_s": "flow_packets/s",
    "bwd_pkts_s": "bwd_packets/s",
    "ack_flag_cnt": "ack_flag_count",
    "bwd_header_len": "bwd_header_length",
    "bwd_pkt_len_max": "bwd_packet_length_max",
    "bwd_pkt_len_min": "bwd_packet_length_min",
    "fwd_pkt_len_max": "fwd_packet_length_max",
    "fwd_pkt_len_min": "fwd_packet_length_min",
    "pkt_len_min": "min_packet_length",
    "flow_duration": "flow_duration",
    "flow_iat_mean": "flow_iat_mean",
    "flow_iat_std": "flow_iat_std"
}
total_packet_processed = 0
top_features_schema = read_yaml_file(file_path=TOP_FEATURE_SCHEMA_FILE_PATH)
expected_columns = list(top_features_schema.keys())


# The Memory Buffer (Holds the last 100 packets for Streamlit)
# traffic_buffer = []    #traffic_buffer is a plain Python list. Under concurrent requests (multiple packets arriving simultaneously), appending and popping from it without a lock can cause race conditions. Also, it resets every time the server restarts
traffic_buffer = deque(maxlen=100)


# Intializing our model outside of get_packets() because every time packet is received, it will again load model, which consume all the memory
preprocessor = load_object("final_model/preprocessor.pkl")
final_model = load_object("final_model/model.pkl")
network_model = NetworkModel(preprocessor=preprocessor, model=final_model)

@app.get("/")
def health_check():
    return {"status": "IDS Server is live and watching."}

@app.post("/predict")
async def get_packets(request:Request):
    try:
        packet_data = await request.json()
        
        #Ensuring that flow is not empty
        if not packet_data.get("flows") or len(packet_data["flows"]) == 0:
            raise Exception("Empty or missing flows in packet data")
        
        extracted_flow = packet_data["flows"][0]
        
        df = pd.DataFrame([extracted_flow])
        df.rename(columns=mapping_dict, inplace=True)
        
        df = df[expected_columns]
        # print(df.columns)
        prediction = network_model.predict(df)[0]        
        
        #Converting Back number (from predictions) to label
        prediction = NUMBER_LABEL_MAPPING_DICT[int(prediction)]
        
        # Attach the prediction to the packet data
        extracted_flow["prediction"] = str(prediction)
        
        # Saving to  memory buffer
        traffic_buffer.append(extracted_flow)
            
        global total_packet_processed
        total_packet_processed=total_packet_processed + 1
        
        return {"status": "success", "prediction": str(prediction)}
        # return {"status": "success"}
    
    except Exception as e:
        raise CustomException(e,sys)
    
    
@app.get("/metrics")
def get_metrics():
    return {"live_traffic": list(traffic_buffer), "total_count": total_packet_processed}
    

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)