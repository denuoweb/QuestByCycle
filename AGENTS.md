# AGENT INSTRUCTIONS

## Scope
These instructions apply to the entire repository except where overridden by a nested `AGENTS.md` file.

## Repository Overview
This project, QuestByCycle, is a Flask based web application with a Node/Vite
frontend.  Python packages are managed via `pyproject.toml`.  Tests are located
in the `tests/` directory and use `pytest`.  Documentation lives in `docs/`.

## Coding Guidelines
- Use **Python 3.11** features.
- Follow PEP 8 style with 4 space indents.
- Keep line length under **120 characters**.
- Prefer double quotes for strings unless single quotes improve readability.
- Document all functions and classes with docstrings.
- Organize imports in three groups: standard library, third party, project.
- For JavaScript/ES modules keep semicolons and prefer `const`/`let`.
- When editing SCSS or JS, run the Vite build to ensure no compilation errors.

## Testing Instructions
1. Install dependencies with `pip install -r requirements.txt` if available
   or `pip install -e .` (in non-package mode use `pip install flask ...`).
2. Run the test suite from the repository root with:
   ```bash
   PYTHONPATH="$PWD" pytest
   ```
   All tests should pass. If tests fail, investigate and fix them or document why
   the failure is expected.

## Commit Guidelines
- Make small, focused commits with descriptive messages.
- Describe *why* a change is made, not just *what* changed.
- Run tests before each commit.

## Documentation
Update the Markdown files in `docs/` when code changes affect user or developer
behavior. Follow the style described in `docs/AGENTS.md`.

## Frontend
The `frontend/` directory contains modern JS that is bundled using Vite. After
modifying any JS or SCSS, run:
```bash
npm install   # only once
npm run build
```
Ensure the build succeeds before committing.
