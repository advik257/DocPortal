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
import pandas as pd

import fitz  # PyMuPDF
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader ,PyPDFLoader,Docx2txtLoader,TextLoader
from langchain_community.vectorstores import FAISS

from utils.model_loader import ModelLoader
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException

from utils.file_io import generate_session_id,save_uploaded_files
from utils.document_ops import load_documents, concat_for_analysis, concat_for_comparison
import utils.document_ops as doc_ops


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

class FaissManager:
  
    
    def __init__(self ,index_dir :Path , model_loader: Optional[ModelLoader] = None):
        self.log = CustomLogger().get_logger(__name__)

        self.index_dir = index_dir
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        self.metapath = self.index_dir / "ingested_meta.json"
        self._meta : Dict[str , Any] = {"rows":{}}
        
        if self.metapath.exists():
            try:
                self._meta = json.load(self.metapath.read_text(encoding='utf-8')) or {"rows":{}}
            except Exception:
                self._meta ={"rows":{}}
                
        self.model_loader = model_loader or ModelLoader()
        self.embedding_model = self.model_loader.load_embeddings()
        self.vector_store: Optional[FAISS] = None

    def _exists(self)->bool:
        return (self.index_dir / "index.faiss").exists() and (self.index_dir / "index.pkl").exists()
    
    @staticmethod
    def _fingerprint(txt:str , md: Dict[str, Any])->str:
        
        src = md.get("source") or md.get("file_path")
        rid =md.get("row_id")
        
        if src is not None:
            return f"{src}::{'' if rid is None else rid}"
        return hashlib.sha256(txt.encode('utf-8')).hexdigest()
        
    
    def _save_metadata(self):
        
        """ persisting your metadata to disk — specifically to the file ingested_meta.json"""
        
        self.metapath.write_text(json.dumps(self._meta, ensure_ascii=False,indent=2), encoding='utf-8')
    
    def add_documents(self, docs : List[Document]):
        """add the documents inside vector database"""
        if self.vector_store is None:
            raise RuntimeError("call load_or_create() before add_documents_idempotent().")
        
        new_docs :List[Document] =[]
        
        for d in docs:
            key = self._fingerprint(d.page_content , d.metadata or {})
            if key in self._meta["rows"]:
                continue
            self._meta["rows"][key]=True
            new_docs.append(d)
            
            if new_docs:
                self.vector_store.add_documents(new_docs)
                self.vector_store.save_local(self.index_dir)
                self._save_metadata()
            return len(new_docs)
            
                
    
    def load_or_create(self, texts: Optional[List[str]]=None, metadatas: Optional[List[dict]]=None):
        """Load existing FAISS index or create new one.
        
        Args:
            texts: Optional list of texts to embed
            metadatas: Optional metadata for each text
            
        Returns:
            FAISS vector store instance
            
        Raises:
            DocumentPortalException: If no index exists and no texts provided
        """
        try:
            # Try loading existing index first
            if self._exists():
                self.vector_store = FAISS.load_local(
                    str(self.index_dir),
                    embeddings=self.embedding_model,
                    allow_dangerous_deserialization=True
                )
                self.log.info("Loaded existing FAISS index", path=str(self.index_dir))
                return self.vector_store

            # Create new index if texts provided
            if not texts:
                raise DocumentPortalException("No existing FAISS index and no data to create one", sys)

            # Create new vector store
            self.vector_store = FAISS.from_texts(
                texts=texts,
                embedding=self.embedding_model,  # Changed from self.emb
                metadatas=metadatas or []
            )
            
            # Save to disk
            self.vector_store.save_local(str(self.index_dir))
            self.log.info("Created new FAISS index", path=str(self.index_dir))
            
            return self.vector_store

        except Exception as e:
            self.log.error("Error in load_or_create", error=str(e))
            raise DocumentPortalException("Failed to load or create FAISS index", sys) from e
   

