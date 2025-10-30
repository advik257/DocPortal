import sys
from pathlib import Path
import fitz
import uuid # data versioning
from datetime import datetime
import os

from logger.custom_logger import CustomLogger
from exception.custom_exception_archive import DocumentPortalException
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DOcumentIngestion:
    
    def __init__(self,base_dir:str="data/document_compare", session_id=None):
        
        try:
            self.log = CustomLogger().get_logger(__name__)
            self.base_dir = Path(base_dir)
            
            self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
           # self.session_path = os.path.join(self.base_dir, self.session_id)
            self.session_path = self.base_dir / self.session_id
            self.session_path.mkdir(parents=True, exist_ok=True)
            
            self.log.info("PDF Handler intialized :",session_id = self.session_id, session_path = str(self.session_path))
           # self.session_path.(parents=True , exist_ok=True)
            
           
        except Exception as e:
            self.log.error("Error initializing DocumentHandler:", error=str(e))
            raise DocumentPortalException("Error initializing DocumentHandler:", e) from e
            
    
    def delete_existing_files(self):
        """Delete existing files in the upload directory."""
        try:
            if self.base_dir.exists() and self.base_dir.is_dir():
                for file in self.base_dir.iterdir():
                    if file.is_file():
                        file.unlink()
                        self.log.info("File deleted " , Path = str(file))
                self.log.info("Directory cleaned ", directory = str(self.base_dir))
            
        except Exception as e:
            self.log.error(f"Error deleting the existing files : {e}")
            raise DocumentPortalException("An Error occured while deleting the existing files. ", sys)
        
    
    def save_uploaded_file(self, reference_file , actual_file):
        """Save the uploaded file to the upload directory."""
        try:
           # self.delete_existing_files()
            #self.log.info("Exisitng files deleted Successfully")
            
            ref_path= self.session_path / reference_file.name  #updated file
            actual_path=self.session_path / actual_file.name
            
            if not reference_file.name.endswith(".pdf") or not actual_file.name.endswith(".pdf"):
                raise ValueError("Only PDF's are allowed")
            
            with open(ref_path ,'wb') as f:
                f.write(reference_file.get_buffer())
                
            with open(actual_path,'wb') as f:
                f.write(actual_file.get_buffer())
                
            self.log.info("Files Saved " ,reference = str(ref_path) , actual = str(actual_path))
            
            return ref_path , actual_path
            
            
        except Exception as e:
            self.log.error(f"Error saving uploaded files :{e}")
            raise DocumentPortalException("An Error occured while saving uploaded files. ", sys)
    
    def read_pdf(self,pdf_path:Path)->str:
        """Read and extract text from a PDF file."""
        try:
            
            # with fitz.open(self, pdf_path) as doc:
            #     if doc.is_encrypted:
            #         raise ValueError(f"PDF is encrypted : {pdf_path.name}")
            #     all_text =[]
            #     for page_num in range(doc.page_count):
            #         page= doc.load_page(page_num)
            #         text = page.get_text()
                    
            #         if text.strip():
            #             all_text.append(f"\n ---- page {page.num+1}.....\n {text}")     
            #     self.log.info("PDF Read Successfully " , file =str(pdf_path),pages= len(all_text))
            #     return "\n".join(all_text)
                all_text =[]
                loader = PyPDFLoader(str(pdf_path))
                documents = loader.load()
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=500,chunk_overlap=50 , length_function=len)
                text = text_splitter.split_documents(documents)
                all_text = "\n".join([doc.page_content for doc in text])
                self.log.info("PDF read and split successfully.", file=pdf_path, total_pages=len(documents), total_chars=len(all_text), total_chunks=len(text))
                return all_text
            
        except Exception as e:
            self.log.error(f"Error reading PDF :{e}")
            raise DocumentPortalException("An Error occured while reading the PDF.",sys)
    
    
    def combined_documents(self) -> str:
        
        """Combine the content of all PDF files in the directory."""
        try:
            doc_parts = []
            content_dict = {}
            
            # Read each PDF file only once
            for file_path in sorted(self.base_dir.iterdir()):
                if file_path.suffix.lower() == ".pdf":
                    content_dict[file_path.name] = self.read_pdf(file_path)
                    
            # Build the combined document text
            for filename, content in content_dict.items():
                doc_parts.append(f"Document: {filename}\n{content}")
                
            combined_text = "\n\n".join(doc_parts)
            self.log.info("Documents combined successfully", 
                            file_count=len(content_dict),
                            total_parts=len(doc_parts))
                    
            return combined_text 
            
        except Exception as e:
            self.log.error(f"Error in Combined Documents: {e}")
            raise DocumentPortalException("Error in combining documents", sys)


    def clean_old_sessions(self , keep_latest:int=3):
        """options to clean old sessions based on timestamp or criteria."""
        try:
            session_folders = sorted(
                [f for f in self.base_dir.iterdir() if f.is_dir()], 
                reverse=True
                )
            
            for folder in session_folders[keep_latest:]:  # Keep the latest 3 sessions
                for item in folder.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        os.rmdir(item)
                folder.rmdir()
                self.log.info("Old session cleaned", session_folder=str(folder))
            
        except Exception as e:
            self.log.error(f"Error cleaning old sessions: {e}")
            raise DocumentPortalException("Error cleaning old sessions", sys)  
        
             