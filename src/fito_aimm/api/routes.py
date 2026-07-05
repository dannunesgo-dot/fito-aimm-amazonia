from __future__ import annotations

import csv
import json
import os
import re
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from fito_aimm.aimm_dashboard import execute_aimm_dashboard
from fito_aimm.aimm_engine import execute_aimm_engine
from fito_aimm.approval import ApprovalWorkflow
from fito_aimm.audit import hash_snapshot
from fito_aimm.benchmark_proxy import execute_benchmark_proxy
from fito_aimm.exporters import ExecutivePdfExporter
from fito_aimm.models import (
    BeneficiaryRange,
    BlockerSummary,
    ComparisonRow,
    DataSourceStatus,
    DimensionSummary,
    EvidenceSummary,
    GapSummary,
    IndicatorDetail,
    ProjectCreateRequest,
    ProjectVersion,
)
from fito_aimm.projects import ProjectRepository
from fito_aimm.species_selection import execute_species_selection
from fito_aimm.utils import (
    dimension_label,
    dimension_tooltip,
    iso_now_utc,
    qualitative_label,
    status_badge,
)


BASE_DIR = Path(".")
PORTAL_JSON = Path("outputs/app/portal_payload.json")
PORTAL_JS = Path("docs/portal_payload.js")
TERRITORY_CONFIG = Path("config/territorios.yaml")
SPECIES_SEED = Path("data/reference/species_candidate_registry_seed.csv")
BLOCKERS_SEED = Path("data/reference/aimm_engine_blockers_seed.csv")
ENGINE_DIMENSIONS = Path("data/processed/aimm_dimension_scores.csv")
ENGINE_INDICATORS = Path("data/processed/aimm_indicator_scores.csv")
ENGINE_OVERALL = Path("data/processed/aimm_overall_score.csv")
BENCHMARK_REGISTRY = Path("data/processed/benchmark_registry.csv")
BENCHMARK_READINESS = Path("data/processed/benchmark_readiness_matrix.csv")
COMMUNICATION_PAYLOAD = Path("outputs/reports/aimm_dashboard_payload.json")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=";"))


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def ensure_prerequisites() -> None:
    execute_species_selection()
    execute_benchmark_proxy()
    execute_aimm_engine()
    execute_aimm_dashboard()


def _normalize_url(value: str) -> str:
    return value.rstrip("/") + "/"


def _repository_slug_from_git() -> str | None:
    try:
        remote = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    match = re.search(r"[:/]([^/]+)/([^/]+?)(?:\.git)?$", remote)
    if not match:
        return None
    return f"{match.group(1)}/{match.group(2)}"


def interface_url() -> str:
    """Return the published GitHub Pages URL for the optimized interface.

    Resolution order:
    1. ``GITHUB_PAGES_URL`` with a trailing slash normalized.
    2. ``GITHUB_REPOSITORY`` in ``owner/repo`` format.
    3. The ``remote.origin.url`` git setting parsed into ``owner/repo``.
    4. The repository's canonical public GitHub Pages URL as a final fallback.
    """
    explicit_url = os.getenv("GITHUB_PAGES_URL")
    if explicit_url:
        return _normalize_url(explicit_url)

    repository = os.getenv("GITHUB_REPOSITORY") or _repository_slug_from_git()
    if repository and "/" in repository:
        owner, repo = repository.split("/", 1)
        return f"https://{owner}.github.io/{repo}/"

    return "https://dannunesgo-dot.github.io/fito-aimm-amazonia/"


def territory_options() -> list[dict[str, str]]:
    payload = load_yaml(TERRITORY_CONFIG)
    return payload.get("territorios", [])


def species_options() -> list[str]:
    rows = read_csv(SPECIES_SEED)
    return [f"{row['nome_popular']} ({row['nome_cientifico']})" for row in rows if row.get("nome_popular")]


