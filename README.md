# PDF Chatbot

A privacy-friendly PDF question-answering service with local BM25 retrieval and page-level citations. The default answerer is extractive, so it does not invent facts that are absent from the uploaded document.

## Features

- Upload multiple PDFs through a FastAPI endpoint
- Local text extraction and retrieval; no API key required
- Page and filename citations with every answer
- File-size and content-type validation
- CLI and Docker support

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn pdf_chatbot.api:app --reload
```

Open `http://localhost:8000/docs`, upload a document with `POST /documents`, then ask a question with `POST /chat`.

```bash
pdf-chat report.pdf -q "What were the main findings?"
docker build -t pdf-chatbot .
docker run --rm -p 8000:8000 pdf-chatbot
```

## API example

```bash
curl -F "file=@report.pdf" http://localhost:8000/documents
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"What were the main findings?","limit":4}'
```

## Architecture

PDF pages are extracted with `pypdf`, split at natural boundaries, indexed in memory, and ranked using BM25. The deliberately simple storage layer is easy to replace with SQLite or a vector database for production workloads.

## Test

```bash
pytest
ruff check .
```

MIT licensed.
