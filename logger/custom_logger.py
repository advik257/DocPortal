import logging
import os
from datetime import datetime
import structlog  # structured logging

class CustomLogger:
    def __init__(self,logs_dir="logs"):
        
        # creating logs directory if not exists
        self.logs_dir = os.path.join(os.getcwd(),logs_dir)
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # create log file name with current timestamp
        LOG_FILE = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        self.LOG_FILE_PATH = os.path.join(self.logs_dir, LOG_FILE)
        
    # configure logger both file(JSON) and console
    def get_logger(self,name=__file__):
        
        logger_name = os.path.basename(name)
        
        file_handler = logging.FileHandler(self.LOG_FILE_PATH)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter("%(message)s")) # JSON format
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter("%(message)s"))

    
    # create basic configuration for logging
        logging.basicConfig(
            #filename=self.LOG_FILE_PATH,
            #format="[%(asctime)s] %(levelname)s %(name)s (line:%(lineno)d) - %(message)s",
            level=logging.INFO,
            format=("%(message)s"), #Structlog will handle the formatting
            handlers=[file_handler, console_handler] 
        )
    
    
    # confgure structlog for JSON structured logging
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso",utc=True,key="timestamp"),
                structlog.processors.add_log_level,
                structlog.processors.EventRenamer(to="event"),
                structlog.processors.JSONRenderer()
            ],
            logger_factory = structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True
            
            
        )
            
        return structlog.get_logger(logger_name) 
    

# if __name__ == "__main__":
#     logger=CustomLogger().get_logger(__file__)
#     logger.info("User uploaded a file", user_id=123, filename="report.pdf")
#     logger.error("Failed to process PDF", error="File not found", user_id=123)
                        
    