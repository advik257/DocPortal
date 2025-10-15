import os
import sys
from langchain_core.output_parsers import StrOutputParser,JsonOutputParser
from langchain.output_parsers import OutputFixingParser

from prompt.prompt_library import *
from model.models import *
from utils.model_loader import ModelLoader
from exception.custom_exception import DocumentPortalException
from logger.custom_logger import CustomLogger



class DocumentAnalyzer:
    
    """class to analyze and process document text.
    Analyzes document using pretrained LLM models."""
    
    def __init__(self):
        self.log = CustomLogger().get_logger(__name__)
        try:
            self.moderloader = ModelLoader()
            self.loader = self.modeloader.load_llm()
            
            #prepare output parser
            
            self.parser = JsonOutputParser(pydantic_object= Metadata)
            self.fixing_parser = OutputFixingParser.from_llm(parser = self.loader, llm =self.parser)
            
            self.prompt = prompt
            
            self.log.info("DocumentAnalyzer initialized successfully.")
            
            
        except Exception as e:
            self.log.error("Error initializing DocumentAnalyzer:", error=str(e))
            raise DocumentPortalException("Error initializing DocumentAnalyzer:", e) from e
        
    
    def analyze_document(self):
        pass
    