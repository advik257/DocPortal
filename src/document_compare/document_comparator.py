import os
import sys
from dotenv import load_dotenv
import pandas as pd
from typing import List, Dict
from pydantic import BaseModel, Field
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException
from model.models import *
from prompt.prompt_library import PROMPT_REGISTRY
from utils.model_loader import ModelLoader
from langchain_core.output_parsers import JsonOutputParser
from langchain.output_parsers import OutputFixingParser

from typing import List, Dict
from pydantic import BaseModel, Field
import json
from langchain.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnablePassthrough

class DocumentComparison(BaseModel):
    """Model for document comparison results"""
    title: str = Field(description="Title of the comparison")
    
    #- A list of strings describing what’s the same in both documents 
    similarities: List[str] = Field(description="List of similarities between documents")
    
    #A list of strings describing what’s different
    differences: List[str] = Field(description="List of differences between documents")
    
    #- Summaries of each document — could include key fields like date, customer name, total, etc.
    document1_summary: List[str] = Field(description="Summary of first document")
    document2_summary: List[str] = Field(description="Summary of second document")
    
    #A dictionary showing what’s unique in each document.
    unique_information: Dict[str, List[str]] = Field(description="Unique information in each document")

class DocumentComparatorLLM:
    
    def __init__(self):
        load_dotenv()
        self.log = CustomLogger().get_logger(__name__)
        self.loader = ModelLoader()
        self.llm = self.loader.load_llm()
        self.output_parser = PydanticOutputParser(pydantic_object=DocumentComparison)
        self.prompt = PROMPT_REGISTRY.get("document_comparison")
        
        if self.prompt is None:
            raise ValueError("Document comparison prompt not found in registry")
        
        self.log.info("DocumentComparatorLLM initialized with model and parser")
    
    def compare_documents(self, combined_docs) -> pd.DataFrame:
        """Compare the two Documents and return a structured response"""
        try:
            # Prepare the inputs
            inputs = {
                "combined_documents": combined_docs,
                "format_instructions": self.output_parser.get_format_instructions()
            }
            
            self.log.info("Starting document comparison")
            
            # Get raw response from LLM
            messages = self.prompt.format_messages(**inputs)
            raw_response = self.llm.invoke(messages)
            
            # Try to parse the response
            try:
                # First try to parse as JSON
                json_str = raw_response.content
                json_obj = json.loads(json_str)
                
                # Then parse into Pydantic model
                comparison_result = DocumentComparison.model_validate(json_obj)
                
                self.log.info("Successfully parsed comparison result")
                return self._format_response(comparison_result)
                
            except json.JSONDecodeError as e:
                self.log.error(f"Failed to parse LLM response as JSON: {str(e)}")
                self.log.error(f"Raw response: {raw_response.content}")
                raise
            except Exception as e:
                self.log.error(f"Failed to parse comparison result: {str(e)}")
                raise
            
        except Exception as e:
            self.log.error(f"Error while comparing documents: {str(e)}")
            raise DocumentPortalException("An error occurred while comparing the documents", sys)
    
    def _format_response(self, comparison_result: DocumentComparison) -> pd.DataFrame:
        """Format the comparison result into a DataFrame"""
        try:
            records = []
            
            if comparison_result.title:
                records.append({
                    "Category": "Title",
                    "Description": comparison_result.title
                })
            
            # Add similarities
            for item in comparison_result.similarities:
                records.append({
                    "Category": "Similarities",
                    "Description": item
                })
            
            # Add differences
            for item in comparison_result.differences:
                records.append({
                    "Category": "Differences",
                    "Description": item
                })
            
            # Add document summaries
            for i, summary in enumerate(comparison_result.document1_summary, 1):
                records.append({
                    "Category": "Document 1 Summary",
                    "Description": f"{i}. {summary}"
                })
            
            for i, summary in enumerate(comparison_result.document2_summary, 1):
                records.append({
                    "Category": "Document 2 Summary",
                    "Description": f"{i}. {summary}"
                })
            
            # Add unique information
            for doc, items in comparison_result.unique_information.items():
                for item in items:
                    records.append({
                        "Category": f"Unique to {doc}",
                        "Description": item
                    })
            
            df = pd.DataFrame(records)
            self.log.info("Response formatted into DataFrame", row_count=len(df))
            return df
            
        except Exception as e:
            self.log.error(f"Error formatting comparison response: {str(e)}")
            raise DocumentPortalException("Error formatting comparison response", sys)