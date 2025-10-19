import sys
from pathlib import Path
import fitz

from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DOcumentIngestion:
    
    def __init__(self,base_dir:str="data\\document_compare"):
        
        self.log = CustomLogger().get_logger(__name__)
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True , exist_ok=True)
    
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
            
            ref_path= self.base_dir/reference_file.name  #updated file
            actual_path=self.base_dir/actual_file.name
            
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
    
        
             