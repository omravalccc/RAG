# RAG System Documentation

## Project Overview

This is a Retrieval Augmented Generation system built from scratch without using LangChain or LlamaIndex. The system accepts plain text documents, processes them into semantic chunks, generates embeddings, and answers questions based on the retrieved context using a GenAI model.

## Functional Requirements

### Document Ingestion

The system accepts plain text files with txt extension and processes them through the following pipeline:

- Files are split into semantic chunks rather than line-based chunks for better context preservation
- Each chunk is stored in a SQLite database with the following information:
  - Document name
  - Chunk identifier
  - Chunk text content
  - Embedding vector

The database implementation uses SQLite without any vector database systems, keeping the architecture simple and dependency-free.

### Embedding Generation

The system uses Hugging Face embedding models exclusively. All embeddings are generated and stored locally for efficient retrieval.

Key features include:

- Free embedding model from Hugging Face
- Selected model: intfloat/e5-base-v2
- Cosine similarity implemented manually using NumPy
- No external vector database dependencies

For E5 models specifically, the implementation includes:

- Prefix added at embedding time
- Prefix added at query time

This ensures optimal performance with the E5 model family.

### Question Answering System

The QA system uses a free LLM API to generate answers based on retrieved context. The process works as follows:

- Retrieve top-k most relevant chunks from the database
- Construct a carefully designed prompt that allows answering only from retrieved chunks
- Force the model to respond with "I don't know based on the provided context" when insufficient data is available

This approach prevents hallucination and ensures all answers are grounded in the actual document content.

### Confidence and Evidence Tracking

Every response includes confidence scores and evidence sources. This is a critical feature for transparency and reliability.

The API response follows this structure:

```
{
  "question": "string",
  "answer": "string",
  "confidence": 0.0,
  "evidence": [
    {
      "document": "doc.txt",
      "chunk_id": 2,
      "text": "relevant excerpt"
    }
  ]
}
```

The confidence score is computed dynamically based on similarity scores, context coverage, or LLM self-check mechanisms. Hardcoded confidence values are not permitted.

## API Endpoints

The system exposes the following REST endpoints using FastAPI:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /ingest | Upload document |
| POST | /ask | Ask question |
| GET | /health | Health check |

The health check endpoint provides detailed information to help diagnose system issues when things are not working as expected.

## Development Timeline

### Day 1: January 6, 2026, 9:12 AM

#### Step 1: Created docsreciever.py - 10:30 AM

Started by creating the document ingestion module. This component handles the core document processing pipeline including file reading, semantic chunking, and embedding generation using the Hugging Face model. All processed chunks along with their embeddings are stored in the SQLite database for later retrieval.

#### Embedding Model Selection

After evaluating multiple embedding models, the final choice was intfloat/e5-base-v2. Here is the comparison of commonly used embedding models:

| Model Name | Pros | Cons | Best Use Case |
|------------|------|------|---------------|
| sentence-transformers/all-MiniLM-L6-v2 | Very fast, lightweight, good semantic quality, CPU-friendly | Slightly lower accuracy than larger models | General-purpose RAG, assignments, lightweight systems |
| sentence-transformers/all-MiniLM-L12-v2 | Better semantic representation than L6 | Slower, higher memory usage | When accuracy is preferred over speed |
| sentence-transformers/paraphrase-MiniLM-L6-v2 | Strong similarity and paraphrase detection | Not optimized for factual retrieval | Similarity-focused retrieval tasks |
| sentence-transformers/multi-qa-MiniLM-L6-cos-v1 | Optimized for question–answer retrieval | Less general-purpose | QA-based RAG systems |
| BAAI/bge-small-en-v1.5 | Strong retrieval performance, modern model | Heavier than MiniLM, slower on CPU | Higher-quality retrieval with moderate resources |
| BAAI/bge-base-en-v1.5 | Better accuracy than small variant | High memory and compute cost | When better retrieval quality is required |
| intfloat/e5-small-v2 | Trained for retrieval tasks, instruction-style | Requires query formatting | Instruction-based RAG pipelines |
| intfloat/e5-base-v2 | Strong semantic retrieval performance | Slower and heavier than small version | High-quality semantic search |

