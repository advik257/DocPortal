from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any , Union

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