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