def source_catalog() -> list[DataSourceStatus]:
    return [
        DataSourceStatus(
            chave="ibge",
            nome="IBGE/SIDRA",
            tipo="Automática",
            campos_expostos=["Município", "Indicador", "Ano", "Valor"],
            status="coletado",
            progresso_label="Base pública pronta para uso",
        ),
        DataSourceStatus(
            chave="mapa_osc",
            nome="Mapa OSC",
            tipo="Automática",
            campos_expostos=["Razão social", "CNPJ", "Pontuação de risco"],
            status="parcial",
            progresso_label="Coleta pronta com revisão documental pendente",
            aviso="A diligência manual das organizações permanece obrigatória.",
        ),
        DataSourceStatus(
            chave="planilha_manual",
            nome="Planilha manual",
            tipo="Upload CSV",
            campos_expostos=["Indicador", "Fonte", "Valor", "Observação"],
            status="pendente",
            progresso_label="Aguardando envio do usuário",
        ),
        DataSourceStatus(
            chave="benchmarks",
            nome="Referências de mercado",
            tipo="Configuração",
            campos_expostos=["Espécie", "Dimensão", "Valor de referência"],
            status="coletado",
            progresso_label="Referências e estimativas carregadas do repositório",
        ),
    ]


def _parse_float(value: str) -> float:
    try:
        return float(str(value).replace(",", "."))
    except Exception:
        return 0.0


def _read_analysis_payload() -> dict[str, Any]:
    payload = json.loads(COMMUNICATION_PAYLOAD.read_text(encoding="utf-8")) if COMMUNICATION_PAYLOAD.exists() else {}
    if payload:
        return payload
    dimensions = read_csv(ENGINE_DIMENSIONS)
    blockers = read_csv(BLOCKERS_SEED)
    overall = read_csv(ENGINE_OVERALL)[0]
    return {"summary": overall, "dimensions": dimensions, "blockers": blockers}


