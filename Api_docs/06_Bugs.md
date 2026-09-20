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
