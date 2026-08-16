# AGENTS.md

FastAPI backend for a laser-cutting quote system (DXF upload → geometry analysis → price → 3D preview → Wompi payment). Python 3.14, no ORM, no CI, no linter configured.

## Environment & commands

- **The repo root IS the virtualenv** (`bin/`, `lib/`, `pyvenv.cfg` at top level, gitignored). Use `bin/python`, `bin/pytest`, `bin/uvicorn` directly — do not create `.venv/` or run system `pip`.
- Run server: `bin/uvicorn main:app --reload` (Swagger at `/docs`; all routes are under `/api`).
- Tests: `bin/pytest` (whole suite, ~2s, ~220 tests). Single test: `bin/pytest tests/unit/test_security.py::TestClass::test_name`. Coverage: `bin/pytest --cov=src --cov-report=html`.
- **`.env` is required even to run tests**: `main.py` reads `ORIGIN` and `JWT_KEY` at import time via the `Environment` singleton, which raises on missing vars. Copy `.env.example` → `.env`. Full var list: `src/utils/enums/__init__.py` (`EnvironmentsEnum`).

## Architecture

- Entry: `main.py` → routers aggregated in `src/__init__.py` with prefix `/api`. **New router modules must be registered there.**
- Module convention (follow it when adding features):
  - `src/<Module>/__init__.py` **is** the `APIRouter` (e.g. `UserModule/__init__.py`).
  - Service in `<Module>/<Name>Service.py`, exposed via a `get_*_service()` `@lru_cache` provider injected with FastAPI `Depends`.
  - Pydantic DTOs all live in `dtos/__init__.py`; SQL + error enums in `enums/__init__.py`.
- DB: `src/utils/PostgresClient.py` (asyncpg pool) runs **raw SQL strings stored in enums**. Writes call Postgres stored procedures with a JSON payload (`save`/`update` pass `dumps(data)` + id). Tables/procedures (`"USER"."TB_USU_USERS"`, `SP_USU_USERPKG_*`) live in the DB, not in this repo — no migrations here.
- Auth: JWT via `HTTPBearer`. Reuse `get_current_user` / `get_current_admin_user` from `src/UserModule/__init__.py` (other modules import them from there).
- `src/CmrModule` has **no router** — it's a Bitrix24 CRM client service used by `UserService`.
- FileModule pipeline: ezdxf/shapely/geopandas analysis (`geometriesAnalyzer.py`, `geometryAnalyzerCreator.py`) → `costCalculator.py` → exporters (`exporters/`: OBJ/GLB/GLTF/image via trimesh+matplotlib) → Google Cloud Storage via `storageWrapper.py`.

## Testing conventions

- `pytest.ini` sets `asyncio_mode = auto` — async tests need no marker/plugin boilerplate.
- Everything external (Postgres, GCS, SMTP, Wompi, CRM) is mocked; tests need **no DB or network**.
- Router tests use `app.dependency_overrides[...]` and must `app.dependency_overrides.clear()` in a `finally` (see `tests/integration/test_routers.py`); shared fixtures in `tests/conftest.py`.
- Geometry test fixture: `tests/shapes/polygons.txt`.

## Gotchas

- Naming is inconsistent across the codebase — keep existing spellings when extending: `autentification` (sic), `PaymentModule/dto` vs `dtos` elsewhere, env vars `WOMPY_*` vs file `wompiWrapper.py`.
- User-facing strings, error messages, and commit history are in **Spanish**; match that for API messages.
- `src/FileModule/credenciales/credentials.json` is a **real GCP service-account key committed to git**; `GOOGLE_APPLICATION_CREDENTIALS` points at it. Don't delete or casually rotate it.
- VS Code runs Pylance in `strict` mode (`.vscode/settings.json`); the codebase silences third-party stubs with `# type: ignore` — match that style rather than adding config.
