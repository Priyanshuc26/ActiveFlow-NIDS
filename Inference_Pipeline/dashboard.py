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
    header {
        visibility: hidden;
        }
    
    /* Removing Extra Space from Main Container */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 2.5rem;
        padding-right: 2.5rem;
    }
</style>
"""

# Injecting the CSS directly into the web DOM
st.markdown(hide_streamlit_style, unsafe_allow_html=True)




#Fetching data from our inference engine through get request
@st.cache_data(ttl=1)         # prevents redundant API calls if Streamlit triggers multiple reruns within the same second.
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


if 'historical_metrics' not in st.session_state:
    st.session_state.historical_metrics = pd.DataFrame()
    
if 'system_health_trend' not in st.session_state:
        st.session_state.system_health_trend = pd.DataFrame()

if "previous_packet_count" not in st.session_state:
    st.session_state.previous_packet_count = None
    st.session_state.previous_packet_arrival_time = None
    
if "previous_throughput" not in st.session_state:
    st.session_state.previous_throughput = 0
    
if "previous_network_health_score" not in st.session_state:
    st.session_state.previous_network_health_score = 0
    
if "previous_alert_df" not in st.session_state:
    st.session_state.previous_alert_df = pd.DataFrame()

@st.fragment(run_every=1)        #st.fragment only rerun the specfic fragment of app, whereas rerun func runs whole app every time(Leading to render whole page every second)
def live_dashboard():
    status, dataframe, packet_processed, attack_count = fetch_data() 
    current_packet_count = packet_processed
    current_packet_arrival_time= datetime.now()

    ## Handling Session State for displaying Time Series Data, as API only sends only sends a buffer of 100 rows. But we need more rows to be stored according to there time thats why we are storing data in session_state that stores the data during whole seesion
    attack_count['timestamp'] = datetime.now()
    st.session_state.historical_metrics = pd.concat([st.session_state.historical_metrics, pd.DataFrame([attack_count])])    #pd.concat strictly requires a single iterable containing the objects to concatenate, thats why we add both dataframe into list
    st.session_state.historical_metrics = st.session_state.historical_metrics.tail(500)    #Storing only last 500 values in session state because sending too many values to browser can lead to crash or freezing


    #Calculating Netwok Security Score
    if packet_processed > 0: 
        network_health_score = float(format((attack_count['benign']/packet_processed)*100,".2f"))
    else:
        network_health_score = 0
        
    ## Checking Security Status of the System
    if status != "connected":
        security_status = ":orange-badge[:material/desktop_access_disabled: Security Status: System not connected to Network]"
    elif status == "connected" and packet_processed == 0:
        security_status = ":gray-badge[:material/desktop_access_disabled: Security Status: Zero Flow Detected]"
    elif network_health_score >= 95:
        security_status = ":green-badge[:material/house_with_shield: Security Status: System is Secured]"
    elif network_health_score >=80 and network_health_score < 95:
        security_status = ":yellow-badge[:material/warning: Security Status: Warning(Elevated Threat Detected)]"
    else:
        security_status = ":red-badge[:material/e911_emergency: Critical(System Under Attack)]"

    # Saving Information for plotting System Health Score Trend over time Graph
    st.session_state.system_health_trend = pd.concat([st.session_state.system_health_trend, pd.DataFrame([{'system_health_score':network_health_score, 'timestamp':datetime.now()}])])    
    st.session_state.system_health_trend = st.session_state.system_health_trend.tail(40)

    ### Dashboard
    with st.container(width="stretch"):
        
        st.title("ActiveFlow NIDS Live Dashboard")
        ## Header
        header_col1, header_col2, header_col3 = st.columns(3,vertical_alignment="center",width='stretch')   
        with header_col1:
            if status == "connected":
                st.markdown(":green-badge[:material/monitor_heart: NIDS Status: Monitoring]")
            else:
                st.markdown(":red-badge[:material/monitor_heart: NIDS Status: Not Monitoring]")
        with header_col2:
            st.markdown(security_status)
        with header_col3:
            st.markdown(f'''**Time:** {datetime.now().strftime("%H:%M:%S")}, {datetime.now().strftime("%d-%m-%Y")}({datetime.now().strftime("%A")})''')
        st.space("small")
             
              
        ## KPI  
        # KPI's First Row
        total_packets_analyzed_col, benign_count_col, malicious_packets_count_col, network_health_score_col, throughput_col= st.columns([1,1,1,1.5,1],border=True)
        
        with total_packets_analyzed_col:
            st.metric(label="Total Packets Analyzed",value=packet_processed)
        with benign_count_col:
            st.metric(label="Benign Packets Count",value=attack_count['benign'])
        with malicious_packets_count_col:
            st.metric(label="Malicious Packets Count", value=packet_processed-attack_count['benign'])
        with network_health_score_col:
            nhs_delta = network_health_score - st.session_state.previous_network_health_score
            st.metric(label="**Network Health Score**",value=f"{network_health_score}%", delta=f'{round(nhs_delta,2)}%')
            st.session_state.previous_network_health_score = network_health_score
        with throughput_col:
            # Throughput Calculation
            if st.session_state.previous_packet_count is None:
                throughput = 0
            else:
                time_diff = (current_packet_arrival_time - st.session_state.previous_packet_arrival_time).total_seconds()
                if time_diff > 0:
                    throughput = (current_packet_count - st.session_state.previous_packet_count) / time_diff
                else:
                    throughput = 0

            if throughput == 0:
                throughput = st.session_state.previous_throughput
            throughput_delta = throughput - st.session_state.previous_throughput
            st.metric(label="Throughput (packets/sec)", value=round(throughput), delta=round(throughput_delta,1))

        # Update previous values
        st.session_state.previous_packet_count = current_packet_count
        st.session_state.previous_packet_arrival_time = current_packet_arrival_time
        st.session_state.previous_throughput = throughput
        

        # KPI's Second Row (Malicious Packets Count)
        with st.container():
            
            malicious_breakdown_col, live_alert_panel_col =st.columns([1,1.5],border=True)
            
            with malicious_breakdown_col:
                st.subheader(body="Malicious Traffic Breakdown", divider="gray",text_alignment="center")
                ddos_count_col,dos_count_col,portscan_count_col = st.columns(3)
                with ddos_count_col:
                    st.metric(label="DDoS",value=attack_count['ddos'], width="content")
                with dos_count_col:
                    st.metric(label="DoS",value=attack_count['dos'], width="content")
                with portscan_count_col:
                    st.metric(label="PortScan",value=attack_count['portscan'], width="content")
              
                brute_force_count_col,web_attack_count_col,bots_count = st.columns(3)
                with brute_force_count_col:
                    st.metric(label="Brute Force",value=attack_count['brute_force'], width="content")
                with web_attack_count_col:
                    st.metric(label="Web Attack",value=attack_count['web_attack'], width="content")
                with bots_count:
                    st.metric(label="Bots",value=attack_count['bots'], width="content")
            
            with live_alert_panel_col:
                st.subheader(body="LIVE ALERT PANEL",divider="gray",text_alignment="center")
                if dataframe.empty:           # Preventing Crash of Dashboard when no flow is occuring(dataframe will be empty)
                    st.markdown("Waiting for traffic...")
                else:
                    alert_df:pd.DataFrame = dataframe[dataframe['prediction'] != 'benign'].reset_index(drop=True)
                    alert_df.sort_values(by='timestamp', ascending=False, inplace=True)
                    alert_df = alert_df.tail(5).loc[:,['prediction','src_addr','dst_addr','timestamp']]
                    if alert_df.shape[0] == 0:
                        alert_df = st.session_state.previous_alert_df
                        
                    st.dataframe(data=alert_df, hide_index=True)
                    st.session_state.previous_alert_df = alert_df
                
            
        st.space("small")
            
        ## Analytical Layer(Visualization)
        line_chart_col, system_health_trend_col = st.columns([1.2,1],border=True)
        with line_chart_col:
            st.subheader(body="Attack Trend Over Time", divider="gray", text_alignment='center')
            st.line_chart(data=st.session_state.historical_metrics, x='timestamp', x_label='Time Stamp', y_label='Volume of Packets',width="stretch")
        with system_health_trend_col:
            st.subheader(body="System Health Trend Over Time", divider="gray", text_alignment='center')
            st.line_chart(data=st.session_state.system_health_trend, x='timestamp', x_label='Time Stamp', y_label='System Health Score(in %)',width="stretch")
        
        
        
        
        st.space("small")
        df_col,map_col = st.columns([1.4,1],border=True)
        with df_col:
            st.subheader(body="Network Logs", divider="gray",text_alignment="center")
            if dataframe.empty:
                    st.markdown("Waiting for traffic...")
            else:
                # Displaying Packets in form of dataframe
                def highlight_threats(row):
                    if str(row['prediction']) != 'benign':
                        style = 'background-color: rgba(220, 38, 38, 0.15); color: #ff4b4b;'
                    else:
                        # benign rows will be transparent/default
                        style = ''
                    
                    # Return the style applied to every column in that specific row
                    return [style] * len(row)
                
                rendered_dataframe = dataframe.tail(20).loc[:,['timestamp','src_addr','dst_addr','dst_port','ip_prot','prediction']]
                styled_dataframe = rendered_dataframe.style.apply(highlight_threats, axis=1)    #Applying Style to rows that contain packets with attack labels
                st.dataframe(data=rendered_dataframe)
        
        with map_col:
            if dataframe.empty:
                    st.markdown("Waiting for traffic...")
            else:
                map_data = dataframe.dropna(subset=['latitude','longitude'])  
                st.map(data=map_data,latitude='latitude',longitude='longitude')
            
            
            

# Call the fragment to initialize the loop
live_dashboard()