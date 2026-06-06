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

## LLM Provider

The backend defaults to `FakeProvider` so the demo path runs without a real API
key. To switch the AI layer to DeepSeek, set these environment variables before
starting FastAPI and install the optional DeepSeek transport:

```powershell
pip install -e "backend[deepseek]"
$env:XENGINEER_AI_PROVIDER = "deepseek"
$env:DEEPSEEK_API_KEY = "<your-deepseek-api-key>"
$env:XENGINEER_DEEPSEEK_MODEL = "deepseek-v4-flash"
$env:DEEPSEEK_BASE_URL = "https://api.deepseek.com"
$env:XENGINEER_LLM_TIMEOUT_SECONDS = "60"
```

Check the provider boundary directly:

```powershell
# from the repository root
python scripts\check_llm_provider.py --provider fake
python scripts\check_llm_provider.py --provider deepseek --model deepseek-v4-flash
```

## Source Of Truth

Internal truth is JSON/Pydantic. YAML is an export and editable interchange
format.
