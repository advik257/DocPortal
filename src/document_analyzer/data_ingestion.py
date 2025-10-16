import os
import sys
import fitz
import uuid # data versioning
from datetime import datetime

#from langchain.document_loaders import PyPDFLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException

class DocumentHandler:
    
    """Handles PDF saving and reading operations
    Class to handle document ingestion and processing."""
    
    def __init__(self,data_dir=None,session_id=None):
        try:
            self.log=CustomLogger().get_logger(__name__)
            
            self.data_dir = (data_dir or 
                             os.getenv("DATA_STORAGE_PATH") or
                             os.path.join(os.getcwd(),"data","document_analysis"))
            
            self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

            # Create base session directory if it doesn't exist
            self.session_path = os.path.join(self.data_dir, self.session_id)
            os.makedirs(self.session_path, exist_ok=True)
            self.log.info("PDF Handler intialized :",session_id = self.session_id, session_path = self.session_path)
            
        except Exception as e:
            self.log.error("Error initializing DocumentHandler:", error=str(e))
            raise DocumentPortalException("Error initializing DocumentHandler:", e) from e
        
        
    def save_pdf(self,uploaded_file):
        try:
            file_name =os.path.basename(uploaded_file.name)
            
            if not file_name.lower().endswith(".pdf"):
                raise DocumentPortalException("Invalid file type , Only PDF files are supported.", sys)
            
            save_path = os.path.join(self.session_path, file_name)
            
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            self.log.info("PDF saved successfully.", file = file_name ,file_path=save_path,session_id=self.session_id)
            return save_path
        
        except Exception as e:
            self.log.error("Error saving PDF:", error=str(e))
            raise DocumentPortalException("Error saving PDF:", e) from e
    
    def read_pdf(self,pdf_path:str)->str:
        try:
            # text_chunks = []
            # with fitz.open(pdf_path) as doc:
            #     for page_num , page in enumerate(doc, start=1):
            #         text_chunks.append(f"\n --- Page {page_num} ---\n {page.get_text()}")
            #     text = "\n".join(text_chunks)
            #     self.log.info("PDF read successfully.", file=pdf_path, total_pages=len(doc), total_chars=len(text))
            # return text
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=500,chunk_overlap=50 , length_function=len)
            text = text_splitter.split_documents(documents)
            combined_text = "\n".join([doc.page_content for doc in text])
            self.log.info("PDF read and split successfully.", file=pdf_path, total_pages=len(documents), total_chars=len(combined_text), total_chunks=len(text))
            return combined_text
            
        except Exception as e:
            self.log.error("Error reading PDF:", error=str(e))
            raise DocumentPortalException("Error reading PDF:", e) from e
        

if __name__ == "__main__":
    
    from pathlib import Path
    from io import BytesIO
    
    #handler = DocumentHandler()
    pdf_path =r"E:\\LLMProjects\\documentportal\\data\\document_analysis\\sample.pdf"
    
    class Dummy_file:
        def __init__(self, file_path):
            self.name = Path(file_path).name
            self._file_path = file_path
        
        def getbuffer(self):
            return open(self._file_path, 'rb').read()
        
    dummy_pdf = Dummy_file(pdf_path)
    
    handler = DocumentHandler()
    
    try:
        saved_path = handler.save_pdf(dummy_pdf)
        print("PDF saved at:", saved_path)
        
        content = handler.read_pdf(saved_path)
        print("PDF content length:", len(content), content[:500])
        
    except DocumentPortalException as e:
        print("Error:", e)
    
        