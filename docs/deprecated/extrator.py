"""
Módulo inicial de extração.
Extrai metadados e valores de respostas já baixadas.
"""
def extrair_valor_simples(registro: dict, campo: str):
    return registro.get(campo)
