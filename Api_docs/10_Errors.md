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
