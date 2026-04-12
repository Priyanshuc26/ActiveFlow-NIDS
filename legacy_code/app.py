import sys
import os

import certifi
ca = certifi.where()

from dotenv import load_dotenv
load_dotenv()
mongo_db_url = os.getenv("MONGODB_URL_KEY")
print(mongo_db_url)
import pymongo
from IDS_Pipeline.exception.exception import NetworkSecurityException
from IDS_Pipeline.logging.logger import logging
from IDS_Pipeline.pipeline.training_pipeline import TrainingPipeline

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile,Request
from uvicorn import run as app_run
from fastapi.responses import Response
from starlette.responses import RedirectResponse
import pandas as pd

from IDS_Pipeline.utils.main_utils.utils import load_object

from IDS_Pipeline.utils.ml_utils.model.estimator import NetworkModel


client = pymongo.MongoClient(mongo_db_url, tlsCAFile=ca)

from IDS_Pipeline.constant.training_pipeline import DATA_INGESTION_COLLECTION_NAME
from IDS_Pipeline.constant.training_pipeline import DATA_INGESTION_DATABASE_NAME

database = client[DATA_INGESTION_DATABASE_NAME]
collection = database[DATA_INGESTION_COLLECTION_NAME]

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="./templates")

@app.get("/", tags=["authentication"])
async def index():
    return RedirectResponse(url="/docs")

@app.get("/train")
async def train_route():
    try:
        train_pipeline=TrainingPipeline()
        train_pipeline.run_pipeline()
        return Response("Training is successful")
    except Exception as e:
        raise NetworkSecurityException(e,sys)
    
@app.post("/predict")
async def predict_route(request: Request,file: UploadFile = File(...)):
    try:
        # Read CSV
        df = pd.read_csv(file.file)

        # Load artifacts
        # Recommendation: Use absolute paths or constants here
        preprocessor = load_object("final_model/preprocessor.pkl")
        final_model = load_object("final_model/model.pkl")

        # Initialize your custom estimator
        network_model = NetworkModel(preprocessor=preprocessor, model=final_model)

        # Prediction
        y_pred = network_model.predict(df)
        df['predicted_column'] = y_pred

        # Ensure output directory exists before saving
        os.makedirs('prediction_output', exist_ok=True)
        df.to_csv('prediction_output/output.csv', index=False)

        # Convert to HTML for the frontend
        table_html = df.to_html(classes='table table-striped table-hover', index=False)

        return templates.TemplateResponse(
            "table.html",
            {"request": request, "table": table_html}
        )
        
    except Exception as e:
            raise NetworkSecurityException(e,sys)

    
if __name__=="__main__":
    app_run(app,host="0.0.0.0",port=8000)
