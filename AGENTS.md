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
    - `pypew.js` — shared frontend helpers loaded on every page (tooltips, print buttons, navbar active state, toasts)
    - `feastList.js`, `serviceForm.js`, `pewSheet.js` — per-page behaviour
    - `styles.css` — app styles; `bootstrap*`, `favicon_io/` are vendored, do not edit
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

### Frontend (JS/CSS/templates)

There is no JS toolchain — no npm, bundler, transpiler, linter or test runner. Assets are served as-is by Flask from `src/pypew/static/` via `url_for('static', ...)`. Keep it that way unless explicitly asked.

- **No inline `<script>` or `<style>` in templates.** Templates render markup and data only. All JS lives in `src/pypew/static/*.js`; app CSS lives in `styles.css`.
- **Never interpolate Jinja into script source.** Pass server values to JS via `data-*` attributes on an element, then read them with `elem.dataset.*`. For URLs, put a `url_for` template in a data attribute and substitute a placeholder (`slug='__slug__'` → `.replace('__slug__', slug)`). This keeps `url_for` (and therefore `SCRIPT_NAME`/`APPLICATION_ROOT`) authoritative. Note that HTML autoescaping is *not* sufficient protection here — it is the wrong escaping for a JS context (a `<script>` body does not decode entities, so `&#34;` stays literal and protects nothing), and newlines are not escaped at all, so a value containing one terminates the string literal and kills the whole script block. Use `data-*` regardless of whether a value is currently trusted.
- **Loading**: vendor scripts first (e.g. `bootstrap.bundle.min.js`), then `pypew.js`, then page scripts. All are `defer`red, which guarantees DOM-readiness and document-order execution — so page scripts can rely on `bootstrap` and `window.pypew` existing. Page scripts belong in `{% block scripts %}` of the template that extends `base.html` (not in the `{% include %}`d partial), which is what keeps that ordering intact.
- **Module shape**: wrap each file in an IIFE with `"use strict"`, look up your root element first and `return` early if it's absent. This makes a script safe to load on any page and avoids `TypeError`s on `null`.
- **Shared behaviour goes in `pypew.js`** (exposed as `window.pypew`), not in a new global. Use `pypew.addTooltip` + `pypew.initTooltips` for tooltips, `.js-print` class for print buttons, and `pypew.toast` for toasts. `initTooltips` is idempotent, so it is safe to call after injecting new elements.
- **Data attributes for configuration** should live on the container element the script already needs, named `data-<kebab-name>` in the template and camelCased on `dataset` in JS. Keep element IDs in JS and HTML in sync; if you derive an ID, keep the mapping table explicit rather than relying on case matching.
- **Progressive enhancement**: prefer a server-side default (e.g. a WTForms `default=`) over JS that sets a field value on load. Keep Bootstrap toast styles and behaviour — `pypew.toast` creates its own toast container at runtime. No external toast CSS is loaded.
- **Vendored assets** (`bootstrap*`, `favicon_io/`) are do-not-edit. Note `notify.js`/`notify.css` (unminified) are the ones actually loaded; there is no minified variant in the tree.
- **Formatting**: 2-space indent, double quotes, semicolons, trailing commas in multi-line literals.
- **Verification**: there is no JS linter, so after touching JS run `node --check <file>` if `node` is available, then `uv run python -m unittest`. Smoke-test that pages render (`app.test_client()`), that every `getElementById`/dataset read in a script resolves against the HTML of the pages that load it, and that `defer` ordering still holds.

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
- **No frontend tests exist.** There is no JS test runner. Cover frontend changes by rendering pages through `app.test_client()` and asserting on the HTML, not by adding a JS harness.

### Data & packaging
- **Bundled data**: Runtime data lives under `src/pypew/data/`. `neh.csv` is tracked and must remain bundled (Hatch forces it into wheel/sdist artifacts).
- **Git hygiene**: Respect `.gitignore`. Do not commit secrets/keys (e.g. `.env`). Do not commit build artifacts (`build/`, `dist/`, `*.egg-info/`, caches).
- **Editable/source runs**: `uv run pypew`, `uv run python -m pypew`, `uv run gunicorn pypew.wsgi:app`. Debug with `--debug`, suppress browser with `--no-launch`.

### Working practices
- **Edit existing files**; create new files only if explicitly required.
- **Keep changes minimal and focused.** Avoid broad refactors unless necessary.
- **References**: When referencing code, include `file_path:line_number` (e.g. `src/pypew/models.py:123`) to help navigation.
- **Commit policy**: Never commit unless explicitly asked. Inspect `git status/diff` and stage only intended files.
- **Git workflow**: This repository has branch protection on `main`. **You cannot push directly to `main`**. You must push changes to a side branch and open a pull request (PR). Agents may merge PRs as soon as they pass CI.
- **Local vs installed package**: Source lives in `src/pypew/`; imports should resolve from the package (src layout). The root `views/` is not part of the installed package.
