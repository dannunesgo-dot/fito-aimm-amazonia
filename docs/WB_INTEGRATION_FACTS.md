# World Bank Integration — Factual Verification

## Dados de entrada
- Evidência: `app.py` (linhas 28-320), `run-local.ps1` (linhas 166-178), `.github/workflows/`
- Data: 2026-07-10
- Método: grep + código-fonte + teste

---

## API World Bank Ativa

### Configuração
- **URL base:** `https://api.worldbank.org/v2` (default em `app.py:28`)
- **Overrides:** `WORLDBANK_API_URL` env var
- **Parser:** custom `parse_worldbank_response()` em `app.py:46`

### Rotas implementadas

#### 1) GET `/worldbank/countries`
