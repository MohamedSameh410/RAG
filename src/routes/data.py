from fastapi import FastAPI, APIRouter, Depends, UploadFile, Request
from helpers.config import get_settings, settings
from controllers import DataController, ProcessController
from .schemas import ProcessRequest
from models import FileModel, DataChunkModel
from models.db_schemas.data_chunk import DataChunk
import os

data_router = APIRouter()

@data_router.post("/uploadfile")
async def upload_file(request: Request, file: UploadFile, app_settings: settings = Depends(get_settings)):
    
    file_model = FileModel(db_client= request.app.db_client)
    data_controller = DataController()
    is_valid = data_controller.validate_file(file= file)
    check_dir = data_controller.check_dir()

    if is_valid and check_dir:
        await data_controller.save_file(file= file)
        file_id = data_controller.file_id
        await file_model.get_or_insert_file(file_id= file_id)
        return {"status": "success",
                "message": "File uploaded successfully",
                "file_id": file_id
                }
    

@data_router.post("/processfile")
async def process_file(request: Request, process_request: ProcessRequest):

    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size

    file_model = FileModel(db_client= request.app.db_client)
    file_db = await file_model.get_or_insert_file(file_id= file_id)

    process_controller = ProcessController()
    file_content = process_controller.get_file_content(file_id= file_id)
    file_chunks = process_controller.process_file_content(
        file_content= file_content,
        file_id= file_id,
        chunk_size= chunk_size,
        overlap_size= overlap_size
    )

    if file_chunks is None or len(file_chunks) == 0:
        return {"status": "error",
                "message": "Error processing file"
                }
    
    file_chunks_db_records = [
        DataChunk(
            chunk_text= chunk.page_content,
            chunk_metadata= chunk.metadata,
            chunk_order= i + 1,
            file_id= file_db.id
        )
        for i, chunk in enumerate(file_chunks)
    ]

    data_chunk_model = DataChunkModel(db_client= request.app.db_client)
    num_records = await data_chunk_model.insert_many_data_chunks(data_chunks= file_chunks_db_records)
    
    return {
        "message": "File processed successfully",
        "inserted chunks": num_records
    }