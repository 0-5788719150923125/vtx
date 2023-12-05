import logging
import os

import numpy as np
from chromadb import Documents, EmbeddingFunction, Embeddings, chromadb
from chromadb.config import Settings

import head
from common import list_full_paths, random_string

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
    except Exception as e:
        logging.error(e)


# subscribe_event("commit_memory", create_memory)


def import_directory(path="/lab/ink"):
    files = list_full_paths(path)
    for file in files:
        try:
            with open(file, "r") as content:
                create_memory(content.read())
        except Exception as e:
            logging.error(e)


import_directory()

query = "What is The Architect's real name?"

results = collection.query(query_texts=[query], n_results=3)

from transformers import pipeline

qa_model = pipeline(
    model=head.ctx.teacher.model,
    tokenizer=head.ctx.teacher.tokenizer,
    task="question-answering",
)

for i, document in enumerate(results["documents"][0]):
    output = qa_model(question=query, context=document)
    print(results["distances"][0][i])
    print(output)
