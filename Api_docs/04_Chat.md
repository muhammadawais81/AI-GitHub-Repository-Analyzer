__________________________________
🌐 Api # 4: ( Ask the Coding Review Agent a question about an indexed repository )

📌 route: /chat

👉 methode: post

👉 Query Parameter:
 
👉 Query URL: http://127.0.0.1:8000/chat

👉 Headers:
______________________

Content-Type: application/json
Accept: application/json

_____________________________

👉 api body: ( Template )  
______________________

{
  "repository_name": "portfolio",
  "question": "Explain the authentication flow."
}

_____________________________

👉 Input attributes:

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `repository_name` | string | yes | Indexed local repo name (`repo` or `owner/repo`) |
| `question` | string | yes | Natural-language question about the code |

👉 Api output: ( Template )
_____________________________

{
  "repository_name": "portfolio",
  "question": "Explain the authentication flow.",
  "answer": "Authentication is handled in app/auth.py. Login validates credentials, issues a token, and protects routes via middleware...",
  "model": "gpt-5.5",
  "agent": "Coding Review Agent"
}

_____________________________

👉 Output attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `repository_name` | string | Repo that was queried |
| `question` | string | Echo of the user question |
| `answer` | string | Agent answer (markdown-friendly text) |
| `model` | string | OpenAI model used |
| `agent` | string | Agent name (`Coding Review Agent`) |

👉 Example questions:
- Explain this repository.
- Where is JWT implemented?
- List API endpoints.
- Is this production ready?
- Find bugs / suggest improvements (chat form)

👉 Prerequisites:
- `/repository/analyze` done
- `/repository/index` done
- `OPENAI_API_KEY` configured

👉 Common errors:

| Status | Meaning |
|--------|---------|
| 400 | Missing/invalid input |
| 404 | Repo missing or not indexed |
| 500 | Missing OpenAI API key |
| 502 | OpenAI / agent failure |
| 503 | ChromaDB unavailable |

👉 Notes for Next.js:
- Best rendered as a chat UI
- Display `answer` with a markdown renderer
- Expect longer latency (RAG + agent tools)

__________________________________
