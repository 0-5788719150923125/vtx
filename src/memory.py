import os
import logging
import numpy as np
from chromadb import chromadb, Documents, EmbeddingFunction, Embeddings
from events import subscribe_event
from head import ctx
from utils import write_to_file

focus = os.environ["FOCUS"]

client = chromadb.EphemeralClient()


class CreateEmbeddings(EmbeddingFunction):
    def __call__(self, texts: Documents) -> Embeddings:
        embeddings = ctx.get_embeddings(texts)
        return embeddings


integrator = CreateEmbeddings()

collection = client.get_or_create_collection(name=focus, embedding_function=integrator)


def create_memory(texts):
    try:
        # embeddings = integrator(texts)
        collection.add(
            # embeddings=embeddings,
            documents=[texts],
            # metadatas=[{"source": "my_source"}, {"source": "my_source"}],
            ids=["id1"],
        )
    except Exception as e:
        # logging.error(e)
        write_to_file("/gen", "err.txt", str(e))


subscribe_event("commit_memory", create_memory)


results = collection.query(query_texts=["Let us"], n_results=2)
print(results)

# results = collection.query(query_texts=["This is a query document"], n_results=2)


# class MyEmbeddingFunction(EmbeddingFunction):
#     def __call__(self, texts: Documents) -> Embeddings:
#         # embed the documents somehow
#         return embeddings
