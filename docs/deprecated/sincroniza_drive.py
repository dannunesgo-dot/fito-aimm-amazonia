"""
Módulo reservado para sincronização com Google Drive.
A implementação real dependerá da decisão de autenticação:
1) OAuth local para testes; ou
2) Workload Identity Federation / service account para GitHub Actions.
"""
def sincronizar_arquivo(caminho_local: str, pasta_drive: str):
    raise NotImplementedError("Sincronização Drive será implementada na rodada de integração.")
