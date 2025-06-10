# AGENT INSTRUCTIONS for /frontend

## Scope
Rules in this file apply to all JavaScript and related assets in `frontend/`.

## Coding Style
- Use modern ES6+ syntax with modules.
- Terminate statements with semicolons.
- Prefer `const` and `let` over `var`.
- Keep line length under **120 characters**.
- Organize imports at the top of each file.

## Build
After modifying any file in this directory or in `app/static/scss`, run:
```bash
npm install    # run once if node_modules is missing
npm run build
```
This generates bundled files under `app/static/dist/`.
