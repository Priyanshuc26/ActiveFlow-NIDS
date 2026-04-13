import argparse
import os
import sys
from pyflowmeter.sniffer import create_sniffer

from IDS_Pipeline.exception.exception import CustomException
from IDS_Pipeline.logging.logger import logging

from IDS_Pipeline.constant.training_pipeline import  CONNECTION_NAME


class NetworkTrafficEngine:
    def __init__(self):
        pass
    
    def process_pcap_file(self, pcap_file_path:str):
        # python traffic_engine.py --pcap pcap_file_path/name
        try:
            #Converting pcap file to csv file
            sniffer = create_sniffer(
            input_file= pcap_file_path,
            server_endpoint = "http://192.168.29.83:8000/predict"
            )
            
            sniffer.start()   #Starts the sniffing process
            # pyflowmeter  uses multithreading. When we type sniffer.start(), Python doesn't run the sniffer on the main timeline. It creates a completely separate, invisible background worker to do the heavy packet sniffing.
            
            try:
                sniffer.join()   #This method is very important, if we remove it, pyflowmeter starts sniffing in background, but python works in main script. The main script instantly moves to the next line. There is no next line. The main script shuts down the entire program, instantly terminating the background worker before it even has the chance to look at the very first network packet. CSV file will be 0 bytes.
                # .join() tells main Python script to stop its 'stoping process' and don't exit the program. Python wait until the background worker explicitly tells you it is 100% finished."
                
            except KeyboardInterrupt:
                print('Stopping the sniffer')
                sniffer.stop()      #Stops the sniffing and safely closes the output file if any
            finally:
                sniffer.join() 
                
        except Exception as e:
            raise CustomException(e,sys)

    def process_live_sniffing(self, network_input_interface:str):
        try:
            live_sniffer = create_sniffer(
                input_interface= network_input_interface,
                server_endpoint = "http://192.168.29.83:8000/predict"
            )
            live_sniffer.start()
            
            try:
                live_sniffer.join()
                
            except KeyboardInterrupt:
                print("Stopping live sniffing....")
                live_sniffer.stop()
                
            finally:
                live_sniffer.join()
            
            
        except Exception as e:
            raise CustomException(e,sys)


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--pcap", help="Flag used when pcap file is needed for real life simulation. Include file pcap file path")
        parser.add_argument("--live", action='store_true', help="Flag is used when need to sniff real time packets from network")  #Live value will be only true if it is mentioned in CLI

        args = parser.parse_args()
        print(args)
        if (args.pcap and args.live == True):
            raise Exception("Two arguments added. Please add only one")
        
        traffic_engine = NetworkTrafficEngine()
        
        if args.pcap:
            traffic_engine.process_pcap_file(pcap_file_path=args.pcap)
        if args.live:
            traffic_engine.process_live_sniffing(network_input_interface=CONNECTION_NAME)
        
    except Exception as e:
        raise CustomException(e,sys)
    
    
    

# "I discovered a train-serve skew between CICFlowMeter-generated training data and PyFlowMeter live inference data, which is a known open problem in network IDS research. Investigating this is planned for v2.1.0."