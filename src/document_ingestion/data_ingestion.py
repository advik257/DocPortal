from __future__ import annotations
import os
import sys
import uuid
import json
import hashlib
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union,Iterable

import fitz  # PyMuPDF
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader ,PyPDFLoader,Docx2txtLoader,TextLoader
from langchain_community.vectorstores import FAISS

from utils.model_loader import ModelLoader
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException


class FaissManager:
  
    
    def __init__(self):
        pass
    
    def _exists(self):
        pass
    
    @staticmethod
    def _fingerprint(self):
        pass
    
    def _save_metadata(self):
        pass
    
    def add_documents(self):
        pass
    
    def load_or_create(self):
        pass
    
    

class DocumentHandler:
    
    
    def __init__(self):
        pass
    
    def save_pdf(self):
        pass
    
    def read_pdf(self):
        pass
        
    

class DocumentComparator:
    
    def __init__(self):
        pass
    
    def save_uploaded_files(self):
        pass
    
    def read_uploaded_files(self):
        pass
    
    def combine_documents(self):
        pass
    
    def clean_old_session(self):
        pass



class ChatIngestor:
    
    def __init__(self):
        pass
    
    def _resolve_dir(self):
        pass
    
    def _split(self):
        pass
    
    def built_retriever(self):
        pass
    

