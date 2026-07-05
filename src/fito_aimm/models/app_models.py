from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PortalBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


def _validate_email(value: str) -> str:
    normalized = value.strip()
    if "@" not in normalized or "." not in normalized.split("@")[-1]:
        raise ValueError("Informe um e-mail válido.")
    return normalized


class BeneficiaryRange(PortalBaseModel):
    minimo: int = Field(ge=1)
    maximo: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_order(self) -> "BeneficiaryRange":
        if self.maximo < self.minimo:
            raise ValueError("A faixa de beneficiários deve ter máximo maior ou igual ao mínimo.")
        return self


class DataSourceStatus(PortalBaseModel):
    chave: str
    nome: str
    tipo: str
    campos_expostos: list[str]
    status: Literal["pendente", "coletado", "parcial", "falha"] = "pendente"
    progresso_label: str = "Aguardando coleta"
    aviso: str | None = None


class IndicatorDetail(PortalBaseModel):
    id_indicador: str
    dimensao: str
    nome_dimensao: str
    score_bruto: float = Field(ge=0, le=100)
    score_ajustado: float = Field(ge=0, le=100)
    fonte: str
    nivel_confianca: str
    status_benchmark: str
    limitacao: str = ""
    proxy_utilizada: str | None = None


class DimensionSummary(PortalBaseModel):
    chave: str
    nome: str
    pontuacao: float = Field(ge=0, le=100)
    rotulo_qualitativo: str
    status: str
    tooltip: str
    indicadores: list[IndicatorDetail] = Field(default_factory=list)


class BlockerSummary(PortalBaseModel):
    id_bloqueio: str
    descricao: str
    criticidade: str
    area: str
    origem_campo: str = ""
    justificativa: str | None = None


class GapSummary(PortalBaseModel):
    id_indicador: str
    dimensao: str
    descricao: str
    proxy_utilizada: str
    sugestao_fonte: str


class EvidenceSummary(PortalBaseModel):
    fonte: str
    titulo: str
    valor: str
    data_referencia: str
    nivel_confianca: str
    resumo: str


class ComparisonRow(PortalBaseModel):
    dimensao: str
    referencia_tipo: Literal["benchmark_setorial", "media_regional", "projeto_similar"]
    referencia_nome: str
    pontuacao_projeto: float
    pontuacao_referencia: float
    delta: float
    direcao: Literal["acima", "abaixo", "igual"]
    status: str
    estimativa_aproximada: bool = False
    sugestao_melhoria: str


class ApprovalRecord(PortalBaseModel):
    revisor_nome: str
    revisor_email: str
    papel_revisor: Literal["Analista sênior", "Gestor", "Coordenador"]
    parecer: str = Field(min_length=50, max_length=800)
    decisao: Literal["Aprovado", "Aprovado com ressalvas", "Reprovado"]
    ressalvas: str | None = None
    confirmou_identidade: bool = True
    assinado_em: datetime
    hash_documento: str

    @model_validator(mode="after")
    def validate_remarks(self) -> "ApprovalRecord":
        if self.decisao == "Aprovado com ressalvas" and not (self.ressalvas or "").strip():
            raise ValueError("Aprovação com ressalvas exige o registro das ressalvas.")
        return self

    @field_validator("revisor_email")
    @classmethod
    def validate_reviewer_email(cls, value: str) -> str:
        return _validate_email(value)


class AuditEvent(PortalBaseModel):
    evento: str
    usuario_nome: str
    usuario_email: str
    ocorrido_em: datetime
    ip_mascarado: str
    hash_estado: str
    nota: str = ""

    @field_validator("usuario_email")
    @classmethod
    def validate_audit_email(cls, value: str) -> str:
        return _validate_email(value)


class ProjectVersion(PortalBaseModel):
    numero_versao: int = Field(ge=1)
    criado_em: datetime
    disparado_por_nome: str
    disparado_por_email: str
    status: Literal[
        "Rascunho",
        "Em análise",
        "Em aprovação",
        "Aprovado",
        "Aprovado condicionalmente",
        "Requer revisão",
        "Arquivado",
    ] = "Em análise"
    nota_versao: str = Field(default="", max_length=200)
    pontuacao_geral: float = Field(ge=0, le=100)
    rotulo_geral: str
    elegivel_analise_formal: bool = False
    dimensoes: list[DimensionSummary]
    bloqueios: list[BlockerSummary]
    lacunas: list[GapSummary]
    evidencias: list[EvidenceSummary]
    comparativos: list[ComparisonRow] = Field(default_factory=list)
    entradas: dict[str, Any]
    hash_documento: str = ""
    pdf_path: str | None = None
    approval_path: str | None = None
    aprovacao: ApprovalRecord | None = None

    @field_validator("disparado_por_email")
    @classmethod
    def validate_runner_email(cls, value: str) -> str:
        return _validate_email(value)


class ProjectCreateRequest(PortalBaseModel):
    nome_projeto: str = Field(min_length=3, max_length=120)
    descricao: str = Field(min_length=10, max_length=500)
    territorios: list[str] = Field(min_length=1)
    especies_produtos: list[str] = Field(min_length=1)
    investimento_previsto_brl: float = Field(gt=0)
    faixa_beneficiarios: BeneficiaryRange
    tecnico_responsavel_nome: str = Field(min_length=3, max_length=120)
    tecnico_responsavel_email: str
    data_referencia: date
    perfil_pesos: Literal["padrão", "conservador", "agressivo"] = "padrão"
    bloqueadores_ativos: list[str] = Field(default_factory=list)
    nivel_confianca_minimo: int = Field(ge=1, le=5, default=3)
    modo_execucao: Literal["rápido", "completo"] = "rápido"
    planilha_manual_nome: str | None = None
    nota_execucao: str = ""

    @field_validator("territorios", "especies_produtos")
    @classmethod
    def strip_values(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("Selecione ao menos um item.")
        return cleaned

    @field_validator("data_referencia")
    @classmethod
    def validate_reference_date(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("A data de referência não pode ser futura.")
        return value

    @field_validator("tecnico_responsavel_email")
    @classmethod
    def validate_request_email(cls, value: str) -> str:
        return _validate_email(value)


class ProjectRecord(PortalBaseModel):
    id_projeto: str
    slug: str
    nome_projeto: str
    descricao: str
    territorios: list[str]
    especies_produtos: list[str]
    investimento_previsto_brl: float
    faixa_beneficiarios: BeneficiaryRange
    tecnico_responsavel_nome: str
    tecnico_responsavel_email: str
    data_referencia: date
    bioma: str = "Amazônia"
    criado_em: datetime
    atualizado_em: datetime
    status_geral: str = "Rascunho"
    versoes: list[ProjectVersion] = Field(default_factory=list)
    auditoria: list[AuditEvent] = Field(default_factory=list)

    @field_validator("tecnico_responsavel_email")
    @classmethod
    def validate_project_email(cls, value: str) -> str:
        return _validate_email(value)