class DocumentHandler:
    
    """
    PDF save + read (page-wise) for analysis.
    """
    def __init__(self, data_dir: Optional[str] = None, session_id: Optional[str] = None):
        self.log = CustomLogger().get_logger(__name__)
        self.data_dir = data_dir or os.getenv("DATA_STORAGE_PATH", os.path.join(os.getcwd(), "data", "document_analysis"))
        self.session_id = session_id or generate_session_id("session")
        self.session_path = os.path.join(self.data_dir, self.session_id)
        os.makedirs(self.session_path, exist_ok=True)
        self.log.info("DocHandler initialized", session_id=self.session_id, session_path=self.session_path)

    async def save_pdf(self, uploaded_file) -> str:
        try:
            filename = os.path.basename(uploaded_file.name)
            if not filename.lower().endswith(".pdf"):
                raise ValueError("Invalid file type. Only PDFs are allowed.")
            save_path = os.path.join(self.session_path, filename)

           
            buffer = uploaded_file.getbuffer()

            with open(save_path, "wb") as f:
                f.write(buffer)

            self.log.info("PDF saved successfully", file=filename, save_path=save_path, session_id=self.session_id)
            return save_path
        except Exception as e:
            self.log.error("Failed to save PDF", error=str(e), session_id=self.session_id)
            raise DocumentPortalException(f"Failed to save PDF: {str(e)}") 



    def read_pdf(self, pdf_path: str) -> str:
        try:
            self.log = CustomLogger().get_logger(__name__)
            text_chunks = []
            with fitz.open(pdf_path) as doc:
                for page_num in range(doc.page_count):
                    page = doc.load_page(page_num)
                    text_chunks.append(f"\n--- Page {page_num + 1} ---\n{page.get_text()}")  # type: ignore
            text = "\n".join(text_chunks)
            self.log.info("PDF read successfully", pdf_path=pdf_path, session_id=self.session_id, pages=len(text_chunks))
            return text
        except Exception as e:
            self.log.error("Failed to read PDF", error=str(e), pdf_path=pdf_path, session_id=self.session_id)
            raise DocumentPortalException(f"Could not process PDF: {pdf_path}", e)
    

class DocumentComparator:
    
       """Save, read & combine PDFs for comparison with session-based versioning."""
       
       def __init__(self, base_dir: str = "data/document_compare", session_id: Optional[str] = None):
           self.df = pd.DataFrame() 
           self.log = CustomLogger().get_logger(__name__)
           self.base_dir = Path(base_dir)
           self.session_id = session_id or generate_session_id()
           self.session_path = self.base_dir / self.session_id
           self.session_path.mkdir(parents=True, exist_ok=True)
           self.log.info("DocumentComparator initialized", session_path=str(self.session_path))
           
           
       async def save_uploaded_fiels(self,reference_file,actual_file):
           try:
            
                ref_path = self.session_path / reference_file.name
                act_path =  self.session_path / actual_file.name
                
                for fobj , out in ((reference_file,ref_path), (actual_file,act_path)):
                    if not fobj.name.lower().endswith(".pdf"):
                        raise ValueError("Only PDF files are allowed")
                    
                    buffer = fobj.getbuffer()
                    
                    with open(out ,"wb") as f:
                        #if hasattr(fobj,"read"):
                        f.write(buffer)
                        
                self.log.info("Files saved", reference=str(ref_path), actual=str(act_path), session=self.session_id)
                
                return ref_path,act_path
           except Exception as e:
                self.log.error("save_uploaded_fiels", error=str(e), reference=str(ref_path), actual=str(act_path), session=self.session_id)
                raise DocumentPortalException(f"save_uploaded_fiels could not compare :", e)
         
       def read_pdf(self, pdf_path: Path) -> str:
            try:
                with fitz.open(pdf_path) as doc:
                    if doc.is_encrypted:
                        raise ValueError(f"PDF is encrypted: {pdf_path.name}")
                    parts = []
                    for page_num in range(doc.page_count):
                        page = doc.load_page(page_num)
                        text = page.get_text()  # type: ignore
                        if text.strip():
                            parts.append(f"\n --- Page {page_num + 1} --- \n{text}")
                self.log.info("PDF read successfully", file=str(pdf_path), pages=len(parts))
                return "\n".join(parts)
            except Exception as e:
                self.log.error("Error reading PDF", file=str(pdf_path), error=str(e))
                raise DocumentPortalException("Error reading PDF", e) 

       def combine_documents(self) -> str:
            try:
                doc_parts = []
                for file in sorted(self.session_path.iterdir()):
                    if file.is_file() and file.suffix.lower() == ".pdf":
                        content = self.read_pdf(file)
                        doc_parts.append(f"Document: {file.name}\n{content}")
                combined_text = "\n\n".join(doc_parts)
                self.log.info("Documents combined", count=len(doc_parts), session=self.session_id)
                return combined_text
            except Exception as e:
                self.log.error("Error combining documents", error=str(e), session=self.session_id)
                raise DocumentPortalException("Error combining documents", e)

       def clean_old_sessions(self, keep_latest: int = 3):
            try:
                sessions = sorted([f for f in self.base_dir.iterdir() if f.is_dir()], reverse=True)
                for folder in sessions[keep_latest:]:
                    shutil.rmtree(folder, ignore_errors=True)
                    self.log.info("Old session folder deleted", path=str(folder))
            except Exception as e:
                self.log.error("Error cleaning old sessions", error=str(e))
                raise DocumentPortalException("Error cleaning old sessions", e)


