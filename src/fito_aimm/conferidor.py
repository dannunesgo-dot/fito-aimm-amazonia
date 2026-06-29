"""
Módulo inicial de conferência.
"""
def conferir_campo_obrigatorio(valor, nome_campo: str):
    if valor in (None, "", []):
        return {"campo": nome_campo, "status": "erro", "mensagem": "Campo obrigatório ausente"}
    return {"campo": nome_campo, "status": "ok", "mensagem": "Campo preenchido"}
