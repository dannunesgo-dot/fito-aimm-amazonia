from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path("src").resolve()))

import fito_aimm.api.routes as routes
from fito_aimm.api.routes import PORTAL_JS, PORTAL_JSON, build_portal_payload
from fito_aimm.projects import ProjectRepository


def test_interface_url_prefers_explicit_pages_url(monkeypatch) -> None:
    monkeypatch.setenv("GITHUB_PAGES_URL", "https://example.com/custom")
    monkeypatch.setenv("GITHUB_REPOSITORY", "ignored/repo")

    assert routes.interface_url() == "https://example.com/custom/"


def test_interface_url_builds_from_repository_env(monkeypatch) -> None:
    monkeypatch.delenv("GITHUB_PAGES_URL", raising=False)
    monkeypatch.setenv("GITHUB_REPOSITORY", "octo/demo")

    assert routes.interface_url() == "https://octo.github.io/demo/"


def test_interface_url_falls_back_to_git_remote(monkeypatch) -> None:
    monkeypatch.delenv("GITHUB_PAGES_URL", raising=False)
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    monkeypatch.setattr(routes, "_repository_slug_from_git", lambda: "git-owner/git-repo")

    assert routes.interface_url() == "https://git-owner.github.io/git-repo/"


def test_build_portal_payload_generates_full_demo() -> None:
    payload = build_portal_payload(reset_demo=True)

    assert payload["metadata"]["titulo"] == "Fito+ Amazônia AIMM"
    assert len(payload["projetos"]) >= 2
    assert payload["projeto_destaque"]["versoes"]
    assert payload["comparacao_destaque"]["dimensoes"]
    assert payload["links"]["interface_otimizada"].startswith("https://")
    assert payload["links"]["interface_otimizada"].endswith("/fito-aimm-amazonia/")

    json_payload = json.loads(PORTAL_JSON.read_text(encoding="utf-8"))
    assert json_payload["metadata"]["titulo"] == payload["metadata"]["titulo"]
    assert json_payload["links"]["interface_otimizada"] == payload["links"]["interface_otimizada"]

    js_payload = PORTAL_JS.read_text(encoding="utf-8")
    assert js_payload.startswith("window.FITO_PORTAL_DATA = ")
    assert '"interface_otimizada"' in js_payload


def test_project_history_and_pdf_are_available() -> None:
    build_portal_payload(reset_demo=True)
    repository = ProjectRepository()
    project = max(repository.list_projects(), key=lambda item: len(item.versoes))

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
