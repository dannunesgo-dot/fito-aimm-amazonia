"""
DEPRECATED — Removido em refactor/phase1 (2026-07-02)

Módulo inicial de conferência.

RAZÃO DA REMOÇÃO:
- Interface mínima; lógica real espalhada em módulos específicos
- Validação de campos obrigatórios já implementada em:
  * src/fito_aimm/pre_diligencia_manual_validator.py
  * src/fito_aimm/aimm_engine.py → validate_inputs()

PLANO PARA FASE 2:
Criar camada genérica de validação:
  src/fito_aimm/validators/
    ├── schema_validator.py
    ├── aimm_validator.py
    └── csv_validator.py
"""

def conferir_campo_obrigatorio(valor, nome_campo: str):
    if valor in (None, "", []):
        return {"campo": nome_campo, "status": "erro", "mensagem": "Campo obrigatório ausente"}
    return {"campo": nome_campo, "status": "ok", "mensagem": "Campo preenchido"}
