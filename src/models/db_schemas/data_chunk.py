from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId

class DataChunk(BaseModel):
    _id: Optional[ObjectId]
    chunk_text: str = Field(..., min_length=1)
    chunk_metadata: dict
    chunk_order: int = Field(..., gt=0)
    file_id: ObjectId


    class config:
        arbitrary_types_allowed = True