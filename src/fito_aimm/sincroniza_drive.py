"""
Conector reutilizável para Google Drive.

Suporta dois modos de autenticação:
1. Service Account — variável de ambiente ``GOOGLE_SERVICE_ACCOUNT_JSON``
   com o conteúdo JSON da chave de serviço; indicado para GitHub Actions.
2. OAuth local — arquivo de token ``token.json`` + credenciais
   ``credentials.json``; indicado para desenvolvimento local.

Dependências: google-api-python-client, google-auth-oauthlib, google-auth-httplib2
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

try:
    from google.oauth2 import service_account
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
    _GOOGLE_OK = True
except ImportError:  # pragma: no cover
    _GOOGLE_OK = False

SCOPES = ["https://www.googleapis.com/auth/drive"]

_ENV_SA_JSON = "GOOGLE_SERVICE_ACCOUNT_JSON"
_ENV_SA_FILE = "GOOGLE_SERVICE_ACCOUNT_FILE"
_OAUTH_TOKEN_FILE = Path("token.json")
_OAUTH_CREDENTIALS_FILE = Path("credentials.json")


def _verificar_dependencias() -> None:
    if not _GOOGLE_OK:
        raise ImportError(
            "Dependências Google Drive não instaladas. "
            "Execute: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"
        )


def _autenticar_service_account() -> Any:
    """Autentica via service account JSON (env var ou arquivo)."""
    sa_json = os.getenv(_ENV_SA_JSON, "").strip()
    sa_file = os.getenv(_ENV_SA_FILE, "").strip()

    if sa_json:
        info = json.loads(sa_json)
        creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        return creds

    if sa_file and Path(sa_file).exists():
        creds = service_account.Credentials.from_service_account_file(sa_file, scopes=SCOPES)
        return creds

    return None


def _autenticar_oauth() -> Any:
    """Autentica via OAuth2 com arquivo de token local."""
    creds = None

    if _OAUTH_TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(_OAUTH_TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif _OAUTH_CREDENTIALS_FILE.exists():
            flow = InstalledAppFlow.from_client_secrets_file(
                str(_OAUTH_CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)
        else:
            raise FileNotFoundError(
                f"Arquivo de credenciais OAuth não encontrado: {_OAUTH_CREDENTIALS_FILE}. "
                "Baixe em Google Cloud Console > APIs & Services > Credentials."
            )

        _OAUTH_TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return creds


def _construir_servico() -> Any:
    """Constrói o cliente Drive autenticado."""
    _verificar_dependencias()

    creds = _autenticar_service_account()
    if creds is None:
        creds = _autenticar_oauth()

    return build("drive", "v3", credentials=creds, cache_discovery=False)


def sincronizar_arquivo(caminho_local: str | Path, pasta_drive: str) -> dict[str, str]:
    """Faz upload de um arquivo local para uma pasta do Google Drive.

    Se o arquivo já existir na pasta (mesmo nome), é atualizado (update);
    caso contrário, é criado (create).

    Args:
        caminho_local: Caminho do arquivo no sistema de arquivos local.
        pasta_drive: ID da pasta de destino no Google Drive.

    Returns:
        Dicionário com ``id``, ``name`` e ``webViewLink`` do arquivo no Drive.
    """
    caminho = Path(caminho_local)
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    service = _construir_servico()
    nome = caminho.name

    # Verifica se já existe arquivo com mesmo nome na pasta
    resultado = (
        service.files()
        .list(
            q=f"name='{nome}' and '{pasta_drive}' in parents and trashed=false",
            fields="files(id,name)",
            spaces="drive",
        )
        .execute()
    )
    arquivos = resultado.get("files", [])

    media = MediaFileUpload(str(caminho), resumable=True)
    campos = "id,name,webViewLink"

    if arquivos:
        file_id = arquivos[0]["id"]
        arquivo_atualizado = (
            service.files()
            .update(fileId=file_id, media_body=media, fields=campos)
            .execute()
        )
        return arquivo_atualizado
    else:
        metadados = {"name": nome, "parents": [pasta_drive]}
        arquivo_criado = (
            service.files()
            .create(body=metadados, media_body=media, fields=campos)
            .execute()
        )
        return arquivo_criado


def listar_arquivos_pasta(
    pasta_drive_id: str,
    tipos_mime: list[str] | None = None,
    max_resultados: int = 100,
) -> list[dict[str, str]]:
    """Lista arquivos em uma pasta do Google Drive.

    Args:
        pasta_drive_id: ID da pasta no Google Drive.
        tipos_mime: Lista de MIME types para filtrar (opcional).
        max_resultados: Número máximo de resultados.

    Returns:
        Lista de dicionários com ``id``, ``name``, ``mimeType`` e ``modifiedTime``.
    """
    service = _construir_servico()
    query = f"'{pasta_drive_id}' in parents and trashed=false"

    if tipos_mime:
        mime_filtros = " or ".join(f"mimeType='{m}'" for m in tipos_mime)
        query += f" and ({mime_filtros})"

    resultado = (
        service.files()
        .list(
            q=query,
            fields="files(id,name,mimeType,modifiedTime,size)",
            pageSize=min(max_resultados, 1000),
        )
        .execute()
    )
    return resultado.get("files", [])


def baixar_arquivo(file_id: str, destino_local: str | Path) -> Path:
    """Baixa um arquivo do Google Drive para o sistema local.

    Args:
        file_id: ID do arquivo no Google Drive.
        destino_local: Caminho de destino no sistema local.

    Returns:
        Caminho do arquivo baixado.
    """
    destino = Path(destino_local)
    destino.parent.mkdir(parents=True, exist_ok=True)
    service = _construir_servico()

    requisicao = service.files().get_media(fileId=file_id)
    with destino.open("wb") as f:
        downloader = MediaIoBaseDownload(f, requisicao)
        concluido = False
        while not concluido:
            _, concluido = downloader.next_chunk()

    return destino


def criar_pasta_se_nao_existir(
    nome: str,
    parent_id: str | None = None,
) -> str:
    """Cria uma pasta no Google Drive se ela não existir.

    Args:
        nome: Nome da pasta a criar.
        parent_id: ID da pasta pai (opcional; raiz do Drive se omitido).

    Returns:
        ID da pasta (existente ou recém-criada).
    """
    service = _construir_servico()
    query = f"name='{nome}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    resultado = service.files().list(q=query, fields="files(id,name)").execute()
    pastas = resultado.get("files", [])
    if pastas:
        return pastas[0]["id"]

    metadados: dict[str, Any] = {
        "name": nome,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        metadados["parents"] = [parent_id]

    pasta = service.files().create(body=metadados, fields="id").execute()
    return pasta["id"]


def obter_metadados_arquivo(file_id: str) -> dict[str, str]:
    """Retorna metadados de um arquivo no Google Drive.

    Args:
        file_id: ID do arquivo no Google Drive.

    Returns:
        Dicionário com ``id``, ``name``, ``mimeType``, ``size``, ``modifiedTime`` e ``webViewLink``.
    """
    service = _construir_servico()
    return (
        service.files()
        .get(fileId=file_id, fields="id,name,mimeType,size,modifiedTime,webViewLink")
        .execute()
    )
