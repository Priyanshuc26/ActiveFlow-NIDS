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
        # if not packet_data.get("flows") or len(packet_data["flows"]) == 0:
        if not packet_data or len(packet_data) == 0:
            raise Exception("Empty or missing flows in packet data")
        
        # extracted_flow = packet_data["flows"][0]
        
        df = pd.DataFrame([packet_data])  #json dont have index value in it, but pandas needs index to create a Dataframe, that why we are wrapping our data into list([])
        
        # print(df.columns)
        prediction = network_model.predict(df)        
        
        #Converting Back number (from predictions) to label
        prediction = NUMBER_LABEL_MAPPING_DICT[int(prediction[0])]
        
        # Attach the prediction to the packet data
        packet_data["prediction"] = str(prediction)
        
        # Saving to  memory buffer
        traffic_buffer.append(packet_data)
            
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