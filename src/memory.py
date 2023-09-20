import os
import logging
import numpy as np
from chromadb import chromadb, Documents, EmbeddingFunction, Embeddings
from chromadb.config import Settings
from events import subscribe_event
from head import ctx
from utils import random_string

focus = os.environ["FOCUS"]

client = chromadb.EphemeralClient(Settings(anonymized_telemetry=False))

collection = client.get_or_create_collection(name=focus)


def create_memory(texts):
    try:
        collection.add(
            documents=[texts],
            # metadatas=[{"source": "my_source"}, {"source": "my_source"}],
            ids=[random_string(length=7)],
        )
        results = collection.query(query_texts=["Let us"], n_results=2)
        print(results)
    except Exception as e:
        logging.error(e)


subscribe_event("commit_memory", create_memory)

# results = collection.query(query_texts=["This is a query document"], n_results=2)
