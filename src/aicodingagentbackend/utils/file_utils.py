"""Filesystem helpers for repository scanning and detection."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

IGNORED_DIR_NAMES: frozenset[str] = frozenset(
    {
        ".git",
        "venv",
        ".venv",
        "node_modules",
        "__pycache__",
        ".idea",
        ".vscode",
        "dist",
        "build",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "eggs",
        ".eggs",
    }
)

LANGUAGE_EXTENSIONS: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".cs": "C#",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "CSS",
    ".sass": "CSS",
    ".json": "JSON",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".md": "Markdown",
    ".markdown": "Markdown",
}

README_NAMES: frozenset[str] = frozenset(
    {"readme", "readme.md", "readme.rst", "readme.txt", "readme.markdown"}
)

LICENSE_NAMES: frozenset[str] = frozenset(
    {
        "license",
        "license.md",
        "license.txt",
        "licence",
        "licence.md",
        "licence.txt",
        "copying",
        "copying.md",
        "copying.txt",
    }
)

REQUIREMENTS_CANDIDATES: tuple[str, ...] = (
    "requirements.txt",
    "requirements-dev.txt",
    "requirements/prod.txt",
    "requirements/base.txt",
    "Pipfile",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "poetry.lock",
    "environment.yml",
    "conda.yml",
)

PYTHON_ENTRY_CANDIDATES: tuple[str, ...] = (
    "main.py",
    "app.py",
    "app/main.py",
    "src/main.py",
    "manage.py",
    "wsgi.py",
    "asgi.py",
    "run.py",
    "server.py",
)

JS_ENTRY_CANDIDATES: tuple[str, ...] = (
    "index.js",
    "index.ts",
    "src/index.js",
    "src/index.ts",
    "src/main.js",
    "src/main.ts",
    "src/app.js",
    "src/app.ts",
    "server.js",
    "server.ts",
    "app.js",
    "app.ts",
)


def should_ignore_dir(name: str) -> bool:
    """Return True if a directory name should be skipped during scanning."""
    if name in IGNORED_DIR_NAMES:
        return True
    return name.endswith(".egg-info")


def iter_repository_paths(root: Path) -> tuple[list[Path], list[Path]]:
    """
    Walk the repository and return (files, folders), skipping ignored directories.

    Both lists contain paths relative to ``root``.
    """
    files: list[Path] = []
    folders: list[Path] = []

    for current_dir, dir_names, file_names in root.walk():
        dir_names[:] = sorted(name for name in dir_names if not should_ignore_dir(name))

        relative_dir = current_dir.relative_to(root)
        if relative_dir != Path("."):
            folders.append(relative_dir)

        for file_name in sorted(file_names):
            files.append(relative_dir / file_name if relative_dir != Path(".") else Path(file_name))

    return files, folders


def detect_languages(files: list[Path]) -> list[str]:
    """Detect programming/markup languages from file extensions, sorted by frequency."""
    counts: Counter[str] = Counter()
    for path in files:
        language = LANGUAGE_EXTENSIONS.get(path.suffix.lower())
        if language:
            counts[language] += 1
    return [language for language, _ in counts.most_common()]


def file_exists_ci(root: Path, relative: str) -> Path | None:
    """Return the matching path if ``relative`` exists (case-insensitive on the leaf name)."""
    candidate = root / relative
    if candidate.is_file():
        return candidate

    parent = candidate.parent
    if not parent.is_dir():
        return None

    target = candidate.name.lower()
    for child in parent.iterdir():
        if child.is_file() and child.name.lower() == target:
            return child
    return None


def find_readme(root: Path, files: list[Path]) -> bool:
    """Return True if a README file exists at the repository root or anywhere."""
    for path in files:
        if path.name.lower() in README_NAMES:
            return True
    return False


def find_license(root: Path, files: list[Path]) -> bool:
    """Return True if a LICENSE file exists."""
    for path in files:
        if path.name.lower() in LICENSE_NAMES:
            return True
    return False


def find_requirements_file(root: Path) -> str | None:
    """Locate the primary dependency manifest, preferring Python requirements.txt."""
    for candidate in REQUIREMENTS_CANDIDATES:
        found = file_exists_ci(root, candidate)
        if found is not None:
            return found.relative_to(root).as_posix()

    package_json = file_exists_ci(root, "package.json")
    if package_json is not None:
        return package_json.relative_to(root).as_posix()

    return None


def detect_python_version(root: Path) -> str | None:
    """Best-effort Python version detection from common metadata files."""
    python_version_file = file_exists_ci(root, ".python-version")
    if python_version_file is not None:
        value = python_version_file.read_text(encoding="utf-8", errors="ignore").strip()
        if value:
            return value.splitlines()[0].strip()

    runtime_file = file_exists_ci(root, "runtime.txt")
    if runtime_file is not None:
        text = runtime_file.read_text(encoding="utf-8", errors="ignore").strip()
        match = re.search(r"python-?([\d.]+)", text, re.IGNORECASE)
        if match:
            return match.group(1)

    pyproject = file_exists_ci(root, "pyproject.toml")
    if pyproject is not None:
        text = pyproject.read_text(encoding="utf-8", errors="ignore")
        match = re.search(
            r'requires-python\s*=\s*["\']([^"\']+)["\']',
            text,
            re.IGNORECASE,
        )
        if match:
            return match.group(1).strip()

    setup_cfg = file_exists_ci(root, "setup.cfg")
    if setup_cfg is not None:
        text = setup_cfg.read_text(encoding="utf-8", errors="ignore")
        match = re.search(r"python_requires\s*=\s*([^\n#]+)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return None


def _read_text(path: Path, limit: int = 200_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def _load_package_json(root: Path) -> dict:
    package_json = file_exists_ci(root, "package.json")
    if package_json is None:
        return {}
    try:
        data = json.loads(_read_text(package_json))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _dependency_blob(root: Path) -> str:
    """Concatenate dependency manifests for framework keyword search."""
    parts: list[str] = []
    for name in (
        "requirements.txt",
        "requirements-dev.txt",
        "Pipfile",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "package.json",
        "pom.xml",
        "go.mod",
        "Cargo.toml",
    ):
        found = file_exists_ci(root, name)
        if found is not None:
            parts.append(_read_text(found).lower())
    return "\n".join(parts)


def _python_imports_blob(root: Path, files: list[Path]) -> str:
    snippets: list[str] = []
    for relative in files:
        if relative.suffix.lower() != ".py":
            continue
        absolute = root / relative
        snippets.append(_read_text(absolute, limit=8_000).lower())
        if len(snippets) >= 40:
            break
    return "\n".join(snippets)


def detect_framework(root: Path, files: list[Path]) -> str | None:
    """
    Detect the primary web/application framework.

    Priority favors more specific frameworks (Next.js before React, FastAPI before Flask).
    """
    package = _load_package_json(root)
    deps: dict = {}
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        section = package.get(key)
        if isinstance(section, dict):
            deps.update({str(k).lower(): str(v) for k, v in section.items()})

    dep_names = set(deps)
    dep_blob = _dependency_blob(root)
    py_blob = _python_imports_blob(root, files)

    if "next" in dep_names or file_exists_ci(root, "next.config.js") or file_exists_ci(
        root, "next.config.mjs"
    ) or file_exists_ci(root, "next.config.ts"):
        return "Next.js"

    if "@angular/core" in dep_names or file_exists_ci(root, "angular.json"):
        return "Angular"

    if "vue" in dep_names or file_exists_ci(root, "vue.config.js") or any(
        path.name == "App.vue" or path.suffix == ".vue" for path in files
    ):
        return "Vue"

    if "react" in dep_names or any(path.suffix.lower() in {".jsx", ".tsx"} for path in files):
        return "React"

    if "express" in dep_names:
        return "Express"

    if (
        "fastapi" in dep_blob
        or "from fastapi" in py_blob
        or "import fastapi" in py_blob
    ):
        return "FastAPI"

    if (
        "django" in dep_blob
        or "from django" in py_blob
        or "import django" in py_blob
        or file_exists_ci(root, "manage.py") is not None
    ):
        return "Django"

    if "flask" in dep_blob or "from flask" in py_blob or "import flask" in py_blob:
        return "Flask"

    return None


def detect_entry_file(root: Path, files: list[Path], framework: str | None) -> str | None:
    """Guess the main application entry file."""
    posix_files = {path.as_posix() for path in files}
    lower_map = {path.as_posix().lower(): path.as_posix() for path in files}

    prioritized: list[str] = []
    if framework in {"FastAPI", "Flask", "Django"}:
        prioritized.extend(PYTHON_ENTRY_CANDIDATES)
    elif framework in {"React", "Next.js", "Express", "Vue", "Angular"}:
        prioritized.extend(JS_ENTRY_CANDIDATES)
    else:
        prioritized.extend(PYTHON_ENTRY_CANDIDATES)
        prioritized.extend(JS_ENTRY_CANDIDATES)

    for candidate in prioritized:
        if candidate in posix_files:
            return candidate
        lowered = candidate.lower()
        if lowered in lower_map:
            return lower_map[lowered]

    skip_parts = {
        "docs",
        "docs_src",
        "doc",
        "examples",
        "example",
        "tests",
        "test",
        "benchmarks",
        "scripts",
        "samples",
        "tutorial",
        "site",
    }

    scored: list[tuple[int, str]] = []
    for path in files:
        parts_lower = {part.lower() for part in path.parts[:-1]}
        if parts_lower & skip_parts:
            continue

        name = path.name.lower()
        if name in README_NAMES or name in LICENSE_NAMES:
            continue

        depth = len(path.parts)
        score = 0
        if name in {"main.py", "app.py", "manage.py", "index.js", "index.ts", "server.js"}:
            score += 10
        elif name.startswith("app.") or name.startswith("main."):
            score += 3
        else:
            continue

        score += max(0, 6 - depth)
        scored.append((score, path.as_posix()))

    if scored:
        scored.sort(key=lambda item: (-item[0], item[1]))
        return scored[0][1]
    return None


def build_tree(root: Path, files: list[Path], folders: list[Path]) -> list[str]:
    """Build a sorted ASCII-like path listing for files and folders."""
    entries: set[str] = set()
    for folder in folders:
        entries.add(folder.as_posix().rstrip("/") + "/")
    for file_path in files:
        entries.add(file_path.as_posix())
    return sorted(entries, key=lambda item: item.replace("\\", "/").lower())


def build_folder_structure(folders: list[Path]) -> list[str]:
    """Return folder paths only, sorted."""
    return sorted((folder.as_posix().rstrip("/") + "/" for folder in folders), key=str.lower)


def largest_files(root: Path, files: list[Path], limit: int = 10) -> list[tuple[str, int]]:
    """Return the largest files as (relative_path, size_bytes)."""
    sized: list[tuple[str, int]] = []
    for relative in files:
        absolute = root / relative
        try:
            size = absolute.stat().st_size
        except OSError:
            continue
        sized.append((relative.as_posix(), size))
    sized.sort(key=lambda item: (-item[1], item[0]))
    return sized[:limit]
