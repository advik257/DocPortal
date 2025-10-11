import sys
import os
import traceback


from logger.custom_logger import CustomLogger
logger = CustomLogger().get_logger(__file__)

class DocumentPortalException(Exception):
    
    def __init__(self, error_message, error_detail:sys):
          _,_,exc_tb=error_detail.exc_info()
          self.filename = exc_tb.tb_frame.f_code.co_filename
          self.lineno = exc_tb.tb_lineno
          self.error_message=str(error_message)
          self.traceback_str = ''.join(traceback.format_exception(*error_detail.exc_info()))
      
        
    def __str__(self):
        return f"""
               Error occurred in script: [{self.filename}]
               at line number: [{self.lineno}]
               with message: {self.error_message}\nTraceback:\n{self.traceback_str}
               Traceback: {self.traceback_str}"""
    

if __name__ == "__main__":
    try:
        a = 1 / 0
    except Exception as e:
        appexc=DocumentPortalException(e,sys)
        logger.error(str(appexc))
        raise appexc