from fastapi import FastAPI, UploadFile,File,Form,HTTPException, Request
from fastapi.responses import JSONResponse , HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from typing import List , Optional, Dict, Any
from pathlib import Path

from src.document_ingestion.data_ingestion import DocumentHandler,DocumentComparator,ChatIngestor
from utils.document_ops import FastAPIFileAdapter,read_pdf_via_handler


from langchain_community.vectorstores import FAISS
from src.document_analyzer.data_analysis import DocumentAnalyzer
from src.document_chat.retrieval import ConversationalRAG
from src.document_compare.document_comparator import DocumentComparatorLLM

FAISS_BASE = os.getenv("FAISS_BASE", "faiss_index")
UPLOAD_BASE = os.getenv("UPLOAD_BASE", "data")
FAISS_INDEX_NAME = os.getenv("FAISS_INDEX_NAME", "index") 

app = FastAPI(title="Document Portal API" , version="0.1")

static_path = os.path.join(os.path.dirname(__file__), "..", "static")
template_path = os.path.join(os.path.dirname(__file__), "..", "templates")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

    

app.mount("/static", StaticFiles(directory=static_path), name="static")

templates = Jinja2Templates(directory=template_path)

#---------displaying HTML page -----------------------------------

@app.get("/", response_class=HTMLResponse)
async def serve_ui(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

#-----------Health check---------------------------------------------
@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "ok" ,"service": "Document-Portal"}
        
# ----------------------Document Analysis------------------------------------------
@app.post("/analyze/")
async def analyze_document(file: UploadFile= File(...)) -> Any:
    try:
        dh = DocumentHandler()
        save_path = await dh.save_pdf(FastAPIFileAdapter(file))
        text = read_pdf_via_handler(dh, save_path)
        
        analyzer = DocumentAnalyzer()
        result=analyzer.analyze_document(text)
        return JSONResponse(content=result)
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed - {str(e)}")
    
    
# ---------------------Document Compare ----------------------------------------------------------------
@app.post("/compare")
async def compare_documents(reference: UploadFile = File(...) , actual :UploadFile = File(...)) -> Any:
    try:
        dc = DocumentComparator()
        ref_path , actpath = await dc.save_uploaded_fiels(FastAPIFileAdapter(reference),FastAPIFileAdapter(actual))
        _ = ref_path , actpath
        combined_text = dc.combine_documents()
        comp = DocumentComparatorLLM()
        df = comp.compare_documents(combined_text) 
        
        return {"rows": df.to_dict(orient="records"), "session_id": dc.session_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed - {str(e)}")

#------------------------create Document Index ---------------------------------------------------------

@app.post("/chat/index")
async def chat_build_index( files: List[UploadFile] = File(...),
    session_id: Optional[str] = Form(None),
    use_session_dirs: bool = Form(True),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200),
    k: int = Form(5),
    ) -> Any:
    try:
            wrapped = [FastAPIFileAdapter(f) for f in files]
            # this is my main class for storing a data into VDB
            # created a object of ChatIngestor
            ci = ChatIngestor(
                temp_base=UPLOAD_BASE,
                faiss_base=FAISS_BASE,
                use_session_dirs=use_session_dirs,
                session_id=session_id or None,
            )
            # NOTE: ensure your ChatIngestor saves with index_name="index" or FAISS_INDEX_NAME
            # e.g., if it calls FAISS.save_local(dir, index_name=FAISS_INDEX_NAME)
            # if your method name is actually build_retriever, fix it there as well
            ci.built_retriever( wrapped, chunk_size=chunk_size, chunk_overlap=chunk_overlap, k=k)
            
            return {"session_id": ci.session_id, "k": k, "use_session_dirs": use_session_dirs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed - {str(e)}")
    
    
# --------------------Document Chat ---------------------------------------------------------------
    
@app.post("/chat/query")
async def chat_query( question: str = Form(...),
    session_id: Optional[str] = Form(None),
    use_session_dirs: bool = Form(True),
    k: int = Form(5),
    ) -> Any:
    try:
        
        if use_session_dirs and not session_id:
            raise HTTPException(status_code=400, detail="session_id is required when use_session_dirs=True")

        index_dir = os.path.join(FAISS_BASE, session_id) if use_session_dirs else FAISS_BASE  # type: ignore
        if not os.path.isdir(index_dir):
            raise HTTPException(status_code=404, detail=f"FAISS index not found at: {index_dir}")
        
         # ✅ Load retriever first using a static method or helper
        retriever = ConversationalRAG.load_retriever_from_faiss(index_dir)

        # ✅ Now initialize ConversationalRAG with a valid retriever
        rag = ConversationalRAG(session_id=session_id, retriever=retriever)

        # ✅ Invoke the RAG chain
        response = rag.invoke(question, chat_history=[])

        return {
            "answer": response,
            "session_id": session_id,
            "k": k,
            "engine": "LCEL-RAG"
        }


    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed - {str(e)}")
    
    
    
#uvicorn main:app --reload
#uvicorn main:app --host 0.0.0.0 --port 8080 --reload
#uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload
#http://127.0.0.1:8080/
#http://localhost:8080/
