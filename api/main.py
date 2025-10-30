from fastapi import FastAPI, UploadFile,File,Form,HTTPException, Request
from fastapi.responses import JSONResponse , HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from typing import List , Optional, Dict, Any
from pathlib import Path


app = FastAPI(title="Document Portal API" , version="0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# base_dir = Path(__file__).parent
# static_dir = base_dir / "static"
# templates_dir = base_dir / "templates"
    
static_path = os.path.join(os.path.dirname(__file__), "..", "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")
template_path = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=template_path)

@app.get("/", response_class=HTMLResponse)
async def serve_ui(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "ok" ,"service": "Document-Portal"}

@app.post("/analyze/")
async def analyze_document(file: UploadFile= File(...)) -> Any:
    try:
        pass
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed - {str(e)}")
    
@app.post("/compare")
async def compare_documents(reference: UploadFile = File(...) , actual :UploadFile = File(...)) -> Any:
    try:
        pass
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed - {str(e)}")
    
@app.post("/chat/index")
async def chat_build_index() -> Any:
    try:
        pass
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed - {str(e)}")
    
@app.post("/chat/query")
async def chat_query() -> Any:
    try:
        pass
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed - {str(e)}")