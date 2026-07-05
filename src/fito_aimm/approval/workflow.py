from __future__ import annotations

from pathlib import Path

from fito_aimm.audit import hash_snapshot, mask_ip
from fito_aimm.models import ApprovalRecord, AuditEvent
from fito_aimm.projects import ProjectRepository
from fito_aimm.utils import iso_now_utc


class ApprovalWorkflow:
    def __init__(self, repository: ProjectRepository):
        self.repository = repository

    def approve_version(
        self,
        project_id: str,
        version_number: int,
        reviewer_name: str,
        reviewer_email: str,
        reviewer_role: str,
        opinion: str,
        decision: str,
        remarks: str | None = None,
        blocker_justifications: dict[str, str] | None = None,
        reviewer_ip: str | None = None,
    ):
        blocker_justifications = blocker_justifications or {}
        project = self.repository.get_project(project_id)
        version = next((item for item in project.versoes if item.numero_versao == version_number), None)
        if version is None:
            raise ValueError("Versão solicitada não existe.")

        if reviewer_email.strip().lower() in {
            project.tecnico_responsavel_email.strip().lower(),
            version.disparado_por_email.strip().lower(),
        }:
            raise ValueError("O revisor deve ser diferente do responsável técnico e do executor da análise.")

        blocker_ids = [item.id_bloqueio for item in version.bloqueios]
        missing_justifications = [
            blocker_id for blocker_id in blocker_ids if not blocker_justifications.get(blocker_id, "").strip()
        ]
        if missing_justifications:
            raise ValueError("Todos os impedimentos ativos precisam de justificativa antes do envio para aprovação.")

        analysis_snapshot = {
            "numero_versao": version.numero_versao,
            "pontuacao_geral": version.pontuacao_geral,
            "dimensoes": [item.model_dump(mode="json") for item in version.dimensoes],
            "bloqueios": [
                {**item.model_dump(mode="json"), "justificativa": blocker_justifications.get(item.id_bloqueio, "")}
                for item in version.bloqueios
            ],
            "lacunas": [item.model_dump(mode="json") for item in version.lacunas],
            "entradas": version.entradas,
        }
        document_hash = hash_snapshot(analysis_snapshot)
        signed_at = iso_now_utc()

        approval = ApprovalRecord(
            revisor_nome=reviewer_name,
            revisor_email=reviewer_email,
            papel_revisor=reviewer_role,
            parecer=opinion,
            decisao=decision,
            ressalvas=remarks,
            confirmou_identidade=True,
            assinado_em=signed_at,
            hash_documento=document_hash,
        )

        version.hash_documento = document_hash
        version.aprovacao = approval
        version.approval_path = str(Path(f"outputs/app/approvals/{project_id}_v{version_number}.json"))
        if decision == "Aprovado":
            version.status = "Aprovado"
        elif decision == "Aprovado com ressalvas":
            version.status = "Aprovado condicionalmente"
        else:
            version.status = "Requer revisão"

        event_name = "aprovacao" if decision != "Reprovado" else "reprovacao"
        project.status_geral = version.status
        project.auditoria.append(
            AuditEvent(
                evento=event_name,
                usuario_nome=reviewer_name,
                usuario_email=reviewer_email,
                ocorrido_em=signed_at,
                ip_mascarado=mask_ip(reviewer_ip),
                hash_estado=document_hash,
                nota=decision,
            )
        )
        approval_path = Path(version.approval_path)
        approval_path.parent.mkdir(parents=True, exist_ok=True)
        approval_path.write_text(approval.model_dump_json(indent=2), encoding="utf-8")
        self.repository.save_project(project)
        return project
