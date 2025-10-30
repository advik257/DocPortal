import uuid
from pathlib import Path
import os
import sys
import uuid # data versioning
from datetime import datetime


from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from logger.custom_logger import CustomLogger
from exception.custom_exception_archive import DocumentPortalException
from model.models import *
from utils.model_loader import  ModelLoader


class SingleDocIngestion:
    
    """Class to handle single document ingestion, processing, and vector store creation."""
    
    def __init__(self, data_dir :str = "data/single_doc_chat", faiss_dir :str = "faiss_index"):
        try:
            self.log = CustomLogger().get_logger(__name__)
            self.data_dir = Path(data_dir)
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
            self.faiss_dir = Path(faiss_dir)
            self.faiss_dir.mkdir(parents=True, exist_ok=True)
            
            self.model_loader = ModelLoader()
            
            self.log.info("SingleDocIngestion initialized successfully." , temp_dir=str(self.data_dir), faiss_dir=str(self.faiss_dir))
        
        except Exception as e:
            self.log.error("Error initializing SingleDocIngestion:", error=str(e))
            raise DocumentPortalException("Failed to initialize SingleDocIngestion", sys)
        
    def ingest_files(self,uploaded_files):
        
        """Ingest and process files from the input directory and create vector stores."""
        try:
            documents =[]
            
            for uploaded_file in uploaded_files:
                unique_filename =f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.pdf"
                self.log.info("Processing uploaded file.", original_filename=uploaded_file.name, unique_filename=unique_filename)
                
                temp_file_path = self.data_dir / unique_filename
                
                with open(temp_file_path, "wb") as f_out:
                    f_out.write(uploaded_file.read())
                    self.log.info("File saved successfully.", file_path=str(temp_file_path))
                    
                
                
                loader= PyPDFLoader(str(temp_file_path))
                docs = loader.load()
                documents.extend(docs)
                self.log.info("File loaded and processed successfully.", file_path=str(temp_file_path), num_pages=len(docs))
                
            return self._create_retriever(documents)
                
        except Exception as e:
            self.log.error("Error ingesting files:", error=str(e))
            raise DocumentPortalException("Failed to ingest files", sys)
        
        
    def _create_retriever(self , documents):
        """Create a retriever from the processed documents."""
        try:
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            docs = splitter.split_documents(documents)
            self.log.info("Documents split into chunks successfully.", num_chunks=len(docs))
            
            embedding_model = self.model_loader.load_embeddings()
            vector_store = FAISS.from_documents(documents=docs, embedding=embedding_model)
            
            # Save the FAISS index
            vector_store.save_local(str(self.faiss_dir))
            self.log.info("FAISS vector store created and saved successfully.", faiss_dir=str(self.faiss_dir))
            
            retriever  = vector_store.as_retriever(search_type="similarity", search_kwargs={"k":5})
            self.log.info("Retriever created successfully." , retriever_type= type(retriever).__name__)
            
            return retriever
            
        except Exception as e:
            self.log.error("Error creating retriever:", error=str(e))
            raise DocumentPortalException("Failed to create retriever", sys)