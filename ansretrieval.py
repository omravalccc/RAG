import numpy as np
import sqlite3
import os
import requests
from sentence_transformers import SentenceTransformer

def cs(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def top_k_chunks(query_embedding, k=5):
    conn = sqlite3.connect("documents.db")
    cursor = conn.cursor()
    cursor.execute("SELECT document_name, chunk_id, chunk_text, embedding FROM documents")
    rows = cursor.fetchall()
    scored = []
    for name, cid, text, blob in rows:
        emb = np.frombuffer(blob, dtype=np.float32)
        score = cs(query_embedding, emb)
        scored.append((score, name, cid, text))
    conn.close()
    scored.sort(reverse=True, key=lambda x: x[0])
    return scored[:k]

def llm_answer(question, chunks):
    context = "\n\n".join(chunks)

    prompt = f"""
Answer the question using only the information present in the context below.
You may rephrase or explain examples if sufficient information is available.
If the answer is not present, say: "I don't know based on the provided context."

Context:
{context}

Question:
{question}
"""
    models = [
    "models/gemini-1.5-flash",
    "models/gemini-1.0-pro"
]

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent"
        params = {"key": os.getenv("GEMINI_API_KEY")}

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        res = requests.post(url, params=params, json=payload)

        if res.status_code == 200:
            data = res.json()
            if "candidates" in data:
                return data["candidates"][0]["content"]["parts"][0]["text"]

    return "I don't know based on the provided context."



def retrieval(question, k=5):
    model = SentenceTransformer("sentence-transformers/multi-qa-MiniLM-L6-cos-v1")
    query_embedding = model.encode(question)

    results = top_k_chunks(query_embedding, k)

    chunks = []
    evidence = []
    scores = []

    for score, doc, cid, text in results:
        chunks.append(text)
        scores.append(score)
        evidence.append({
            "document": doc,
            "chunk_id": cid,
            "text": text
        })

    answer = llm_answer(question, chunks)

    confidence = float(sum(scores) / len(scores)) if scores else 0.0

    return {
        "question": question,
        "answer": answer,
        "confidence": round(confidence, 3),
        "evidence": evidence
    }
