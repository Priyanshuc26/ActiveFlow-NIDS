import os
import sys
import subprocess
import multiprocessing

from IDS_Pipeline.exception.exception import CustomException
from IDS_Pipeline.logging.logger import logging

from IDS_Pipeline.constant.training_pipeline import CONNECTION_NAME


#Popen runs in background
# packet_extractor = subprocess.Popen([
# "tcpdump",
# "-v",
# "-i", CONNECTION_NAME,       # -i:interface from where packets will be captured
# "-w", "traffic_engine/pcap_buffer/chunk_%03d.pcap",     # -w: writes packet to the file path
# "-G", "20",         # -G: for how much time will it capture the packet(rotate seconds)
# "-W", "5"           # -W: Writes hte specified number of files
# ])   
# subprocess directly run shell command, unlike terminal which is visual element connected to shell
# While terminal has its own tokenizer that convert command into tokens, subprocess don't have one, that why we split it in tokens manually


run_lycostand = subprocess.run(["./lycostand", "-i", "./pcap/", "-o", "./pcap_lycos/"], cwd="lycostand")