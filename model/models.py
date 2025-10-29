from pydantic import BaseModel, Field, RootModel
from typing import Optional, List, Dict, Any , Union
from enum import Enum

class Metadata(BaseModel):
    Summary: List[str] = Field(default_factory=list, description="List of summary points about the document.")
    Title: str
    Author: str
    DateCreated: str
    LastModifiedDate: str
    Publisher :str
    Language: str
    Pagecount: Union[int, str]
    Senttimetone: str
    
class ChangeFormat(BaseModel):
    page:str
    changes:str

class SummaryResponse(RootModel[list[ChangeFormat]]):
    pass


class promptType(str, Enum):
    DOCUMENT_ANALYSIS = "document_analysis"
    DOCUMENT_COMPARISON = "document_comparison"
    CONTEXTULIZE_QUSTION = "contextulize_question"
    CONTEXT_QA = "context_qa"