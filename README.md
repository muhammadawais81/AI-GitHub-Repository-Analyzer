# AI Coding Agent Backend

Phase 1: **Repository Analysis** — clone a public GitHub repository and return structural metadata.

Phase 2: **Coding Review Agent** — Q&A over a cloned repository with the OpenAI Agents SDK routed through Groq.

Phase 3: **RAG** — chunk code, embed locally with Sentence Transformers, store in ChromaDB, retrieve top matches before answering.

Phase 4: **AI Software Engineer** — review code, detect bugs, suggest improvements, generate tests & documentation (analysis only; never writes to the repo).

## Tech Stack

- Python 3.12+
- FastAPI
- GitPython
- Pydantic v2
- python-dotenv
- uvicorn
- OpenAI Agents SDK (`openai-agents`) with Groq (OpenAI-compatible API)
- Local embeddings via Sentence Transformers (`BAAI/bge-small-en-v1.5`)
- ChromaDB (persistent)

## Installation

```bash
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
copy .env.example .env
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
cp .env.example .env
```

## Groq Setup (LLM only)

1. Create an API key at [console.groq.com](https://console.groq.com/).
2. Add it to your `.env` file:

```env
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_BASE_URL=https://api.groq.com/openai/v1
```

The backend uses the official `openai` Python client and OpenAI Agents SDK pointed at Groq's OpenAI-compatible endpoint for chat / analysis. No OpenAI API key is required.

`POST /chat` and all Phase 4 analysis endpoints require a valid `GROQ_API_KEY`.

## Local Embeddings (RAG)

Embeddings are generated **locally** with Sentence Transformers. No embedding API key is required.

```env
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
```

On first index/retrieval, the model is downloaded once and kept in memory (singleton). `POST /repository/index` only needs this local model — it does not call Groq for embeddings.
## Run Server

```bash
uvicorn aicodingagentbackend.main:app --reload --reload-dir src --host 0.0.0.0 --port 8000
```

Docs: http://127.0.0.1:8000/docs

## Typical Workflow

1. `POST /repository/analyze` — clone the GitHub repo locally
2. `POST /repository/index` — chunk → embed → store in ChromaDB
3. Ask questions via `POST /chat` **or** run structured analyses:
   - `POST /review`
   - `POST /bugs`
   - `POST /improvements`
   - `POST /tests`
   - `POST /documentation`

## How Indexing Works

Supported files only: `.py`, `.js`, `.ts`, `.jsx`, `.tsx`, `.json`, `.yml`, `.yaml`, `.md`

1. Read each supported file from the cloned repository
2. Split into chunks of **1000** characters with **200** character overlap
3. Generate embeddings locally with Sentence Transformers `BAAI/bge-small-en-v1.5`
4. Upsert into persistent ChromaDB at `src/aicodingagentbackend/chroma_db/`
5. Collection name: `repositories`

Each chunk stores metadata:

- `repository_name`
- `file_path`
- `language`
- `chunk_index`
- `chunk_number`

Re-indexing a repository deletes its previous vectors first, then writes a fresh index.

### `POST /repository/index`

**Request**

```json
{
  "repository_name": "portfolio"
}
```

**Response**

```json
{
  "status": "success",
  "repository_name": "portfolio",
  "files_indexed": 42,
  "chunks": 391
}
```

## How RAG / Semantic Search Works

1. Embed the user question with the same embedding model
2. Query ChromaDB filtered by `repository_name`
3. Return the **top 5** nearest chunks (cosine distance)
4. Pass those chunks to the Coding Review Agent as context
5. The agent may call `retrieve_relevant_chunks()` again for a refined search
6. The agent calls `read_file()` only when a full file is still needed

### `POST /chat`

**Request**

```json
{
  "repository_name": "portfolio",
  "question": "Where is JWT implemented?"
}
```

**Example response**

```json
{
  "repository_name": "portfolio",
  "question": "Where is JWT implemented?",
  "answer": "JWT handling appears in ...",
  "model": "llama-3.3-70b-versatile",
  "agent": "Coding Review Agent"
}
```

**Supported question examples**

- Explain authentication.
- Where is JWT implemented?
- Explain database models.
- How does login work?
- Find SQL queries.
- Explain middleware.
- List API endpoints.
- Explain project architecture.
- Suggest improvements.
- Review this repository.
- Find bugs.
- Generate unit tests.
- Improve this function.
- Explain this class.
- Write documentation.
- What should be refactored?
- Is this production ready?

## Phase 4 — AI Software Engineer APIs

All Phase 4 endpoints:

- Accept `{ "repository_name": "...", "focus": "optional" }`
- Require the repository to be **indexed** first
- Use RAG (`retrieve_relevant_chunks` / specialized tools) instead of loading the whole repo
- Return structured JSON
- **Never modify** repository files

### `POST /review`

Professional code review with scores and strengths/weaknesses.

```json
{
  "repository_name": "portfolio",
  "focus": "authentication"
}
```

Response includes: `overall_score`, `strengths`, `weaknesses`, `code_quality`, `architecture_quality`, `readability`, `maintainability`, `summary`.

### `POST /bugs`

Potential bugs, logic issues, dead/duplicate code, exception risks, security and performance concerns.

Response includes: `bugs[]` with `severity`, `description`, `file`, `line`, `recommendation`, plus `count` and `summary`.

### `POST /improvements`

Naming, simplification, refactoring, performance, architecture, and Python best-practice recommendations.

### `POST /tests`

Generated **pytest** tests as response text (normal / edge / invalid input). Does not write files.

### `POST /documentation`

Module summary, function/class descriptions, README improvements, and a full documentation markdown body.

### Agent tools (Phase 4)

The Coding Review Agent can choose among:

- `retrieve_relevant_chunks`
- `review_code`
- `detect_bugs`
- `suggest_improvements`
- `generate_tests`
- `generate_documentation`
- plus existing read/search tools

## Phase 1 Analyze Endpoint

### `POST /repository/analyze`

```json
{
  "github_url": "https://github.com/user/project"
}
```

## Error Handling

| Situation | HTTP status |
|-----------|-------------|
| Invalid repository name | 400 |
| Missing local repository | 404 |
| Repository not indexed | 404 |
| Empty / no supported files | 422 |
| Embedding failure | 502 |
| Groq / agent failure | 502 |
| ChromaDB unavailable | 503 |
| Missing `GROQ_API_KEY` | 500 |

## Folder Structure

```text
aiCodingAgentBackend/
├── app/repositories/
├── src/aicodingagentbackend/
│   ├── main.py
│   ├── chroma_db/                 # Persistent ChromaDB
│   ├── api/
│   │   ├── repository.py          # /analyze, /index
│   │   ├── chat.py                # /chat
│   │   └── analysis.py            # /review, /bugs, /tests, /documentation, /improvements
│   ├── agents/
│   │   └── coding_agent.py
│   ├── tools/
│   │   ├── repository_tools.py
│   │   ├── engineering_tools.py   # Phase 4 analysis tools
│   │   └── rag_helpers.py
│   ├── services/
│   │   ├── git_service.py
│   │   ├── repository_service.py
│   │   ├── agent_service.py
│   │   ├── analysis_service.py
│   │   ├── repository_resolver.py
│   │   └── rag/
│   ├── schemas/
│   │   ├── repository.py
│   │   ├── chat.py
│   │   └── analysis.py
│   ├── core/
│   │   ├── config.py
│   │   └── groq_config.py
│   └── utils/
├── .env.example
├── requirements.txt
└── README.md
```

## Notes

- Do **not** use LangChain, LangGraph, LlamaIndex, FAISS, Pinecone, Redis, or Celery in this project.
- Phase 3/4 avoid reading every file on each request; retrieval supplies only the most relevant chunks.
- Phase 4 generates analysis outputs only — it never edits the cloned repository.
- Prefer `--reload-dir src` so cloned repos and Chroma files do not thrash the reloader.
#   A I - G i t H u b - R e p o s i t o r y - A n a l y z e r  
 