#### Module Functions Overview

The docsreciever.py module contains these key functions:

| Function | What It Does |
|----------|--------------|
| receive_files() | Reads txt files and extracts raw text |
| generate_embeddings() | Generates embeddings using intfloat/e5-base-v2 |
| store_in_db() | Performs semantic chunking, generates embeddings per chunk, and stores everything in SQLite |

#### Testing Phase - 10:46 AM

Added the ingestion endpoint in app.py and began testing. Successfully uploaded revision.txt from desktop and the database was generated correctly. Embeddings are stored as binary data in the database and will be converted back during retrieval for efficient storage.

#### Commit - 11:00 AM

First commit completed with working document ingestion pipeline.

### Step 2: Answer Retrieval Logic - 11:10 AM

Started developing the answer retrieval logic in ansretrieval.py.

#### LLM API Selection

Evaluated multiple free LLM API options before settling on Google Gemini. Here is the detailed comparison:

| LLM API | Pros | Cons |
|---------|------|------|
| Google Gemini (gemini-pro / gemini-1.5-flash) | Free tier, good reasoning, fast responses, strong instruction following, simple REST API | Rate limits, needs Google account, internet dependency |
| Hugging Face Inference API | Many open-source models, free tier, easy integration | Free models can be slow, strict rate limits, inconsistent uptime |
| Groq API (LLaMA / Mixtral) | Extremely fast inference, free tier available | Rate limits, model availability may change |
| Together AI | Multiple open models, free credits, decent quality | Credits limited, not fully free long-term |
| Ollama (local LLM) | Fully free, runs offline, no rate limits, full control | Requires local setup, high RAM/CPU/GPU usage, deployment complexity |

The decision to use Google Gemini was based on several factors. Hugging Face Inference API showed inconsistent uptime in the free tier, while Groq and Together AI have limitations around model availability and free usage quotas. Ollama requires local setup and additional system resources, making deployment more complex. Google Gemini was selected due to its simple cloud-based configuration and sufficient free-tier rate limits for development and testing.

#### Answer Retrieval Functions

The ansretrieval.py module implements the following functions:

| Function Name | What it Does |
|---------------|--------------|
| cs() | Computes cosine similarity between query embedding and document embeddings using NumPy |
| top_k_chunks() | Retrieves all stored embeddings from SQLite, calculates similarity scores, and selects the top-k most relevant chunks |
| llm_answer() | Sends retrieved chunks and the user question to the Gemini API with a constrained prompt to generate an answer |
| retrieval() | Orchestrates the full pipeline: generates query embedding with query prefix, retrieves top-k chunks, calls the LLM, prepares evidence, and computes confidence |

#### Testing Complete - 12:05 PM

Development of ansretrieval.py completed. Configured the endpoint in app.py and started testing.

Example test response:

```
{
  "question": "Explain the sed backreference example given in the document.",
  "answer": "I don't know based on the provided context.",
  "confidence": 0.823,
  "evidence": [
    {
      "document": "Revision sheet.txt",
      "chunk_id": 4,
      "text": "of backreef s/\\([0-9]\\+\\):\\([0-9]\\+\\)/\\2:\\1/g q5)awk rem u always make a mistake for this shebang is #!/usr/bin/gawk -f BEGIN{ FS=\" \"; } Must write NR==1 { next } BEFORE main condition $2 == 75 && $3 <= 50 { ..... ...... } END{ print $2,\"is greater than 75\",$3,\"is less than 50 for\",count\"times\"; } now if(( )){ ..; } elif (( )){ ..; } else{ ..; } for((i=0;i<=5;i++)){ ..; ..; ))"
    },
    (additional evidence chunks...)
  ]
}
```

Committed the update to ansretrieval.py.

### Deployment Considerations - 12:36 PM

Added vercel.json configuration file for deployment on Vercel platform.

### Model Switch - 1:00 PM

