# Módulos Deprecated (Obsoletos)

Este diretório contém módulos que foram removidos da arquitetura ativa.

## Motivos da Deprecação

### `buscador.py`
- **Status:** Interface vazia; conectores reais nunca implementados
- **Razão:** Funcionalidade substituída por coletores especializados (`coletor_mapaosc.py`, `coletor_ibge.py`, etc.)
- **Data de Deprecação:** 2026-07-02
- **Arquivado em:** `docs/deprecated/buscador.py`

### `extrator.py`
- **Status:** Uma única função trivial não usada
- **Razão:** Lógica de extração distribuída nos coletores específicos
- **Data de Deprecação:** 2026-07-02
- **Arquivado em:** `docs/deprecated/extrator.py`

### `conferidor.py`
- **Status:** Interface mínima; lógica real em módulos específicos
- **Razão:** Validação movida para `pre_diligencia_manual_validator.py` e futuro `validators/` genérico
- **Data de Deprecação:** 2026-07-02
- **Arquivado em:** `docs/deprecated/conferidor.py`

### `sincroniza_drive.py`
- **Status:** Placeholder com `NotImplementedError`
- **Razão:** Drive API real implementada em scripts operacionais; será movida para módulo `drive_sync.py` em fase posterior
- **Data de Deprecação:** 2026-07-02
- **Arquivado em:** `docs/deprecated/sincroniza_drive.py`

## Migração para Fase 2

Na **Fase 2 (Refatoração Arquitetural)**, será criado:
- `src/fito_aimm/validators/` — com validadores genéricos
- `src/fito_aimm/drive_sync/` — para sincronização com Drive

Esses novos módulos **não** serão baseados em código deprecated; serão reescritos do zero com testes e documentação.

## Referência Histórica

Para consultar implementações antigas, ver commits:
- Remocção de `buscador.py`: Branch refactor/phase1
- Remocção de `extrator.py`: Branch refactor/phase1
- etc.
