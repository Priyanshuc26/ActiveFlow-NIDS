import argparse
import os
import sys
import pyflowmeter


from IDS_Pipeline.exception.exception import CustomException
from IDS_Pipeline.logging.logger import logging


class NetworkTrafficEngine:
    def __init__(self):
        pass
    
    def process_pcap_file(self, file_path:str):
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