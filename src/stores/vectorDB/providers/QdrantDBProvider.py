from qdrant_client import QdrantClient, models
from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMethodEnum
import logging
from typing import List
from models.db_schemas import RetrivedDocument

class QdrantDBProvider(VectorDBInterface):

    def __init__(self, db_path: str, distance_method: str):
        
        self.client = None
        self.db_path = db_path
        self.distance_method = None

        self.logger = logging.getLogger(__name__)

        if distance_method == DistanceMethodEnum.COSINE.value:
            self.distance_method = models.Distance.COSINE

        elif distance_method == DistanceMethodEnum.DOT.value:
            self.distance_method = models.Distance.DOT

    def connect(self):
        self.client = QdrantClient(path= self.db_path)

    def disconnect(self):
        self.client = None

    def is_collection_exists(self, collection_name: str) -> bool:
        return self.client.collection_exists(collection_name= collection_name)
    
    def list_all_clollections(self) -> List:
        return self.client.get_collections()
    
    def get_collection_info(self, collection_name: str) -> dict:
        return self.client.get_collection(collection_name= collection_name)
    
    def create_collection(self, collection_name: str, embedding_size: int, do_reset: bool = False):
        if do_reset:
            self.delete_collection(collection_name= collection_name)

        if not self.is_collection_exists(collection_name= collection_name):
            self.client.create_collection(
                collection_name= collection_name,
                vectors_config= models.VectorParams(size= embedding_size, distance= self.distance_method)
            )

            return True
        
        self.logger.error(f"Error while creating collection {collection_name}.")
        return False
    
    def delete_collection(self, collection_name: str):
        if self.is_collection_exists(collection_name= collection_name):
            return self.client.delete_collection(collection_name= collection_name)
        else:
            self.logger.warning(f"Collection {collection_name} does not exist.")
            return None
        
    def insert_one(self, collection_name: str, text: str,
                   vector: list, metadata: dict = None, record_id: str = None):
        
        if not self.is_collection_exists(collection_name= collection_name):
            self.logger.error(f"cannot insert record into collection {collection_name} because it does not exist.")
            return False
        
        try:
            self.client.upload_records(
                collection_name= collection_name,
                records= [
                    models.Record(
                        vector= vector,
                        id= [record_id],
                        payload= {
                            "text": text,
                            "metadata": metadata
                        }
                    )
                ]
            )
        except Exception as e:
            self.logger.error(f"Error inserting record: {e}")
            return False

        return True

    def insert_many(self, collection_name: str, texts: list,
                    vectors:list, metadata: list = None,
                    record_ids: list = None, batch_size: int = 50):
        
        if metadata is None:
            metadata = [None] * len(texts)

        if record_ids is None:
            record_ids = list(range(0, len(texts)))

        for i in range(0, len(texts), batch_size):
            batch_end = i + batch_size

            batch_texts = texts[i: batch_end]
            batch_vectors = vectors[i: batch_end]
            batch_metadata = metadata[i: batch_end]
            batch_record_ids = record_ids[i: batch_end]

            batch_records = [
                models.Record(
                    vector= batch_vectors[x],
                    id= batch_record_ids[x],
                    payload= {
                        "text": batch_texts[x],
                        "metadata": batch_metadata[x]
                    }
                )
                for x in range(len(batch_texts))
            ]

            try:
                self.client.upload_records(
                    collection_name= collection_name,
                    records= batch_records,
                )
            except Exception as e:
                self.logger.error(f"Error inserting batch: {e}")
                return False
                
            return True

    def search_by_vector(self, collection_name: str, vector: list, limit: int = 5):
        results = self.client.search(
            collection_name= collection_name,
            query_vector= vector,
            limit= limit
        )

        if not results or len(results) == 0:
            self.logger.warning(f"No results found for the given vector in collection {collection_name}.")
            return None
        
        return [
            RetrivedDocument(**{
                "score": result.score,
                "text": result.payload["text"],
            })
            for result in results
        ]