import os
import sys
import uuid
from pathlib import Path
from datetime import datetime

from utils.model_loader import  ModelLoader
from logger.custom_logger import CustomLogger
from exception.custom_exception_archive import DocumentPortalException
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import Docx2txtLoader
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

class DocumentIngestor:
    
    SUPPORTED_FILE_TYPES = {".pdf", ".docx", ".txt",".md"}
      
          
    
    def __init__(self, temp_dir :str = "data/multi_doc_chat", faiss_dir :str = "faiss_index", retriever =None, session_id:str | None =None):
        
        try:
            self.log = CustomLogger().get_logger(__name__)
            
            self.temp_dir = Path(temp_dir)
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            
            self.faiss_dir = Path(faiss_dir)
            self.faiss_dir.mkdir(parents=True, exist_ok=True)
            
            self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            self.session_temp_dir = self.temp_dir / self.session_id
            self.session_temp_dir.mkdir(parents=True, exist_ok=True)
            
            self.session_faiss_dir = self.faiss_dir / self.session_id
            self.session_faiss_dir.mkdir(parents=True, exist_ok=True)
            
            self.model_loader = ModelLoader()
            self.log.info("Document_ingestor initialized successfully." ,temp_dir=str(self.temp_dir), faiss_dir=str(self.faiss_dir), session_id=self.session_id,session_temp_dir=str(self.session_temp_dir),session_faiss_dir=str(self.session_faiss_dir))
            
        except Exception as e:
            self.log.error("Error initializing Multi doc ConversationalRAG:", error=str(e))
            raise DocumentPortalException("Failed to initialize ConversationalRAG", sys)
    
    def ingest_file(self , uploaded_files):
        try:
            documents =[]
            
            for uploaded_file in uploaded_files:
                ext =Path(uploaded_file.name).suffix.lower()
                
                if ext not in self.SUPPORTED_FILE_TYPES:
                    self.log.warning("Unsupported file type. Skipping file.", file_name=uploaded_file.name, file_extension=ext)
                    continue
                unique_filename =f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
                temp_file_path = self.session_temp_dir / unique_filename
                
                with open(temp_file_path, "wb") as f_out:
                    f_out.write(uploaded_file.read())
                    self.log.info("File saved successfully.", file_path=str(temp_file_path))
                
                if ext == ".pdf":
                    
                    loader= PyPDFLoader(str(temp_file_path))
                    
                elif ext in {".txt", ".md"}:
                    
                    loader = TextLoader(str(temp_file_path),encoding="utf-8")
                    
                elif ext == ".docx":
                    
                    loader = Docx2txtLoader(str(temp_file_path))
                else:
                    self.log.warning("No loader available for this file type. Skipping file.", file_name=uploaded_file.name, file_extension=ext)
                    continue
                
                
                docs = loader.load()
                documents.extend(docs)
                self.log.info("File loaded and processed successfully.", file_path=str(temp_file_path))
                
                if not documents:
                    self.log.warning("No valid documents were ingested from the uploaded files.")
                    raise DocumentPortalException("No valid documents ingested", sys)
                
                return self._create_retriever(documents)
            
        except Exception as e:
            self.log.error("Error ingesting files:", error=str(e))
            raise DocumentPortalException("Failed to ingest files", sys)
    
    def _create_retriever(self, documents):
        
        try:
            
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            docs = splitter.split_documents(documents)
            self.log.info("Documents split into chunks successfully.", num_chunks=len(docs))
            
            embedding_model = self.model_loader.load_embeddings()
            vector_store = FAISS.from_documents(documents=docs, embedding=embedding_model)
            
            vector_store.save_local(str(self.session_faiss_dir))
            self.log.info("FAISS vector/ index store created and saved successfully.", faiss_dir=str(self.session_faiss_dir))
            
            retriever  = vector_store.as_retriever(search_type="similarity", search_kwargs={"k":5})
            
            self.log.info("Retriever created successfully." , retriever_type= type(retriever).__name__)
            return retriever
        
        except Exception as e:
            self.log.error("Error creating retriever:", error=str(e))
            raise DocumentPortalException("Failed to create retriever", sys)