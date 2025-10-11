import logging
import os
from datetime import datetime

class CustomLogger:
    def __init__(self,logs_dir="logs"):
        
        self.logs_dir = os.path.join(os.getcwd(),logs_dir)
        os.makedirs(self.logs_dir, exist_ok=True)
        LOG_FILE = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        LOG_FILE_PATH = os.path.join(self.logs_dir, LOG_FILE)
        
        # create basic configuration for logging
        logging.basicConfig(
            filename=LOG_FILE_PATH,
            format="[%(asctime)s] %(levelname)s %(name)s (line:%(lineno)d) - %(message)s",
            level=logging.INFO,
        )
        #logger = logging.getLogger("Document Portal")
        #logger.info("Logging has started, Logging is set up for CustomerLogger class.")
    
    def get_logger(self,name=__file__):
        return logging.getLogger(os.path.basename(name))

if __name__ == "__main__":
    logger =CustomLogger()
    logger= logger.get_logger(__file__)
    logger.info("This is an info message")
            
    