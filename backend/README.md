# XEngineer Backend

V0+V1 backend skeleton for the structured novel-to-screenplay workbench.

The current files define contracts and call boundaries. They are intentionally
thin until the implementation plan starts.

## Architecture

- FastAPI routes in `app/api/`
- Pydantic domain models in `app/domain/`
- SQLite/repository boundary in `app/db/` and `app/repositories/`
- AI provider and skill wrappers in `app/ai/`
- Deterministic validators in `app/validators/`
- Orchestration services in `app/services/`
- Background task wrapper in `app/workers/`
- YAML/schema export in `app/exporters/`

## Source Of Truth

Internal truth is JSON/Pydantic. YAML is an export and editable interchange
format.

