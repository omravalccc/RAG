from fastapi import UploadFile
from typing import List
from sentence_transformers import SentenceTransformer
import numpy as np
import sqlite3
async def receive_files(files: List[UploadFile]):
    documents = []
    for file in files:
        if not file.filename.endswith(".txt"):
            continue
        content = await file.read()
        text = content.decode("utf-8").strip()
        if text:
            documents.append({
                "document_name": file.filename,
                "text": text
            })
    return documents



def generate_embeddings(chunks):
    model = SentenceTransformer("intfloat/e5-base-v2")
    vectors = []
    for chunk in chunks:
        embedding = model.encode("passage: " + chunk)
        vectors.append(embedding)

    return np.array(vectors)



def store_in_db(documents):
    conn = sqlite3.connect("documents.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            document_name TEXT,
            chunk_id INTEGER,
            chunk_text TEXT,
            embedding BLOB
        )
    """)

    for doc in documents:
        name = doc["document_name"]
        text = doc["text"]

        words = text.split()
        chunks = []

        for i in range(0, len(words), 60):
            chunks.append(" ".join(words[i:i+120]))

        embeddings = generate_embeddings(chunks)

        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            cursor.execute(
                "INSERT INTO documents VALUES (?, ?, ?, ?)",
                (name, i, chunk, emb.tobytes())
            )

    conn.commit()
    conn.close()


