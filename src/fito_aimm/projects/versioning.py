from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from fito_aimm.audit import hash_snapshot
from fito_aimm.models import AuditEvent, ProjectCreateRequest, ProjectRecord, ProjectVersion
from fito_aimm.utils import iso_now_utc, slugify


DEFAULT_PROJECTS_DIR = Path("outputs/app/projects")


class ProjectRepository:
    def __init__(self, base_dir: Path = DEFAULT_PROJECTS_DIR):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _project_path(self, project_id: str) -> Path:
        return self.base_dir / f"{project_id}.json"

    def list_projects(self) -> list[ProjectRecord]:
        projects: list[ProjectRecord] = []
        for path in sorted(self.base_dir.glob("*.json")):
            projects.append(ProjectRecord.model_validate_json(path.read_text(encoding="utf-8")))
        return sorted(projects, key=lambda item: item.atualizado_em, reverse=True)

    def get_project(self, project_id: str) -> ProjectRecord:
        path = self._project_path(project_id)
        if not path.exists():
            raise FileNotFoundError(f"Projeto não encontrado: {project_id}")
        return ProjectRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def save_project(self, project: ProjectRecord) -> ProjectRecord:
        project.atualizado_em = iso_now_utc()
        self._project_path(project.id_projeto).write_text(
            project.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return project

    def create_project(self, request: ProjectCreateRequest) -> ProjectRecord:
        normalized_name = request.nome_projeto.strip().lower()
        normalized_email = request.tecnico_responsavel_email.strip().lower()
        for existing in self.list_projects():
            if (
                existing.nome_projeto.strip().lower() == normalized_name
                and existing.tecnico_responsavel_email.strip().lower() == normalized_email
            ):
                raise ValueError("Já existe um projeto com este nome para o mesmo responsável técnico.")

        created_at = iso_now_utc()
        slug = slugify(request.nome_projeto)
        project_id = f"PRJ_{created_at.strftime('%Y%m%d%H%M%S')}_{slug[:24]}"
        project = ProjectRecord(
            id_projeto=project_id,
            slug=slug,
            nome_projeto=request.nome_projeto,
            descricao=request.descricao,
            territorios=request.territorios,
            especies_produtos=request.especies_produtos,
            investimento_previsto_brl=request.investimento_previsto_brl,
            faixa_beneficiarios=request.faixa_beneficiarios,
            tecnico_responsavel_nome=request.tecnico_responsavel_nome,
            tecnico_responsavel_email=request.tecnico_responsavel_email,
            data_referencia=request.data_referencia,
            criado_em=created_at,
            atualizado_em=created_at,
            status_geral="Rascunho",
            auditoria=[
                AuditEvent(
                    evento="criacao",
                    usuario_nome=request.tecnico_responsavel_nome,
                    usuario_email=request.tecnico_responsavel_email,
                    ocorrido_em=created_at,
                    ip_mascarado="0.xxx.xxx.0",
                    hash_estado=hash_snapshot(
                        {
                            "nome_projeto": request.nome_projeto,
                            "territorios": request.territorios,
                            "especies_produtos": request.especies_produtos,
                        }
                    ),
                    nota="Projeto criado na tela única de projeto.",
                )
            ],
        )
        return self.save_project(project)

    def append_version(self, project_id: str, version: ProjectVersion, audit_note: str) -> ProjectRecord:
        project = self.get_project(project_id)
        if project.status_geral == "Arquivado":
            raise ValueError("Projetos arquivados não podem receber nova análise sem desarquivamento.")

        if project.versoes and any(existing.numero_versao == version.numero_versao for existing in project.versoes):
            raise ValueError("Número de versão duplicado.")

        project.versoes.append(version)
        project.status_geral = version.status
        project.auditoria.append(
            AuditEvent(
                evento="reanalise" if version.numero_versao > 1 else "analise_inicial",
                usuario_nome=version.disparado_por_nome,
                usuario_email=version.disparado_por_email,
                ocorrido_em=version.criado_em,
                ip_mascarado="0.xxx.xxx.0",
                hash_estado=version.hash_documento,
                nota=audit_note,
            )
        )
        return self.save_project(project)

    def archive_project(self, project_id: str, note: str, actor_name: str, actor_email: str) -> ProjectRecord:
        project = self.get_project(project_id)
        project.status_geral = "Arquivado"
        project.auditoria.append(
            AuditEvent(
                evento="arquivamento",
                usuario_nome=actor_name,
                usuario_email=actor_email,
                ocorrido_em=iso_now_utc(),
                ip_mascarado="0.xxx.xxx.0",
                hash_estado=hash_snapshot({"project_id": project_id, "status": "Arquivado"}),
                nota=note,
            )
        )
        return self.save_project(project)

    def compare_versions(self, project_id: str, version_left: int, version_right: int) -> dict[str, Any]:
        project = self.get_project(project_id)
        versions = {version.numero_versao: version for version in project.versoes}
        if version_left not in versions or version_right not in versions:
            raise ValueError("Versões solicitadas não existem para este projeto.")

        left = versions[version_left]
        right = versions[version_right]

        left_dims = {item.chave: item for item in left.dimensoes}
        right_dims = {item.chave: item for item in right.dimensoes}
        dims = []
        for key in right_dims:
            before = left_dims.get(key)
            after = right_dims[key]
            before_score = before.pontuacao if before else 0.0
            delta = round(after.pontuacao - before_score, 2)
            dims.append(
                {
                    "dimensao": after.nome,
                    "antes": round(before_score, 2),
                    "depois": round(after.pontuacao, 2),
                    "delta": delta,
                    "direcao": "melhora" if delta > 0 else "piora" if delta < 0 else "estavel",
                }
            )

        left_blockers = {item.id_bloqueio for item in left.bloqueios}
        right_blockers = {item.id_bloqueio for item in right.bloqueios}
        left_gaps = {item.id_indicador for item in left.lacunas}
        right_gaps = {item.id_indicador for item in right.lacunas}

        changed_inputs = []
        for key, right_value in right.entradas.items():
            left_value = left.entradas.get(key)
            if left_value != right_value:
                changed_inputs.append({"campo": key, "antes": left_value, "depois": right_value})

        return {
            "score_geral": {
                "antes": left.pontuacao_geral,
                "depois": right.pontuacao_geral,
                "delta": round(right.pontuacao_geral - left.pontuacao_geral, 2),
            },
            "dimensoes": dims,
            "bloqueios_adicionados": sorted(right_blockers - left_blockers),
            "bloqueios_resolvidos": sorted(left_blockers - right_blockers),
            "lacunas_adicionadas": sorted(right_gaps - left_gaps),
            "lacunas_preenchidas": sorted(left_gaps - right_gaps),
            "campos_alterados": changed_inputs,
        }

    def reset(self) -> None:
        for path in self.base_dir.glob("*.json"):
            path.unlink()
