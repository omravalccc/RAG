from fastapi import FastAPI, UploadFile, File
from typing import List
from docsreciever import receive_files, store_in_db
app = FastAPI(
    title="Lightweight RAG System",
    description="RAG system without LangChain or vector databases",
    version="0.1.0"
)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "components": {
            "api": "running",
            "database": "unknown",
            "embedding_model": "intfloat/e5-base-v2",
            "llm": "not_configured"
        }
    }

@app.post("/ingest")
async def ingest(files: List[UploadFile] = File(...)):
    documents = await receive_files(files)
    store_in_db(documents)
    return {
        "status": "success",
        "documents_received": len(documents)
    }
