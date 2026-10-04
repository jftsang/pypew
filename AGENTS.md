# AGENTS.md

Guidance for coding agents working on the PyPew repository.

## Repository overview

PyPew is a Flask web app for generating Anglican pew sheets from Book of Common Prayer texts. It assembles service details (date/feast, hymns, clergy names, etc.) into a web page or `.docx` export.

- **Package**: `pypew` (console script `pypew` → `pypew.app:main`)
- **Runtime**: Python 3.12+ (Flask 2.x, WTForms, Jinja2, Flask-Pydantic)
- **Build/packaging**: [Hatchling](https://hatch.pypa.io/) (wheel/sdist). PyInstaller used for desktop binaries.
- **Dependency/env management**: [uv](https://docs.astral.sh/uv/) (`uv.lock`, `pyproject.toml`)
- **Versioning**: `hatch.version` reads from `src/pypew/__init__.py` (`__version__`)

## Package structure

- `src/pypew/` — installed package
  - `__init__.py` — package metadata/version
  - `__main__.py` — `python -m pypew` entry
  - `app.py` — Flask app factory/CLI entry (`main()`)
  - `wsgi.py` — WSGI app (`app`) for gunicorn
  - `models.py`, `models_base.py` — liturgical models and logic
  - `views/` — route handlers (Flask views/blueprints)
  - `forms.py` — WTForms forms
  - `filters.py` — Jinja template filters
  - `dateexpr.py` — date/feast expression parsing
  - `utils.py` — utilities
  - `paths.py` — filesystem/resource paths
  - `templates/` — Jinja2 templates (bundled)
  - `static/` — CSS/JS/assets (bundled)
  - `data/` — bundled data files (e.g. `neh.csv`, feast data). Tracked CSVs here are required at runtime and are explicitly included in wheels/sdist by hatch.
- `tests/` — unittest-based tests
  - `test_pypew.py`, `test_dateexpr.py`
  - `feast_dates.json` — test fixtures/data
- `scripts/` — development helper scripts (not installed with the package). Install with `uv sync --extra scripts` if needed.
- `deploy/` — deployment helpers (e.g. `deploy/srcf.sh`)
- `views/` — root-level views directory (separate from `src/pypew/views/`); treat as repository artifacts, not part of the installed package.
- Top-level build/packaging: `pyproject.toml`, `uv.lock`, `build.sh`, `build.bat`, `pypew.spec`, `wsgi.spec`, `.python-version`, `.env` (local config, not committed).

## Conventions to observe

### Code style & linting
- **Line length**: 88 (Ruff)
- **Target Python**: 3.12
- **Formatter/linter**: [Ruff](https://docs.astral.sh/ruff/). Configured in `pyproject.toml` under `[tool.ruff]`.
- **Lint**: `uv run ruff check .`
- **Format**: `uv run ruff format .`
- **Imports**: follow Ruff isort rules (`known-first-party = ["pypew"]`, src layout). Prefer absolute imports within the package.
- **Comments**: **do not add comments unless explicitly asked.** Preserve existing comments/markers.
- **Ruff ignores**: Many rules are explicitly ignored in `pyproject.toml` with `# FIXME(<CODE>)` markers. Do not remove/“fix” these ignores unless explicitly instructed; the codebase has deliberate style choices tied to them.
- **Codebase consistency**: Mimic existing patterns, naming, error handling style, and library choices. When editing, read surrounding context (especially imports) first.

### Dependencies
- Managed with `uv`. Install/runtime deps in `pyproject.toml` dependencies; dev in `[dependency-groups].dev` (includes `ruff`, `parameterized`, `pandas`); build in `[dependency-groups].build` (`pyinstaller>=6`).
- Optional extras: `hymns` (pandas), `scripts` (pandas, python-slugify).
- **Do not assume a library exists** unless it’s used in the codebase or declared. Check `pyproject.toml`/neighboring code before introducing new deps.

### Testing
- **Framework**: Python `unittest` (no pytest configured). Tests use `parameterized` for parametrization.
- **Run all tests**: `uv run python -m unittest` (from repo root)
- **Test discovery**: standard unittest discovery in `tests/`.
- **Adding tests**: Follow existing test style in `tests/test_pypew.py` and `tests/test_dateexpr.py`. Use fixtures like `tests/feast_dates.json` when applicable.
- **Verification**: After code changes, run tests. Also run lint/typecheck via ruff (`check`/`format`) as appropriate. If you cannot find the correct verification command, ask.

### Data & packaging
- **Bundled data**: Runtime data lives under `src/pypew/data/`. `neh.csv` is tracked and must remain bundled (Hatch forces it into wheel/sdist artifacts).
- **Git hygiene**: Respect `.gitignore`. Do not commit secrets/keys (e.g. `.env`). Do not commit build artifacts (`build/`, `dist/`, `*.egg-info/`, caches).
- **Editable/source runs**: `uv run pypew`, `uv run python -m pypew`, `uv run gunicorn pypew.wsgi:app`. Debug with `--debug`, suppress browser with `--no-launch`.

### Working practices
- **Edit existing files**; create new files only if explicitly required.
- **Keep changes minimal and focused.** Avoid broad refactors unless necessary.
- **References**: When referencing code, include `file_path:line_number` (e.g. `src/pypew/models.py:123`) to help navigation.
- **Commit policy**: Never commit unless explicitly asked. Inspect `git status/diff` and stage only intended files.
- **Local vs installed package**: Source lives in `src/pypew/`; imports should resolve from the package (src layout). The root `views/` is not part of the installed package.
