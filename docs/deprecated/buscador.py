"""
Módulo inicial de busca e coleta.
Versão: v0.1
Observação: conectores reais serão implementados por fonte em rodadas futuras.
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
