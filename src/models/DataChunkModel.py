from .BaseDataModel import BaseDataModel
from .db_schemas.data_chunk import DataChunk
from bson.objectid import ObjectId
from pymongo import InsertOne

class DataChunkModel(BaseDataModel):

    def __init__(self, db_client):
        super().__init__(db_client= db_client)
        self.collection = self.db_client["DataChunks"]

    async def insert_data_chunk(self, data_chunk: DataChunk):

        result = await self.collection.insert_one(data_chunk.dict(by_alias=True, exclude_unset=True))
        data_chunk._id = result.inserted_id

        return data_chunk
    
    async def get_data_chunk(self, data_chunk_id: str):
        
        result = await self.collection.find_one({"_id": ObjectId(data_chunk_id)})

        if result is None:
            return None
        
        return DataChunk(**result)
    
    async def insert_many_data_chunks(self, data_chunks: list, batch_size: int= 100):

        inserted_chunks = 0
        for i in range(0, len(data_chunks), batch_size):
            batch = data_chunks[i: i + batch_size]
            operations = [
                InsertOne(data_chunk.dict(by_alias=True, exclude_unset=True))
                for data_chunk in batch
            ]

            await self.collection.bulk_write(operations)
            inserted_chunks = inserted_chunks + len(batch)

        return inserted_chunks