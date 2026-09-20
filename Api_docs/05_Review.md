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