During deployment testing, the intfloat/e5-base-v2 model created issues in the serverless environment. Switched to sentence-transformers/multi-qa-MiniLM-L6-cos-v1 as an alternative.

However, this change caused significant performance degradation. For the same test question about sed backreference, the confidence ratio dropped dramatically to 0.177, which is too low for acceptable performance:

```
{
  "question": "explain backreference in sed",
  "answer": "I don't know based on the provided context.",
  "confidence": 0.177,
  "evidence": [...]
}
```

Such performance degradation cannot be ignored. The confidence score drop from 0.823 to 0.177 represents a serious quality issue.

### Final Decision

Removed the serverless deployment approach and switched back to intfloat/e5-base-v2 model for optimal performance. After reverting, the confidence score returned to 0.815 for the same query:

```
{
  "question": "explain backreference in sed",
  "answer": "I don't know based on the provided context.",
  "confidence": 0.815,
  "evidence": [
    {
      "document": "Revision sheet.txt",
      "chunk_id": 4,
      "text": "of backreef s/\\([0-9]\\+\\):\\([0-9]\\+\\)/\\2:\\1/g q5)awk rem u always make a mistake for this shebang is #!/usr/bin/gawk -f BEGIN{ FS=\" \"; } Must write NR==1 { next } BEFORE main condition $2 == 75 && $3 <= 50 { ..... ...... } END{ print $2,\"is greater than 75\",$3,\"is less than 50 for\",count\"times\"; } now if(( )){ ..; } elif (( )){ ..; } else{ ..; } for((i=0;i<=5;i++)){ ..; ..; ))"
    },
    (additional evidence chunks...)
  ]
}
```

Changes committed to repository with the final model selection.

## Architecture Decisions

### Chunking Strategy

The system uses semantic chunking rather than fixed-size or line-based chunking. This approach preserves context boundaries and ensures that related information stays together in the same chunk, improving retrieval quality.

### Embedding Choice

After extensive testing and comparison, intfloat/e5-base-v2 was selected as the final embedding model. While sentence-transformers/multi-qa-MiniLM-L6-cos-v1 offered better serverless deployment compatibility, the significant drop in confidence scores made it unsuitable for production use. The e5-base-v2 model provides strong semantic retrieval performance with acceptable resource requirements.

### Confidence Logic

Confidence scores are computed dynamically based on the cosine similarity between the query embedding and retrieved chunk embeddings. The system never uses hardcoded confidence values. This ensures that confidence scores accurately reflect the quality of the match between the question and available context.

### Hallucination Prevention

Multiple safeguards prevent the LLM from hallucinating or providing information not present in the documents:

- The prompt explicitly instructs the model to answer only from provided chunks
- The model is forced to say "I don't know based on the provided context" when information is insufficient
- All answers include evidence citations showing which document chunks were used
- Confidence scores help users assess answer reliability

### System Limitations

Users should be aware of the following limitations:

- The system only works with plain text files in txt format
- Embeddings are generated locally which requires adequate computational resources
- Manual cosine similarity calculation may be slower than optimized vector database solutions
- SQLite database may have performance limitations with very large document collections
- The system depends on external LLM API availability and rate limits
- Semantic chunking quality depends on document structure and content

## Restrictions and Constraints

The following restrictions are enforced throughout the system:

- No LangChain or LlamaIndex frameworks allowed
- No vector databases permitted
- No answers provided without supporting evidence
- No hardcoded answers or responses
- All confidence scores must be computed dynamically

## Getting Started

### Installation

Install the required dependencies listed in requirements.txt.

### Configuration

Set up your environment with the necessary API keys for Google Gemini.

### Usage

1. Start the FastAPI server using app.py
2. Upload documents using POST /ingest endpoint
3. Ask questions using POST /ask endpoint
4. Monitor system health using GET /health endpoint

## Repository Standards

The repository maintains the following standards:

- Logical commit history with descriptive messages
- Comprehensive gitignore file
- Detailed README documentation explaining all architectural decisions
- Clear code organization and module separation
- Evidence-based development decisions documented with timestamps and test results
