"""
DEPRECATED — Removido em refactor/phase1 (2026-07-02)

Módulo reservado para sincronização com Google Drive.

RAZÃO DA REMOÇÃO:
- Apenas placeholder com NotImplementedError
- Drive API real já implementada em scripts operacionais:
  * scripts/rodada_4_31_drive_api_real_test.py
  * scripts/rodada_4_31b_drive_api_oauth_real_test.py
  * scripts/rodada_4_32_aimm_minimum_integrated_pipeline.py

PLANO PARA FASE 2:
Criar módulo produção-ready:
  src/fito_aimm/drive_sync/
    ├── __init__.py
    ├── auth.py (OAuth + Workload Identity)
    ├── uploader.py (upload de arquivos)
    └── downloader.py (download de dados)

Com:
- Logging estruturado
- Retry com backoff
- Testes unitários
- Documentação de API
"""

def sincronizar_arquivo(caminho_local: str, pasta_drive: str):
    raise NotImplementedError("Sincronização Drive será implementada na rodada de integração.")
