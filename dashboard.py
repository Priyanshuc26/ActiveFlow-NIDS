import streamlit as st
import pandas as pd
import requests
import sys
import time
from datetime import datetime
import altair as alt

from IDS_Pipeline.exception.exception import CustomException
from IDS_Pipeline.logging.logger import logging

st.set_page_config(page_title='ActiveFlow NIDS', layout='wide')
# Hiding unnecssary buttons
hide_streamlit_style = """
<style>
    /* Hides the Top Header Bar */
    header {visibility: hidden;}
</style>
"""

# Injecting the CSS directly into the web DOM
st.markdown(hide_streamlit_style, unsafe_allow_html=True)




#Fetching data from our inference engine through get request
def fetch_data():
    try: 
        response = requests.get("http://127.0.0.1:8000/metrics")
        system_status = "connected"
        data = response.json()
        packets_processed = data['packets_processed']
        attack_count_dict = data['prediction_count']
        data = data['live_traffic']
        df = pd.DataFrame(data)
        return [system_status, df, packets_processed, attack_count_dict]
    except:
        system_status = "offline"
        df = pd.DataFrame()
        return [system_status, df, 0, {"benign": 0,"dos": 0,"portscan": 0,"ddos": 0,"brute_force": 0,"web_attack": 0,"bots": 0}]

status, dataframe, packet_processed, attack_count = fetch_data() 

## Handling Session State for displaying Time Series Data, as API only sends only sends a buffer of 100 rows. But we need more rows to be stored according to there time thats why were storing data in session_state that stores the data during whole seesion
attack_count['timestamp'] = datetime.now()
if 'historical_metrics' not in st.session_state:
    st.session_state.historical_metrics = pd.DataFrame([attack_count])

st.session_state.historical_metrics = pd.concat([st.session_state.historical_metrics, pd.DataFrame([attack_count])])    #pd.concat strictly requires a single iterable containing the objects to concatenate, thats why we add both dataframe into list
st.session_state.historical_metrics = st.session_state.historical_metrics.tail(500)    #Storing only last 500 values in session state because sending too many values to browser can lead to crash or freezing


#Calculating Netwok Security Score
if packet_processed > 0: 
    network_health_score = float(format((attack_count['benign']/packet_processed)*100,".2f"))
else:
    network_health_score = 0
    
#Checking Security Status of the System
if network_health_score >= 95:
    security_status_symbol = ":green-badge[:material/house_with_shield:]"
elif network_health_score >=80 and network_health_score < 95:
    security_status_symbol = ":yellow-badge[:material/warning:]"
    security_status = "Warning: Elevated Threat Detected" 
else:
    security_status_symbol = ":red-badge[:material/e911_emergency:]"
    security_status = "Critical: System Under Attack"


### Dashboard
with st.container(width="stretch"):
    
    ## Header
    header_col1, header_col2 = st.columns([3, 1],vertical_alignment="center",width='stretch')   
    with header_col1:
        st.header("ActiveFlow NIDS Live Dashboard")
    with header_col2:
        if status == "connected":
            st.write("")
            st.markdown(":green-badge[:material/monitor_heart: System Status: Monitoring]")
        else:
            st.write("")
            st.markdown(":red-badge[:material/monitor_heart: System Status: Offline]")
          
          
    ## KPI  
    # KPI's First Row
    total_packets_analyzed_col, benign_count_col, network_health_score_col, security_status_col = st.columns(4,border=True)
    
    with total_packets_analyzed_col:
        st.metric(label="Total Packets Analyzed",value=packet_processed)
    with benign_count_col:
        st.metric(label="Benign Packets Count",value=attack_count['benign'])
    with network_health_score_col:
        st.metric(label="Network Health Score",value=f"{network_health_score}%")
    with security_status_col:
        st.markdown(security_status_symbol,text_alignment='center',unsafe_allow_html=True)


    # KPI's Second Row (Malicious Packets Count)
    with st.container(border=True, width="stretch"):
        st.subheader("Malicious Packets Count", divider="red", width="stretch", text_alignment="center")
        
        dos_count_col, portscan_count_col, ddos_count_col, brute_force_count_col, web_attack_count_col, bots_count =st.columns(6,border=True)

        with dos_count_col:
            st.metric(label="DoS",value=attack_count['dos'])
        with portscan_count_col:
            st.metric(label="PortScan",value=attack_count['portscan'])
        with ddos_count_col:
            st.metric(label="DDoS",value=attack_count['ddos'])
        with brute_force_count_col:
            st.metric(label="Brute Force",value=attack_count['brute_force'])
        with web_attack_count_col:
            st.metric(label="Web Attack",value=attack_count['web_attack'])
        with bots_count:
            st.metric(label="Bots",value=attack_count['bots'])
        
        
    ## Analytical Layer(Visualization)
    line_chart_col,donut_chart_col = st.columns([1.5,1],border=True)
    with line_chart_col:
        st.line_chart(data=st.session_state.historical_metrics, x='timestamp', x_label='Time Stamp', y_label='Volume of Packets',width="stretch")
    
    with donut_chart_col:
        del attack_count['timestamp']
        attack_count_df = pd.DataFrame({"threat":list(attack_count.keys()), "count":list(attack_count.values())})
        chart = alt.Chart(attack_count_df).mark_arc(innerRadius=60,stroke="#111111",strokeWidth=1).encode(theta='count',color='threat',tooltip=['threat', 'count'])
        st.altair_chart(chart)
        
        
    st.dataframe(data=dataframe)










time.sleep(1)
st.rerun()