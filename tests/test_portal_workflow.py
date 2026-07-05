from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path("src").resolve()))

from fito_aimm.api.routes import PORTAL_JS, PORTAL_JSON, build_portal_payload
from fito_aimm.projects import ProjectRepository


def test_build_portal_payload_generates_full_demo() -> None:
    payload = build_portal_payload(reset_demo=True)

    assert payload["metadata"]["titulo"] == "Fito+ Amazônia AIMM"
    assert len(payload["projetos"]) >= 2
    assert payload["projeto_destaque"]["versoes"]
    assert payload["comparacao_destaque"]["dimensoes"]

    json_payload = json.loads(PORTAL_JSON.read_text(encoding="utf-8"))
    assert json_payload["metadata"]["titulo"] == payload["metadata"]["titulo"]

    js_payload = PORTAL_JS.read_text(encoding="utf-8")
    assert js_payload.startswith("window.FITO_PORTAL_DATA = ")


def test_project_history_and_pdf_are_available() -> None:
    build_portal_payload(reset_demo=True)
    repository = ProjectRepository()
    project = repository.list_projects()[0]

    assert len(project.versoes) >= 2
    latest = project.versoes[-1]
    assert latest.status in {"Aprovado", "Aprovado condicionalmente"}
    assert latest.hash_documento
    assert latest.pdf_path
    assert Path(latest.pdf_path).exists()
    assert Path(latest.pdf_path).read_bytes().startswith(b"%PDF")

    diff = repository.compare_versions(project.id_projeto, 1, latest.numero_versao)
    assert "score_geral" in diff
    assert diff["dimensoes"]