class ChatIngestor:
    
    def __init__(self,temp_base: Path=Path("data"),faiss_base:Path  = Path("faiss_index"),use_session_dirs: bool = True,session_id: Optional[str] = None):

        try:
            self.log = CustomLogger().get_logger(__name__)
            self.model_loader = ModelLoader()
            
            self.use_session = use_session_dirs
            self.session_id = session_id or generate_session_id()
            
            self.temp_base = Path(temp_base)
            self.temp_base.mkdir(parents=True , exist_ok=True)
            
            self.faiss_base = Path(faiss_base)
            self.faiss_base.mkdir(parents=True, exist_ok=True)
            


            self.temp_dir = self._resolve_dir(self.temp_base)
            self.faiss_dir = self._resolve_dir(self.faiss_base)
            
            self.log.info("Chat Ingestor intialized : " , session_id= session_id , temp_dir = str(self.temp_dir),faiss_dir = str(self.faiss_dir),sessionized = self.use_session)
            
            
        except Exception as e:
         self.log.error("Error cleaning old sessions", error=str(e))
         raise DocumentPortalException("Error cleaning old sessions", e) 
        
    
    def _resolve_dir(self,base:Optional[Path])->Path:
        print("Resolving base:", base, "type:", type(base))
        if base is None:
            raise ValueError("Base path is None. Check FAISS_BASE initialization.")
        if self.use_session:
            d =base / self.session_id
            d.mkdir(parents=True , exist_ok=True)
            return d
        return base
    
    def _split(self, docs: List[Document], chunk_size=1000, chunk_overlap=200) -> List[Document]:
        self.log = CustomLogger().get_logger(__name__)
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = splitter.split_documents(docs)
        self.log.info("Documents split", chunks=len(chunks), chunk_size=chunk_size, overlap=chunk_overlap)
        return chunks
    
    
    
 


    def built_retriever(self,uploaded_files: Iterable,*,chunk_size: int = 1000,chunk_overlap: int = 200,k: int = 5):
        try:
       
            self.log = CustomLogger().get_logger(__name__)
            paths = save_uploaded_files(uploaded_files, self.temp_dir)
        
    
            docs = doc_ops.load_documents(paths)
            if not docs:
                raise ValueError("No valid documents loaded")
            
            chunks = self._split(docs, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            ## FAISS manager very very important class for the docchat
            fm = FaissManager(self.faiss_dir, self.model_loader)
            
            texts = [c.page_content for c in chunks]
            metas = [c.metadata for c in chunks]
            
            try:
                vs = fm.load_or_create(texts=texts, metadatas=metas)
            except Exception:
                vs = fm.load_or_create(texts=texts, metadatas=metas)
                
            added = fm.add_documents(chunks)
            self.log.info(f"FAISS index updated: added={added}, index={self.faiss_dir}")
            #self.log.info(f"Retriever built successfully: retriever_type=similarity, k={k}")

            #self.log.info("Retriever built successfully", retriever_type="similarity", k=k)

            
            return vs.as_retriever(search_type="similarity", search_kwargs={"k": k})
            
            
            
        except Exception as e:
         self.log.error(f"built_retriever failed: {str(e)}")
         raise DocumentPortalException(f"built_retriever failed: {e}")
    

