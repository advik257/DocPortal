import os
import sys
from langchain_core.output_parsers import StrOutputParser,JsonOutputParser
from langchain.output_parsers import OutputFixingParser

from prompt.prompt_library import PROMPT_REGISTRY
from model.models import *
from utils.model_loader import ModelLoader
from exception.custom_exception_archive import DocumentPortalException
from logger.custom_logger import CustomLogger



class DocumentAnalyzer:
    
    """class to analyze and process document text.
    Analyzes document using pretrained LLM models."""
    
    def __init__(self):
        self.log = CustomLogger().get_logger(__name__)
        try:
            self.modeloader = ModelLoader()
            self.llm = self.modeloader.load_llm()
            
            #prepare output parser
            
            self.parser = JsonOutputParser(pydantic_object= Metadata)
            self.fixing_parser = OutputFixingParser.from_llm(parser = self.parser, llm =self.llm)
            
            self.prompt = PROMPT_REGISTRY["document_analysis"]
            
            self.log.info("DocumentAnalyzer initialized successfully.")
            
            
        except Exception as e:
            self.log.error("Error initializing DocumentAnalyzer:", error=str(e))
            raise DocumentPortalException("Error initializing DocumentAnalyzer:", e) from e
        
    
    def analyze_document(self, document_text: str) -> dict:
        
        """Analyze the document text and return structured metadata."""
        self.log.info("Analyzing document...")
         
        try:
            chain = self.prompt | self.llm | self.fixing_parser
            self.log.info("Meta data analysis chain intilized.")
            
            response = chain.invoke({
                "format_instructions": self.parser.get_format_instructions(),
                "document_text": document_text
            })
            
            self.log.info("Meta data analysis completed successfully.", keys = list(response.keys()))
            return response
                
                 
            
        except Exception as e:
            self.log.error("Error analyzing document:", error=str(e))
            raise DocumentPortalException("Error analyzing document:", e)