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
