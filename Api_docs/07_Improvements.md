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
