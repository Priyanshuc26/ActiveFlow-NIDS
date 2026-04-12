import streamlit as st
import pandas as pd
import requests
import sys
import time

from IDS_Pipeline.exception.exception import CustomException
from IDS_Pipeline.logging.logger import logging


#Fetching data from our inference engine through get request
def fetch_data():
    try: 
        response = requests.get("http://127.0.0.1:8000/metrics")
        status = "connected"
        data = response.json()
        data = data['live_traffic']
        df = pd.DataFrame(data)
        return status,df
    except:
        status = "offline"
        df = pd.DataFrame()
        return status, df

status,dataframe = fetch_data()


## Dashboard
total_packets_analyzed,threats_detected, network_health_score = st.columns(3)

with st.container(width=1500):
    
    header_col1, header_col2 = st.columns([3, 1],vertical_alignment="center")   
    with header_col1:
        st.header("ActiveFlow IDS Live Dashboard")
    with header_col2:
        if status == "connected":
            st.write("")
            st.markdown(":green-badge[:material/monitor_heart: Monitoring]")
        else:
            st.write("")
            st.markdown(":red-badge[:material/monitor_heart: Offline]")

    if status == "connected":
        st.dataframe(data=dataframe)










time.sleep(1)
st.rerun()