import argparse
import os
import sys
from pyflowmeter.sniffer import create_sniffer

from IDS_Pipeline.exception.exception import CustomException
from IDS_Pipeline.logging.logger import logging


class NetworkTrafficEngine:
    def __init__(self):
        pass
    
    def process_pcap_file(self, pcap_file_path:str, pcap_csv_file_path:str):
        try:
            #Converting pcap file to csv file
            sniffer = create_sniffer(
            input_file= pcap_file_path,
            to_csv=True,
            output_file= pcap_csv_file_path,
            )
            
            sniffer.start()   #Starts the sniffing process
            # pyflowmeter  uses multithreading. When we type sniffer.start(), Python doesn't run the sniffer on the main timeline. It creates a completely separate, invisible background worker to do the heavy packet sniffing.
            
            try:
                sniffer.join()   #This method is very important, if we remove it, pyflowmeter starts sniffing in background, but python works in main script. The main script instantly moves to the next line. There is no next line. The main script shuts down the entire program, instantly terminating the background worker before it even has the chance to look at the very first network packet. CSV file will be 0 bytes.
                # .join() tells main Python script to stop its 'stoping process' and don't exit the program. Python wait until the background worker explicitly tells you it is 100% finished."
                
            except KeyboardInterrupt:
                print('Stopping the sniffer')
                sniffer.stop()
            finally:
                sniffer.join()   #Stops the sniffing and safely closes the output file if any
                
        except Exception as e:
            raise CustomException(e,sys)

    def process_live_sniffing(self):
        try:
            pass
        except Exception as e:
            raise CustomException(e,sys)


if __name__ == "__main __":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--pcap", help="Flag used when pcap file is needed for real life simulation. Include file pcap file path")
        parser.add_argument("--live", action='store_true', help="Flag is used when need to sniff real time packets from network")  #Live value will be only true if it is mentioned in CLI

        args = parser.parse_args()
        print(args)
        if (args.pcap and args.live == True):
            raise Exception("Two arguments added. Please add only one")
        
    except Exception as e:
        raise CustomException(e,sys)