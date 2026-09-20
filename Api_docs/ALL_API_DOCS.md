# AI Coding Agent Backend — Complete API Documentation

Base URL (local):

```text
http://127.0.0.1:8000
```

Interactive Swagger UI: `http://127.0.0.1:8000/docs`

## Table of contents

1. [Next.js Frontend Flow](#nextjs-frontend-integration-flow)
2. [Api #1 — Health](#api--1-health-check--verify-backend-is-running)
3. [Api #2 — Analyze](#api--2-clone-a-public-github-repository-and-return-structural-analysis)
4. [Api #3 — Index](#api--3-index-a-cloned-repository-into-chromadb-for-rag)
5. [Api #4 — Chat](#api--4-ask-the-coding-review-agent-a-question-about-an-indexed-repository)
6. [Api #5 — Review](#api--5-run-a-professional-code-review-with-quality-scores)
7. [Api #6 — Bugs](#api--6-detect-potential-bugs-security-risks-and-reliability-issues)
8. [Api #7 — Improvements](#api--7-suggest-refactoring-and-code-quality-improvements)
9. [Api #8 — Tests](#api--8-generate-pytest-unit-tests-as-text--does-not-write-files)
10. [Api #9 — Documentation](#api--9-generate-modulefunctionclass-documentation-and-readme-ideas)
11. [Common Errors](#common-error-responses)

## Required order for most features

```text
1) POST /repository/analyze   → clone + structure metadata
2) POST /repository/index     → embeddings into ChromaDB
3) POST /chat or /review /bugs /improvements /tests /documentation
```

## Common headers

```http
Content-Type: application/json
Accept: application/json
```

No auth headers are required by the backend today (OpenAI key stays on the server `.env`).

---

# Next.js Frontend Integration Flow

This guide explains how to wire the AI Coding Agent backend into a Next.js app.

## 1) Environment

In Next.js (`.env.local`):

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Use a server-side env var (without `NEXT_PUBLIC_`) if you proxy through Next.js Route Handlers.

## 2) Recommended UX screens

1. **Connect Repository** — user pastes a GitHub URL
2. **Indexing Progress** — call index after analyze succeeds
3. **Workspace Dashboard** — tabs/actions for Chat, Review, Bugs, Improvements, Tests, Docs
4. **Result Viewer** — render structured JSON (scores, lists, markdown, code blocks)

## 3) End-to-end product flow

```text
User pastes GitHub URL
        │
        ▼
POST /repository/analyze
  • Save repository_name from response
  • Show languages, framework, tree summary
        │
        ▼
POST /repository/index
  • { repository_name }
  • Show files_indexed + chunks
  • Keep repository_name in app state / URL / localStorage
        │
        ▼
User chooses an action
   ┌────────────┬──────────┬──────────────┬─────────┬──────────────┐
   │ Chat       │ Review   │ Bugs         │ Tests   │ Documentation│
   │ /chat      │ /review  │ /bugs        │ /tests  │ /documentation│
   │            │          │ /improvements│         │              │
   └────────────┴──────────┴──────────────┴─────────┴──────────────┘
```

## 4) State you should keep in the frontend

| State key | Source | Used by |
|-----------|--------|---------|
| `githubUrl` | user input | `/repository/analyze` |
| `repositoryName` | analyze response `repository_name` | all later APIs |
| `indexStats` | index response | dashboard badge |
| `analysisFocus` | optional user input | review/bugs/improvements/tests/docs |

Important: after analyze, prefer storing `repository_name` exactly as returned (e.g. `flask`).  
If multiple clones share the same name under different owners, pass `owner/repo`.

## 5) Suggested Next.js API helper

```ts
// lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL!;

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.detail ?? `Request failed (${res.status})`);
  }
  return data as T;
}
```

## 6) Screen-by-screen calls

### A) Connect repository page

1. User submits GitHub URL
2. Call `POST /repository/analyze`
3. On success:
   - store `repository_name`
   - immediately call `POST /repository/index`
4. On index success → redirect to workspace

Timeout tip: analyze/index/chat/review can take longer than normal CRUD APIs.  
Increase UI loading states (and optionally `AbortSignal` timeouts to 2–5 minutes for AI endpoints).

### B) Chat page

```ts
await apiPost("/chat", {
  repository_name: repositoryName,
  question: userQuestion,
});
```

Render `answer` as markdown.

### C) Review / Bugs / Improvements / Tests / Docs pages

Shared body:

```ts
{
  repository_name: repositoryName,
  focus: optionalFocus || undefined
}
```

| Button | Endpoint |
|--------|----------|
| Run Review | `POST /review` |
| Find Bugs | `POST /bugs` |
| Suggest Improvements | `POST /improvements` |
| Generate Tests | `POST /tests` |
| Generate Docs | `POST /documentation` |

## 7) UI rendering tips

- **Review**: score cards + strengths/weaknesses lists
- **Bugs**: table filtered by `severity`
- **Improvements**: cards by `category`
- **Tests**: code blocks per `tests[].test_code` (copy button)
- **Documentation**: markdown for `full_documentation`; lists for functions/classes

## 8) Error handling in Next.js

Backend errors look like:

```json
{ "detail": "Repository 'x' is not indexed. Run POST /repository/index first." }
```

Map common cases:

| Message / status | Frontend action |
|------------------|-----------------|
| 404 not found locally | Ask user to analyze again |
| 404 not indexed | Auto-offer “Index repository” button |
| 422 empty/no supported files | Show unsupported-repo message |
| 500 missing OpenAI key | Server config issue (not user fault) |
| 502 / 503 | Retry with backoff |

## 9) CORS note

If the Next.js app runs on another origin (e.g. `localhost:3000`), enable CORS on FastAPI or proxy via Next.js Route Handlers (`app/api/.../route.ts`) to avoid browser CORS issues.

Recommended for production: Next.js server routes → backend (keeps backend URL private if needed).

## 10) Minimal page map

```text
/connect          → analyze + index
/workspace/[repo] → dashboard
/workspace/[repo]/chat
/workspace/[repo]/review
/workspace/[repo]/bugs
/workspace/[repo]/improvements
/workspace/[repo]/tests
/workspace/[repo]/docs
```

---

__________________________________
🌐 Api # 1: ( Health check — verify backend is running )

📌 route: /health

👉 methode: get

👉 Query Parameter:
 
👉 Query URL: http://127.0.0.1:8000/health

👉 Headers:
______________________

Accept: application/json

_____________________________

👉 api body: ( Template )  
______________________

(none — GET request has no body)

_____________________________


👉 Api output: ( Template )
_____________________________

{
  "status": "ok"
}

_____________________________

👉 Notes for Next.js:
- Call on app load or settings page to show “Backend Online/Offline”
- No repository setup required

__________________________________

---

__________________________________
🌐 Api # 2: ( Clone a public GitHub repository and return structural analysis )

📌 route: /repository/analyze

👉 methode: post

👉 Query Parameter:
 
👉 Query URL: http://127.0.0.1:8000/repository/analyze

👉 Headers:
______________________

Content-Type: application/json
Accept: application/json

_____________________________

👉 api body: ( Template )  
______________________

{
  "github_url": "https://github.com/user/project"
}

_____________________________

👉 Input attributes:

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `github_url` | string (URL) | yes | Public GitHub repo URL (`https://github.com/owner/repo`) |

👉 Api output: ( Template )
_____________________________

{
  "repository_name": "project",
  "framework": "FastAPI",
  "languages": ["Python", "Markdown"],
  "files": 32,
  "folders": 9,
  "readme": true,
  "requirements": true,
  "license": true,
  "entry_file": "app/main.py",
  "requirements_file": "requirements.txt",
  "python_version": ">=3.12",
  "largest_files": [
    {
      "path": "package-lock.json",
      "size_bytes": 120000
    }
  ],
  "folder_structure": [
    "app/",
    "tests/"
  ],
  "tree": [
    "README.md",
    "app/",
    "app/main.py"
  ]
}

_____________________________

👉 Output attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `repository_name` | string | Local folder name (use this later for index/chat/analysis) |
| `framework` | string \| null | Detected framework (FastAPI, React, etc.) |
| `languages` | string[] | Detected languages by frequency |
| `files` | number | File count (ignored dirs excluded) |
| `folders` | number | Folder count |
| `readme` | boolean | README exists |
| `requirements` | boolean | Dependency manifest found |
| `license` | boolean | LICENSE exists |
| `entry_file` | string \| null | Best-guess entry file |
| `requirements_file` | string \| null | Path to dependency file |
| `python_version` | string \| null | Detected Python version constraint |
| `largest_files` | object[] | Top largest files |
| `folder_structure` | string[] | Folder paths |
| `tree` | string[] | File/folder tree listing |

👉 Common errors:

| Status | Meaning |
|--------|---------|
| 400 | Invalid GitHub URL |
| 403 | Private / access denied |
| 404 | Repository not found on GitHub |
| 422 | Empty repository |
| 502 | Git clone failed |

👉 Notes for Next.js:
- First step in onboarding
- Save `repository_name` from response into app state
- Then call `/repository/index`

__________________________________

---

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

---

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

---

__________________________________
🌐 Api # 5: ( Run a professional code review with quality scores )

📌 route: /review

👉 methode: post

👉 Query Parameter:
 
👉 Query URL: http://127.0.0.1:8000/review

👉 Headers:
______________________

Content-Type: application/json
Accept: application/json

_____________________________

👉 api body: ( Template )  
______________________

{
  "repository_name": "portfolio",
  "focus": "authentication"
}

_____________________________

👉 Input attributes:

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `repository_name` | string | yes | Indexed local repo name (`repo` or `owner/repo`) |
| `focus` | string \| null | no | Optional focus area (module/feature/concern) |

👉 Api output: ( Template )
_____________________________

{
  "repository_name": "portfolio",
  "overall_score": 7.5,
  "strengths": [
    "Clear module boundaries",
    "Consistent naming in API layer"
  ],
  "weaknesses": [
    "Limited input validation in some routes",
    "Sparse test coverage around auth edge cases"
  ],
  "code_quality": 7.0,
  "architecture_quality": 8.0,
  "readability": 7.5,
  "maintainability": 7.0,
  "summary": "Solid foundation with good structure; tighten validation and tests before production."
}

_____________________________

👉 Output attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `repository_name` | string | Reviewed repository |
| `overall_score` | number (0–10) | Overall review score |
| `strengths` | string[] | What’s working well |
| `weaknesses` | string[] | Gaps / risks |
| `code_quality` | number (0–10) | Code quality score |
| `architecture_quality` | number (0–10) | Architecture score |
| `readability` | number (0–10) | Readability score |
| `maintainability` | number (0–10) | Maintainability score |
| `summary` | string | Short overall verdict |

👉 Prerequisites:
- Repository analyzed + indexed
- OpenAI configured

👉 Notes for Next.js:
- Render score cards for the 4 quality metrics + overall
- Lists for strengths/weaknesses
- Does **not** modify repository files

__________________________________

---

__________________________________
🌐 Api # 6: ( Detect potential bugs, security risks, and reliability issues )

📌 route: /bugs

👉 methode: post

👉 Query Parameter:
 
👉 Query URL: http://127.0.0.1:8000/bugs

👉 Headers:
______________________

Content-Type: application/json
Accept: application/json

_____________________________

👉 api body: ( Template )  
______________________

{
  "repository_name": "portfolio",
  "focus": "auth"
}

_____________________________

👉 Input attributes:

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `repository_name` | string | yes | Indexed local repo name |
| `focus` | string \| null | no | Optional focus (e.g. auth, database, API) |

👉 Api output: ( Template )
_____________________________

{
  "repository_name": "portfolio",
  "bugs": [
    {
      "severity": "high",
      "description": "Password compared in plain text without hashing",
      "file": "app/auth.py",
      "line": 42,
      "recommendation": "Hash passwords with a strong algorithm (e.g. bcrypt/argon2) and compare hashes."
    },
    {
      "severity": "medium",
      "description": "Broad except block may hide unexpected failures",
      "file": "app/services/user_service.py",
      "line": 88,
      "recommendation": "Catch specific exceptions and log unexpected errors."
    }
  ],
  "count": 2,
  "summary": "Found 2 potential issues, primarily around authentication and error handling."
}

_____________________________

👉 Output attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `repository_name` | string | Analyzed repository |
| `bugs` | object[] | List of findings |
| `bugs[].severity` | `"critical"` \| `"high"` \| `"medium"` \| `"low"` | Severity |
| `bugs[].description` | string | What the issue is |
| `bugs[].file` | string | File path |
| `bugs[].line` | number \| null | Line number when detectable |
| `bugs[].recommendation` | string | How to fix |
| `count` | number | Number of findings |
| `summary` | string | Short overview |

👉 Notes for Next.js:
- Table/list filtered by severity chips
- Link `file` path in UI (even if read-only)
- Analysis only — no file writes

__________________________________

---

__________________________________
🌐 Api # 7: ( Suggest refactoring and code-quality improvements )

📌 route: /improvements

👉 methode: post

👉 Query Parameter:
 
👉 Query URL: http://127.0.0.1:8000/improvements

👉 Headers:
______________________

Content-Type: application/json
Accept: application/json

_____________________________

👉 api body: ( Template )  
______________________

{
  "repository_name": "portfolio",
  "focus": "api layer"
}

_____________________________

👉 Input attributes:

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `repository_name` | string | yes | Indexed local repo name |
| `focus` | string \| null | no | Optional focus area |

👉 Api output: ( Template )
_____________________________

{
  "repository_name": "portfolio",
  "improvements": [
    {
      "category": "naming",
      "description": "Helper function name is too generic",
      "file": "app/utils.py",
      "recommendation": "Rename `process_data` to a domain-specific name like `normalize_user_payload`."
    },
    {
      "category": "architecture",
      "description": "Business logic lives directly in route handlers",
      "file": "app/api/users.py",
      "recommendation": "Move business rules into a service layer and keep routes thin."
    }
  ],
  "count": 2,
  "summary": "Focus on clearer naming and separating API routes from business logic."
}

_____________________________

👉 Output attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `repository_name` | string | Analyzed repository |
| `improvements` | object[] | Suggestion list |
| `improvements[].category` | string | e.g. naming, refactoring, performance, architecture, best_practices |
| `improvements[].description` | string | What should improve |
| `improvements[].file` | string \| null | Related file if known |
| `improvements[].recommendation` | string | Concrete recommendation |
| `count` | number | Number of suggestions |
| `summary` | string | Overview |

👉 Notes for Next.js:
- Group cards by `category`
- Optional focus input improves relevance
- Does not edit the repository

__________________________________

---

__________________________________
🌐 Api # 8: ( Generate pytest unit tests as text — does not write files )

📌 route: /tests

👉 methode: post

👉 Query Parameter:
 
👉 Query URL: http://127.0.0.1:8000/tests

👉 Headers:
______________________

Content-Type: application/json
Accept: application/json

_____________________________

👉 api body: ( Template )  
______________________

{
  "repository_name": "portfolio",
  "focus": "auth service"
}

_____________________________

👉 Input attributes:

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `repository_name` | string | yes | Indexed local repo name |
| `focus` | string \| null | no | Optional module/feature to prioritize |

👉 Api output: ( Template )
_____________________________

{
  "repository_name": "portfolio",
  "tests": [
    {
      "module": "tests/test_auth.py",
      "test_code": "import pytest\n\ndef test_login_success():\n    assert True\n",
      "covers": [
        "normal login success",
        "invalid password",
        "missing email"
      ]
    }
  ],
  "missing_coverage": [
    "Token expiry edge case",
    "Rate-limit behavior"
  ],
  "notes": "Generated for guidance only. Review before adding to the repo."
}

_____________________________

👉 Output attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `repository_name` | string | Target repository |
| `tests` | object[] | Generated test modules |
| `tests[].module` | string | Suggested path (e.g. `tests/test_auth.py`) |
| `tests[].test_code` | string | Full pytest source code (text only) |
| `tests[].covers` | string[] | Cases covered |
| `missing_coverage` | string[] | Gaps still likely untested |
| `notes` | string | Extra guidance |

👉 Important:
- Backend **does not** create/modify files in the cloned repository
- Frontend should show copy/download actions if user wants to save tests

👉 Notes for Next.js:
- Render each `test_code` in a syntax-highlighted code block
- Provide “Copy” button per module
- Covers normal, edge, and invalid-input cases when evidence exists in RAG chunks

__________________________________

---

__________________________________
🌐 Api # 9: ( Generate module/function/class documentation and README ideas )

📌 route: /documentation

👉 methode: post

👉 Query Parameter:
 
👉 Query URL: http://127.0.0.1:8000/documentation

👉 Headers:
______________________

Content-Type: application/json
Accept: application/json

_____________________________

👉 api body: ( Template )  
______________________

{
  "repository_name": "portfolio",
  "focus": "api package"
}

_____________________________

👉 Input attributes:

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `repository_name` | string | yes | Indexed local repo name |
| `focus` | string \| null | no | Optional module/area to document |

👉 Api output: ( Template )
_____________________________

{
  "repository_name": "portfolio",
  "module_summary": "This project is a FastAPI backend that exposes repository analysis and AI coding assistance endpoints.",
  "function_descriptions": [
    {
      "name": "analyze_repository",
      "file": "api/repository.py",
      "description": "Clones a GitHub repository and returns structural metadata."
    }
  ],
  "class_descriptions": [
    {
      "name": "RepositoryService",
      "file": "services/repository_service.py",
      "description": "Orchestrates clone + local repository scanning."
    }
  ],
  "readme_improvements": [
    "Add a quickstart section with analyze → index → chat",
    "Document required OpenAI environment variables"
  ],
  "full_documentation": "# Portfolio API\n\n## Overview\n...\n"
}

_____________________________

👉 Output attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `repository_name` | string | Documented repository |
| `module_summary` | string | High-level project/module summary |
| `function_descriptions` | object[] | Function docs |
| `function_descriptions[].name` | string | Function name |
| `function_descriptions[].file` | string | File path |
| `function_descriptions[].description` | string | What it does |
| `class_descriptions` | object[] | Class docs |
| `class_descriptions[].name` | string | Class name |
| `class_descriptions[].file` | string | File path |
| `class_descriptions[].description` | string | What it does |
| `readme_improvements` | string[] | Suggested README upgrades |
| `full_documentation` | string | Full markdown documentation body |

👉 Notes for Next.js:
- Render `full_documentation` with a markdown viewer
- Show function/class tables
- Keep a “Copy Markdown” button
- Does not write README/files to disk

__________________________________

---

# Common Error Responses

Most endpoints return errors in this shape:

```json
{
  "detail": "Human-readable error message"
}
```

Validation errors (invalid JSON / missing fields) may look like:

```json
{
  "detail": "Invalid request payload",
  "errors": []
}
```

## Status code map

| Status | Typical meaning | Frontend action |
|--------|-----------------|-----------------|
| 400 | Invalid input (URL, repository name, empty question) | Show field-level message |
| 403 | Private GitHub repo / access denied | Ask for a public repo |
| 404 | Repo missing locally **or** not indexed | Guide user to Analyze / Index |
| 422 | Empty repo or no supported files to index | Show unsupported-repo state |
| 500 | Server config (e.g. missing `OPENAI_API_KEY`) | Show “server misconfigured” |
| 502 | Git clone / OpenAI / embedding / agent failure | Retry |
| 503 | ChromaDB unavailable | Retry later |

## Prerequisite checklist (for AI endpoints)

Before calling `/chat`, `/review`, `/bugs`, `/improvements`, `/tests`, `/documentation`:

1. `POST /repository/analyze` succeeded
2. `POST /repository/index` succeeded
3. Backend `.env` has a valid `OPENAI_API_KEY`
