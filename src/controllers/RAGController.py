from .BaseController import BaseController
from models.db_schemas import File, DataChunk
from stores.llm.LLMEnums import DocumentTypeEnums
from typing import List
import json

class RAGController(BaseController):

    def __init__(self, vector_db_client, generation_client, embedding_client, template_parser):
        super().__init__()

        self.vector_db_client = vector_db_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser

    def create_collection_name(self, file_id: str):
        return f"collection_{file_id}".strip()
    
    def reset_vector_db_collection(self, file: File):
        collection_name = self.create_collection_name(file_id= file.file_id)
        return self.vector_db_client.delete_collection(collection_name= collection_name)

    def get_vector_db_collection_info(self, file: File):
        collection_name = self.create_collection_name(file_id= file.file_id)
        collection_info = self.vector_db_client.get_collection_info(collection_name= collection_name)

        return json.loads(
            json.dumps(collection_info, default= lambda x: x.__dict__)
        )
    
    def index_into_vector_db(self, file: File, chunks: List[DataChunk],
                             chunks_ids: List[int], do_reset: bool = False):
        
        # get collection name
        collection_name = self.create_collection_name(file_id= file.file_id)

        # manage items in the collection
        texts = [chunk.chunk_text for chunk in chunks]
        metadata = [chunk.chunk_metadata for chunk in chunks]
        vectors = [
            self.embedding_client.embed_text(text= text, document_type= DocumentTypeEnums.DOCUMENT.value)
            for text in texts
        ]

        # create collection if it does not exist
        _ = self.vector_db_client.create_collection(
            collection_name= collection_name,
            embedding_size= self.embedding_client.embedding_size,
            do_reset= do_reset,
        )

        # insert items into the collection
        _ = self.vector_db_client.insert_many(
            collection_name= collection_name,
            texts= texts,
            vectors= vectors,
            metadata= metadata,
            record_ids= chunks_ids,
        )

        return True
    
    def search_vector_db_collection(self, file: File, text: str, limit: int = 5):

        collection_name = self.create_collection_name(file_id= file.file_id)

        vector = self.embedding_client.embed_text(text= text, document_type= DocumentTypeEnums.QUERY.value)

        if not vector or len(vector) == 0:
            return False
        
        result = self.vector_db_client.search_by_vector(
            collection_name= collection_name,
            vector= vector,
            limit= limit
        )

        if not result:
            return False
        
        return result
    
    def answer_rag_question(self, file: File, query: str, limit: int = 5):

        answer, full_prompt, chat_history = None, None, None

        retrived_docs = self.search_vector_db_collection(
            file= file,
            text= query,
            limit= limit,
        )

        if not retrived_docs or len(retrived_docs) == 0:
            return answer, full_prompt, chat_history
    
        system_prompt = self.template_parser.get(group= "rag", key= "system_prompt")
        documents_prompts = "\n".join([
            self.template_parser.get(
                group= "rag",
                key= "document_prompt",
                vars= {
                    "doc_num": idx + 1,
                    "chunk_text": doc.text,
                }
            )
            for idx, doc in enumerate(retrived_docs)
        ])
        footer_prompt = self.template_parser.get(group= "rag", key= "footer_prompt", vars= {"query": query})

        chat_history = [
            self.generation_client.construct_prompt(prompt= system_prompt, role= self.generation_client.enums.SYSTEM.value)
        ]

        full_prompt = "\n\n".join([documents_prompts, footer_prompt])

        answer = self.generation_client.generate_text(prompt= full_prompt, chat_history= chat_history)

        if not answer or len(answer) == 0:
            return answer, full_prompt, chat_history
        
        return answer, full_prompt, chat_history