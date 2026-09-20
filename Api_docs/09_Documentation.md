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
