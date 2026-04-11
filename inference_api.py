import os
import sys
import pandas as pd

from fastapi import FastAPI,Request
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

from IDS_Pipeline.exception.exception import CustomException
from IDS_Pipeline.logging.logger import logging

from IDS_Pipeline.components.data_transformation import ColumnNameCleaner, FeatureDropper, InfinityToNanConverter


from IDS_Pipeline.utils.ml_utils.model.estimator import NetworkModel
from IDS_Pipeline.utils.main_utils.utils import load_object

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# The Memory Buffer (Holds the last 100 packets for Streamlit)
traffic_buffer = []

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
        
        df = pd.DataFrame([packet_data])
        prediction = network_model.predict(df)[0]
        
        # Attach the prediction to the packet data
        packet_data["prediction"] = str(prediction)
        
        # Save it to our memory buffer
        traffic_buffer.append(packet_data)
        
        # Keep the buffer lightweight: only store the last 100 packets
        if len(traffic_buffer) > 100:
            traffic_buffer.pop(0)
            
        return {"status": "success", "prediction": str(prediction)}
    except Exception as e:
        raise CustomException(e,sys)
    
    
@app.get("/metrics")
def get_metrics():
    return {"live_traffic": traffic_buffer}
    

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)