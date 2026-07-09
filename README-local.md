# README Local — Operação do ambiente (factual)

Este guia descreve a execução local com base nos arquivos confirmados no repositório.

## 1) Arquivos de operação local confirmados

- `run-local.ps1`
- `status-local.ps1`
- `stop-local.ps1`
- `run-tests-local.ps1`
- `Iniciar-API.cmd`
- `Parar-API.cmd`
- `activate-api.ps1`
- `deactivate-api.ps1`
- `app.py`
- `Caddyfile`
- `Caddyfile.local`
- `.env.example`
- `requirements.txt`

## 2) Pré-requisitos locais

- Python instalado (o repositório usa `requirements.txt`)
- PowerShell para scripts `.ps1`
- Caddy disponível no sistema para uso com `Caddyfile`
- Variáveis de ambiente configuradas em `.env` (a partir de `.env.example`)

## 3) Preparação do ambiente

### 3.1 Criar e ativar ambiente virtual
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3.2 Criar `.env` com base no exemplo
```powershell
copy .env.example .env
```

## 4) Execução local (fluxo oficial)

> Comando oficial: `.\run-local.ps1`

```powershell
.\run-local.ps1
```

Verificar estado:
```powershell
.\status-local.ps1
```

Rodar testes locais:
```powershell
.\run-tests-local.ps1
```

Parar serviços:
```powershell
.\stop-local.ps1
```

## 5) Comandos alternativos disponíveis no repositório

- `Iniciar-API.cmd`
- `Parar-API.cmd`
- `python app.py`

> Use alternativas apenas quando necessário para diagnóstico/contingência.

## 6) Verificações operacionais rápidas

### 6.1 Dependências e runtime
```powershell
python --version
pip --version
```

### 6.2 Caddy disponível
```powershell
caddy version
```

### 6.3 Portas de runtime (checagem local)
```powershell
netstat -ano | findstr ":8000"
netstat -ano | findstr ":8080"
```

## 7) Estruturas relevantes para operação

- Logs locais observados no inventário local:
  - `logs/backend.log`, `logs/backend.err.log`, `logs/backend.out.log`
  - `logs/caddy.log`, `logs/caddy.err.log`, `logs/caddy.out.log`
- Diretório temporário:
  - `tmp/teste-api.txt`

## 8) Troubleshooting básico (factual)

### 8.1 Porta ocupada
```powershell
.\stop-local.ps1
```
Depois, reexecute `.\run-local.ps1`.

### 8.2 Ambiente virtual não ativado
```powershell
.\.venv\Scripts\Activate.ps1
```

### 8.3 Dependências ausentes
```powershell
pip install -r requirements.txt
```

### 8.4 Erro de configuração local
- Verifique presença e conteúdo de `.env` (base `.env.example`)
- Verifique disponibilidade do Caddy (`caddy version`)
- Revise logs em `logs/` para backend e gateway

## 9) Referências internas

- `README.md` (mapa geral)
- `README_operacional.md` (documentação operacional adicional)
- `scripts/test_api_integration.ps1`
- `scripts/worldbank_examples.ps1`
