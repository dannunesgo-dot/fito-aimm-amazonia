"""
DEPRECATED — Removido em refactor/phase1 (2026-07-02)

Módulo inicial de busca e coleta.
Versão: v0.1
Observação: conectores reais foram implementados por fonte em rodadas posteriores.

RAZÃO DA REMOÇÃO:
- Interface vazia; nunca utilizada
- Funcionalidade substituída por coletores especializados:
  * src/fito_aimm/coletor_mapaosc.py
  * src/fito_aimm/coletor_ibge.py
  * src/fito_aimm/coletor_ibge_geociencias.py

REFERÊNCIA DE IMPLEMENTAÇÃO:
Veja src/fito_aimm/coletor_mapaosc.py para exemplo de coletor real
com retry, normalização e logging.
"""

from dataclasses import dataclass

@dataclass
class ResultadoBusca:
    id_fonte: str
    consulta: str
    url: str
    titulo: str
    status: str

def registrar_consulta(id_fonte: str, consulta: str, url: str, titulo: str = "") -> ResultadoBusca:
    return ResultadoBusca(id_fonte=id_fonte, consulta=consulta, url=url, titulo=titulo, status="registrada")
