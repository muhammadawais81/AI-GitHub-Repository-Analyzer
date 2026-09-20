__________________________________
🌐 Api # 3: ( Index a cloned repository into ChromaDB for RAG )

📌 route: /repository/index

👉 methode: post

👉 Query Parameter:
 
👉 Query URL: http://127.0.0.1:8000/repository/index

👉 Headers:
______________________

Content-Type: application/json
Accept: application/json

_____________________________

👉 api body: ( Template )  
______________________

{
  "repository_name": "portfolio"
}

_____________________________

👉 Input attributes:

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `repository_name` | string | yes | Local repo name from analyze (`repo`) or `owner/repo` |

👉 Api output: ( Template )
_____________________________

{
  "status": "success",
  "repository_name": "portfolio",
  "files_indexed": 42,
  "chunks": 391
}

_____________________________

👉 Output attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `status` | string | `"success"` when indexing completes |
| `repository_name` | string | Canonical local repository name |
| `files_indexed` | number | Supported source files chunked |
| `chunks` | number | Total vector chunks stored in ChromaDB |

👉 Prerequisites:
- Repository must already exist locally via `/repository/analyze`
- Server must have `OPENAI_API_KEY` configured (embeddings)

👉 Common errors:

| Status | Meaning |
|--------|---------|
| 400 | Invalid repository name |
| 404 | Repository not found locally |
| 422 | No supported files to index |
| 500 | Missing OpenAI API key |
| 502 | Embedding failure |
| 503 | ChromaDB unavailable |

👉 Notes for Next.js:
- Required before `/chat`, `/review`, `/bugs`, `/improvements`, `/tests`, `/documentation`
- Show progress spinner; indexing can take time on large repos
- Re-running replaces previous vectors for that repository

__________________________________