def _select_blockers(active_blockers: list[str], default_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    if not active_blockers:
        return default_rows
    return [row for row in default_rows if row.get("id_bloqueio") in active_blockers]


def _dedupe_gaps(gaps: list[GapSummary]) -> list[GapSummary]:
    seen: set[str] = set()
    ordered: list[GapSummary] = []
    for gap in gaps:
        if gap.id_indicador in seen:
            continue
        seen.add(gap.id_indicador)
        ordered.append(gap)
    return ordered


def _build_dimension_models(multiplier: float) -> tuple[list[DimensionSummary], list[GapSummary]]:
    dimensions_rows = read_csv(ENGINE_DIMENSIONS)
    indicator_rows = read_csv(ENGINE_INDICATORS)
    readiness_rows = {row["id_benchmark"]: row for row in read_csv(BENCHMARK_READINESS)}

    dimensions: list[DimensionSummary] = []
    gaps: list[GapSummary] = []
    for dimension_row in dimensions_rows:
        key = dimension_row["dimensao_aimm"]
        indicators = []
        related = [row for row in indicator_rows if row["dimensao_aimm"] == key]
        for row in related:
            adjusted = min(100.0, round(_parse_float(row["score_ajustado_preliminar"]) * multiplier, 2))
            indicator = IndicatorDetail(
                id_indicador=row["id_indicador"],
                dimensao=key,
                nome_dimensao=dimension_label(key),
                score_bruto=_parse_float(row["score_bruto_preliminar"]),
                score_ajustado=adjusted,
                fonte=row["id_benchmark"],
                nivel_confianca=row["nivel_confianca"],
                status_benchmark=row["status_prontidao_benchmark"],
                limitacao=row.get("limitacao", ""),
                proxy_utilizada=readiness_rows.get(row["id_benchmark"], {}).get("classificacao_benchmark"),
            )
            indicators.append(indicator)
            if row["status_prontidao_benchmark"] != "benchmark_utilizavel":
                gaps.append(
                    GapSummary(
                        id_indicador=row["id_indicador"],
                        dimensao=dimension_label(key),
                        descricao=row.get("limitacao", "Indicador ainda depende de dado confiável."),
                        proxy_utilizada=readiness_rows.get(row["id_benchmark"], {}).get("classificacao_benchmark", "Estimativa"),
                        sugestao_fonte="Validar benchmark público, evidência documental e atualização territorial.",
                    )
                )

        score = min(100.0, round(_parse_float(dimension_row["score_dimensao_preliminar"]) * multiplier, 2))
        dimensions.append(
            DimensionSummary(
                chave=key,
                nome=dimension_label(key),
                pontuacao=score,
                rotulo_qualitativo=qualitative_label(score),
                status=dimension_row.get("status_dimensao", "preliminar"),
                tooltip=dimension_tooltip(key),
                indicadores=indicators,
            )
        )
    return dimensions, gaps


def _build_evidence_items() -> list[EvidenceSummary]:
    dashboard_payload = _read_analysis_payload()
    blockers = dashboard_payload.get("blockers", [])
    evidence = [
        EvidenceSummary(
            fonte="Calculadora AIMM",
            titulo="Resumo estrutural do motor AIMM",
            valor=str(dashboard_payload.get("summary", {}).get("score_estrutural_preliminar", "")),
            data_referencia=date.today().isoformat(),
            nivel_confianca="médio",
            resumo="Resultado consolidado da rodada automática com foco em pontuação estrutural e impedimentos ativos.",
        )
    ]
    for blocker in blockers[:4]:
        evidence.append(
            EvidenceSummary(
                fonte=blocker.get("area", "Governança"),
                titulo=blocker.get("bloqueio", "Impedimento registrado"),
                valor=blocker.get("criticidade", ""),
                data_referencia=date.today().isoformat(),
                nivel_confianca="médio",
                resumo=blocker.get("efeito_no_score", ""),
            )
        )
    return evidence


def _benchmark_reference_scores() -> dict[str, float]:
    benchmarks = read_csv(BENCHMARK_REGISTRY)
    readiness = {row["id_benchmark"]: row for row in read_csv(BENCHMARK_READINESS)}
    confidence_score = {"alto": 78.0, "medio": 65.0, "baixo": 48.0, "bloqueado": 35.0}
    bucket: dict[str, list[float]] = {}
    for row in benchmarks:
        dimension = row["dimensao_aimm"]
        score = confidence_score.get(row.get("nivel_confianca", "baixo"), 45.0)
        if readiness[row["id_benchmark"]]["status_prontidao"] == "bloqueado":
            score = 35.0
        bucket.setdefault(dimension, []).append(score)
    return {key: round(sum(values) / len(values), 2) for key, values in bucket.items()}


def _comparison_rows(
    dimensions: list[DimensionSummary],
    regional_versions: list[ProjectVersion],
    similar_versions: list[ProjectVersion],
) -> list[ComparisonRow]:
    references = _benchmark_reference_scores()
    rows: list[ComparisonRow] = []
    regional_map: dict[str, float] = {}
    if regional_versions:
        for version in regional_versions:
            for dimension in version.dimensoes:
                regional_map.setdefault(dimension.chave, 0.0)
                regional_map[dimension.chave] += dimension.pontuacao
        regional_map = {
            key: round(value / len(regional_versions), 2)
            for key, value in regional_map.items()
        }

    similar_reference = similar_versions[0] if similar_versions else None
    for dimension in dimensions:
        benchmark_score = references.get(dimension.chave, 50.0)
        regional_score = regional_map.get(dimension.chave, benchmark_score - 4)
        similar_score = next(
            (item.pontuacao for item in similar_reference.dimensoes if item.chave == dimension.chave),
            benchmark_score - 2,
        ) if similar_reference else benchmark_score - 2
        similar_name = similar_reference.nota_versao if similar_reference and similar_reference.nota_versao else "Projeto similar"
        for ref_type, ref_name, ref_score, estimated in (
            ("benchmark_setorial", "Benchmark setorial", benchmark_score, True),
            ("media_regional", "Média regional", regional_score, False),
            ("projeto_similar", similar_name, similar_score, False),
        ):
            delta = round(dimension.pontuacao - ref_score, 2)
            rows.append(
                ComparisonRow(
                    dimensao=dimension.nome,
                    referencia_tipo=ref_type,
                    referencia_nome=ref_name,
                    pontuacao_projeto=dimension.pontuacao,
                    pontuacao_referencia=ref_score,
                    delta=delta,
                    direcao="acima" if delta > 0 else "abaixo" if delta < 0 else "igual",
                    status="Acima da referência" if delta > 0 else "Abaixo da referência" if delta < 0 else "Em linha",
                    estimativa_aproximada=estimated,
                    sugestao_melhoria=(
                        f"Reforçar {dimension.nome.lower()} com dados validados e ações territoriais."
                        if delta < 0
                        else f"Manter a consistência de {dimension.nome.lower()} e registrar evidências comparáveis."
                    ),
                )
            )
    return rows


def _analysis_multiplier(profile: str, execution_mode: str, confidence_level: int) -> float:
    multiplier = 1.0
    if profile == "conservador":
        multiplier -= 0.08
    elif profile == "agressivo":
        multiplier += 0.05
    if execution_mode == "rápido":
        multiplier -= 0.02
    else:
        multiplier += 0.03
    multiplier += (confidence_level - 3) * 0.01
    return max(0.75, min(1.15, multiplier))


def create_analysis_version(
    request: ProjectCreateRequest,
    version_number: int,
    related_versions: list[ProjectVersion] | None = None,
    similar_versions: list[ProjectVersion] | None = None,
) -> ProjectVersion:
    ensure_prerequisites()
    overall = read_csv(ENGINE_OVERALL)[0]
    multiplier = _analysis_multiplier(request.perfil_pesos, request.modo_execucao, request.nivel_confianca_minimo)
    dimensions, gaps = _build_dimension_models(multiplier)
    blocker_rows = _select_blockers(request.bloqueadores_ativos, read_csv(BLOCKERS_SEED))
    blockers = [
        BlockerSummary(
            id_bloqueio=row["id_bloqueio"],
            descricao=row["bloqueio"],
            criticidade=row["criticidade"],
            area=row["area"],
            origem_campo="bloqueadores_ativos",
        )
        for row in blocker_rows
    ]
    score = min(100.0, round(_parse_float(overall["score_estrutural_preliminar"]) * multiplier, 2))
    has_critical = any(item.criticidade == "alta" for item in blockers)
    comparisons = _comparison_rows(dimensions, related_versions or [], similar_versions or [])
    version = ProjectVersion(
        numero_versao=version_number,
        criado_em=iso_now_utc(),
        disparado_por_nome=request.tecnico_responsavel_nome,
        disparado_por_email=request.tecnico_responsavel_email,
        status="Em análise",
        nota_versao=request.nota_execucao or f"Análise {request.modo_execucao} executada com perfil {request.perfil_pesos}.",
        pontuacao_geral=score,
        rotulo_geral=status_badge(score, has_blocker=has_critical),
        elegivel_analise_formal=score >= 70 and not has_critical,
        dimensoes=dimensions,
        bloqueios=blockers,
        lacunas=_dedupe_gaps(gaps),
        evidencias=_build_evidence_items(),
        comparativos=comparisons,
        entradas=request.model_dump(mode="json"),
    )
    version.hash_documento = hash_snapshot(
        {
            "numero_versao": version.numero_versao,
            "pontuacao_geral": version.pontuacao_geral,
            "dimensoes": [item.model_dump(mode="json") for item in version.dimensoes],
            "bloqueios": [item.model_dump(mode="json") for item in version.bloqueios],
            "lacunas": [item.model_dump(mode="json") for item in version.lacunas],
            "entradas": version.entradas,
        }
    )
    return version


def _project_summary(project) -> dict[str, Any]:
    latest = project.versoes[-1] if project.versoes else None
    return {
        "id_projeto": project.id_projeto,
        "nome_projeto": project.nome_projeto,
        "territorios": project.territorios,
        "especies_produtos": project.especies_produtos,
        "status_geral": project.status_geral,
        "ultima_pontuacao": latest.pontuacao_geral if latest else None,
        "ultima_versao": latest.numero_versao if latest else None,
        "ultima_aprovacao": latest.status if latest else None,
    }


def _write_payload(payload: dict[str, Any]) -> None:
    PORTAL_JSON.parent.mkdir(parents=True, exist_ok=True)
    PORTAL_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    PORTAL_JS.write_text(
        "window.FITO_PORTAL_DATA = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )


def _seed_demo_projects(repository: ProjectRepository, reset: bool) -> None:
    if reset:
        repository.reset()
    if repository.list_projects():
        return

    demo_requests = [
        ProjectCreateRequest(
            nome_projeto="Corredor de Fitoterápicos Manaus",
            descricao="Projeto demonstrativo para consolidar coleta de dados, pontuação AIMM e aprovação formal.",
            territorios=["Manaus/AM", "Belém/PA"],
            especies_produtos=["andiroba (Carapa guianensis)", "gengibre (Zingiber officinale)"],
            investimento_previsto_brl=9500000,
            faixa_beneficiarios=BeneficiaryRange(minimo=120, maximo=400),
            tecnico_responsavel_nome="Equipe FITO+",
            tecnico_responsavel_email="analise@fito-amazonia.org",
            data_referencia=date(2026, 7, 5),
            perfil_pesos="padrão",
            bloqueadores_ativos=["BLK_002", "BLK_004"],
            nivel_confianca_minimo=3,
            modo_execucao="completo",
            nota_execucao="Versão inicial com comparação regional e geração do painel executivo.",
        ),
        ProjectCreateRequest(
            nome_projeto="Bioeconomia Andiroba Tapajós",
            descricao="Projeto de referência para comparação regional e benchmarking em bioeconomia amazônica.",
            territorios=["Santarém/PA"],
            especies_produtos=["andiroba (Carapa guianensis)"],
            investimento_previsto_brl=6800000,
            faixa_beneficiarios=BeneficiaryRange(minimo=80, maximo=260),
            tecnico_responsavel_nome="Núcleo Regional",
            tecnico_responsavel_email="tapajos@fito-amazonia.org",
            data_referencia=date(2026, 6, 28),
            perfil_pesos="conservador",
            bloqueadores_ativos=["BLK_003"],
            nivel_confianca_minimo=4,
            modo_execucao="completo",
            nota_execucao="Projeto usado como referência de mercado e histórico.",
        ),
    ]

    created_project_ids: dict[str, str] = {}
    for request in demo_requests:
        project = repository.create_project(request)
        created_project_ids[request.nome_projeto] = project.id_projeto
        current_versions = [
            item.versoes[-1]
            for item in repository.list_projects()
            if item.versoes
        ]
        version = create_analysis_version(
            request,
            version_number=1,
            related_versions=current_versions,
            similar_versions=current_versions,
        )
        repository.append_version(project.id_projeto, version, version.nota_versao)

    primary = repository.get_project(created_project_ids["Corredor de Fitoterápicos Manaus"])
    secondary = repository.get_project(created_project_ids["Bioeconomia Andiroba Tapajós"])
    first_request = demo_requests[0].model_copy(update={"perfil_pesos": "agressivo", "nivel_confianca_minimo": 4, "bloqueadores_ativos": ["BLK_002"]})
    version_two = create_analysis_version(
        first_request,
        version_number=2,
        related_versions=[secondary.versoes[-1]],
        similar_versions=[secondary.versoes[-1]],
    )
    repository.append_version(primary.id_projeto, version_two, version_two.nota_versao)

    workflow = ApprovalWorkflow(repository)
    workflow.approve_version(
        primary.id_projeto,
        version_number=2,
        reviewer_name="Coordenação Técnica",
        reviewer_email="coordenacao@fito-amazonia.org",
        reviewer_role="Coordenador",
        opinion="A análise apresenta coerência metodológica, registra os impedimentos remanescentes e oferece base suficiente para uso executivo interno nesta etapa.",
        decision="Aprovado",
        blocker_justifications={"BLK_002": "Benchmark interno segue bloqueado, mas a decisão atual usa apenas referência pública e revisão documental."},
        reviewer_ip="189.10.20.12",
    )


def build_portal_payload(reset_demo: bool = False) -> dict[str, Any]:
    repository = ProjectRepository()
    _seed_demo_projects(repository, reset_demo)
    exporter = ExecutivePdfExporter()

    projects = repository.list_projects()
    for project in projects:
        for version in project.versoes:
            if not version.pdf_path:
                pdf_path = exporter.export(project, version)
                version.pdf_path = str(pdf_path)
        repository.save_project(project)

    highlighted = max(repository.list_projects(), key=lambda item: (len(item.versoes), item.atualizado_em))
    latest = highlighted.versoes[-1]
    compare_latest = repository.compare_versions(highlighted.id_projeto, 1, latest.numero_versao) if len(highlighted.versoes) > 1 else {}

    payload = {
        "metadata": {
            "titulo": "Fito+ Amazônia AIMM",
            "descricao": "Fluxo único de projeto, análise, comparativos, histórico, aprovação formal e exportação executiva.",
            "gerado_em": iso_now_utc().isoformat(),
        },
        "formularios": {
            "territorios": territory_options(),
            "especies_produtos": species_options(),
            "fontes": [item.model_dump(mode="json") for item in source_catalog()],
            "bloqueadores": read_csv(BLOCKERS_SEED),
            "perfis_peso": ["padrão", "conservador", "agressivo"],
        },
        "projetos": [_project_summary(project) for project in projects],
        "projeto_destaque": highlighted.model_dump(mode="json"),
        "comparacao_destaque": compare_latest,
        "links": {
            "interface_otimizada": interface_url(),
            "pdf_versao_atual": latest.pdf_path,
            "json_payload": str(PORTAL_JSON),
        },
    }
    _write_payload(payload)
    return payload
