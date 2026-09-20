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
