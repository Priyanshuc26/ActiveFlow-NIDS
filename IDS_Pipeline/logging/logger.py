import logging
import os
import datetime

LOG_FILE = f"{datetime.datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"

# Fix 1: Stop at the "logs" folder. Do not include the filename yet.
logs_path = os.path.join(os.getcwd(), "logs")

# This now creates just the ".../logs" directory
os.makedirs(logs_path, exist_ok=True)

# Fix 2: Now join the folder path with the filename
LOG_FILE_PATH = os.path.join(logs_path, LOG_FILE)

logging.basicConfig(
    filename=LOG_FILE_PATH,
    # Fix 3: Corrected "message" (singular) and removed space in "(name)"
    format="[ %(asctime)s ] %(lineno)d %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
