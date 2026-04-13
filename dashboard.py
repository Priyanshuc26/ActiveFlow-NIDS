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
        packets_processed = data['total_count']
        data = data['live_traffic']
        df = pd.DataFrame(data)
        return [status,df,packets_processed]
    except:
        status = "offline"
        df = pd.DataFrame()
        return [status,df,0]

status,dataframe,packet_processed = fetch_data()


## Dashboard
header_col1, header_col2 = st.columns([3, 1],vertical_alignment="center")   
total_packets_analyzed,threats_detected, network_health_score = st.columns(3)

with st.container(width=1500):
    
    # Header
    with header_col1:
        st.header("ActiveFlow IDS Live Dashboard")
    with header_col2:
        if status == "connected":
            st.write("")
            st.markdown(":green-badge[:material/monitor_heart: Monitoring]")
        else:
            st.write("")
            st.markdown(":red-badge[:material/monitor_heart: Offline]")
            
    # KPIs
    with total_packets_analyzed:
        st.metric(label="Total Packets Analyzed",value=packet_processed, chart_data=packet_processed, chart_type="line", border=True)
    
            

    
    st.dataframe(data=dataframe)










time.sleep(1)
st.rerun()