# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


BASE = Path("outputs/gis/rodada_4_22_E_pacote_replicacao")

ARQUIVOS = {
    "guia_curto": BASE / "GUIA_CURTO_REPLICACAO_GIS_NOVO_MUNICIPIO.md",
    "guia_tecnico": BASE / "GUIA_TECNICO_QGIS_REPLICACAO_MUNICIPIO.md",
    "checklist": BASE / "checklist_replicacao_gis_novo_municipio.csv",
    "manifesto": BASE / "gis_novo_municipio_manifest_template.csv",
    "drive_map": BASE / "drive_map_replicacao_gis.csv",
    "registry": Path("data/processed/gis/gis_replication_package_registry_4_22_e.csv"),
    "status": Path("data/processed/gis/gis_replication_package_status_4_22_e.csv"),
    "gaps": Path("data/processed/gis/gis_replication_package_gaps_4_22_e.csv"),
    "evidence": Path("data/evidence/evidence_gis_replication_package_4_22_e.csv"),
    "report": Path("outputs/reports/RELATORIO_GIS_REPLICACAO_4_22_E.md"),
    "log": Path("outputs/logs/teste_gis_replicacao_4_22_e.txt"),
}


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Nenhuma linha para gravar em {path}")

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()), delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    guia_curto = """
# Guia curto — replicação GIS para novo município

## Finalidade

Repetir o fluxo GIS validado em Manaus para outro município.

## O que a equipe precisa entregar

1. GeoPackage isolado do município.
2. Código IBGE do município.
3. Nome do município.
4. Nome da UF.
5. Sigla da UF.
6. Área em km² conforme fonte oficial usada.
7. Prints de validação no QGIS.
8. Projeto QGIS salvo.

## Fluxo simples

1. Abrir a malha municipal no QGIS.
2. Selecionar o município pelo código IBGE.
3. Exportar somente o município como GeoPackage.
4. Conferir se há 1 feição.
5. Registrar CRS, campo de código e valor do código.
6. Criar tabela relacional de atributos.
7. Fazer join visual no QGIS.
8. Confirmar campos com prefixo aimm_ preenchidos.
9. Salvar prints e projeto QGIS.
10. Registrar a validação no GitHub.

## Travas

- Não editar geometria.
- Não recalcular área nesta etapa.
- Não gerar buffer.
- Não calcular densidade.
- Não calcular centroide.
- Não liberar score AIMM final.
"""

    guia_tecnico = """
# Guia técnico — QGIS 3.40.14 e GitHub

## 1. Preparar GeoPackage isolado

No QGIS:

Camada > Adicionar Camada > Adicionar Camada Vetorial

Abra a malha municipal do IBGE.

Selecione o município por expressão. Exemplo:

"CD_MUN" = '1302603'

Depois:

Botão direito na camada > Exportar > Salvar feições selecionadas como...

Configuração recomendada:

- Formato: GeoPackage
- CRS: manter o CRS original ou registrar explicitamente o CRS usado
- Nome do arquivo: municipio_nome_codigo.gpkg

Exemplo:

municipio_manaus_1302603.gpkg

## 2. Conferências mínimas

- Total de feições: 1
- Código IBGE correto
- Município correto
- UF correta
- Geometria visível
- CRS identificado
- Sem problema visual grosseiro

## 3. Join relacional

Usar:

Campo da camada geométrica = campo da tabela relacional

Exemplo validado:

CD_MUN = codigo_ibge

Prefixo recomendado:

aimm_

## 4. Arquivamento no Drive

Usar a estrutura:

- 09_gis/01_insumos_brutos
- 09_gis/02_qgis_projetos
- 09_gis/03_camadas_validadas
- 09_gis/04_outputs
- 09_gis/05_logs

## 5. Restrições

Não usar workflows antigos C, C2 ou C3.

Não fazer UPDATE direto na tabela geométrica do GeoPackage pelo SQLite.

Não usar ST_IsEmpty, ST_Area, ST_Centroid ou ST_Buffer no SQLite puro do GitHub Actions.

Operações espaciais reais devem ser feitas no QGIS ou em rodada própria com biblioteca GIS adequada.
"""

    checklist = [
        {"item": "GeoPackage isolado criado", "obrigatorio": "sim", "como_conferir": "arquivo abre no QGIS"},
        {"item": "Apenas uma feição", "obrigatorio": "sim", "como_conferir": "tabela de atributos mostra total 1"},
        {"item": "Código IBGE confirmado", "obrigatorio": "sim", "como_conferir": "campo de código tem valor esperado"},
        {"item": "CRS registrado", "obrigatorio": "sim", "como_conferir": "propriedades da camada"},
        {"item": "Geometria visível", "obrigatorio": "sim", "como_conferir": "aproximar à camada"},
        {"item": "Tabela relacional criada", "obrigatorio": "sim", "como_conferir": "tabela interna ou CSV validado"},
        {"item": "Join criado", "obrigatorio": "sim", "como_conferir": "campos com prefixo aimm_ aparecem preenchidos"},
        {"item": "Prints gerados", "obrigatorio": "sim", "como_conferir": "arquivos PNG arquivados"},
        {"item": "Projeto QGIS salvo", "obrigatorio": "sim", "como_conferir": "arquivo QGZ no Drive"},
        {"item": "Registro GitHub executado", "obrigatorio": "sim", "como_conferir": "workflow verde"},
    ]

    manifesto = [
        {
            "rodada": "preencher",
            "municipio": "preencher",
            "codigo_ibge": "preencher",
            "arquivo_gpkg": "municipio_nome_codigo.gpkg",
            "crs": "preencher",
            "campo_codigo": "preencher",
            "valor_codigo": "preencher",
            "campo_municipio": "preencher",
            "valor_municipio": "preencher",
            "campo_uf": "preencher",
            "valor_uf": "preencher",
            "numero_feicoes": "1",
            "geometria_visivel_qgis": "sim",
            "check_validity_executado": "sim/nao",
            "valid_count": "preencher",
            "invalid_count": "preencher",
            "error_count": "preencher",
            "pasta_drive": "09_gis/03_camadas_validadas",
            "observacao": "preencher",
        }
    ]

    drive_map = [
        {"arquivo": "GeoPackage bruto original", "pasta_drive": "09_gis/01_insumos_brutos"},
        {"arquivo": "GeoPackage isolado validado", "pasta_drive": "09_gis/03_camadas_validadas"},
        {"arquivo": "GeoPackage com tabela relacional", "pasta_drive": "09_gis/03_camadas_validadas"},
        {"arquivo": "Projeto QGIS QGZ", "pasta_drive": "09_gis/02_qgis_projetos"},
        {"arquivo": "Prints de validação visual", "pasta_drive": "09_gis/04_outputs/rodada_municipio_validacao_visual"},
        {"arquivo": "Logs", "pasta_drive": "09_gis/05_logs"},
        {"arquivo": "ZIP de artefato GitHub", "pasta_drive": "07_versoes_congeladas"},
    ]

    registry = [
        {
            "rodada": "4.22-E",
            "pacote": "replicacao_gis_novos_municipios",
            "arquivos_operacionais": "5",
            "checklist_itens": "10",
            "modelo_manifesto": "sim",
            "mapa_drive": "sim",
            "trava": "nao_processa_geometria_nao_calcula_area_densidade_buffer_centroide_score_final",
        }
    ]

    status = [
        {
            "rodada": "4.22-E",
            "status": "sucesso",
            "erros_estruturais": "0",
            "lacunas_registradas": "2",
            "proxima_rodada": "4.22-F",
            "proxima_rodada_descricao": "aplicacao do pacote GIS a segundo municipio ou fechamento do modulo GIS Manaus",
        }
    ]

    gaps = [
        {
            "gap_id": "GAP_422E_SEM_PROCESSAMENTO_GEOMETRICO",
            "tipo": "metodologico",
            "criticidade": "controlada",
            "descricao": "Pacote operacional não processa geometria real",
            "acao_recomendada": "Executar validação geométrica e join visual no QGIS para cada novo município",
            "bloqueia_score_final": "sim",
        },
        {
            "gap_id": "GAP_422E_DRIVE_NAO_VERIFICADO",
            "tipo": "arquivamento",
            "criticidade": "baixa",
            "descricao": "Workflow não acessa o Google Drive",
            "acao_recomendada": "Confirmar arquivamento visualmente pelo operador",
            "bloqueia_score_final": "nao",
        },
    ]

    evidence = [
        {
            "id_evidencia": "EVD_GIS_REPLICATION_PACKAGE_4_22_E",
            "tipo_evidencia": "pacote_operacional",
            "descricao": "Pacote para replicação controlada do fluxo GIS em novos municípios",
            "status": "gerado",
            "limitacao": "Não processa geometria e não verifica Drive",
        }
    ]

    report = """
# Rodada 4.22-E — pacote operacional GIS para replicação em novos municípios

## Resultado

Pacote operacional gerado para replicar o fluxo GIS validado em Manaus.

## Arquivos principais

- GUIA_CURTO_REPLICACAO_GIS_NOVO_MUNICIPIO.md
- GUIA_TECNICO_QGIS_REPLICACAO_MUNICIPIO.md
- checklist_replicacao_gis_novo_municipio.csv
- gis_novo_municipio_manifest_template.csv
- drive_map_replicacao_gis.csv

## Travas

- Não processa geometria.
- Não altera GeoPackage.
- Não calcula área.
- Não calcula densidade.
- Não calcula centroide.
- Não calcula buffer.
- Não libera score AIMM final.

## Próximo uso

A equipe deve usar este pacote antes de iniciar novo município no QGIS.
"""

    log = """
TESTE GIS_REPLICATION_PACKAGE_4_22_E — Fito+ Amazônia
======================================================================================
Pacote operacional GIS gerado: sim
Itens de checklist: 10
Modelo de manifesto: sim
Mapa de Drive: sim
Lacunas registradas: 2
Erros estruturais: 0

Resultado: SUCESSO.
Pacote operacional GIS para replicação em novos municípios foi gerado.

Trava: não processa geometria, não calcula área, densidade, centroide, buffer nem score AIMM final.
"""

    write_text(ARQUIVOS["guia_curto"], guia_curto)
    write_text(ARQUIVOS["guia_tecnico"], guia_tecnico)
    write_csv(ARQUIVOS["checklist"], checklist)
    write_csv(ARQUIVOS["manifesto"], manifesto)
    write_csv(ARQUIVOS["drive_map"], drive_map)
    write_csv(ARQUIVOS["registry"], registry)
    write_csv(ARQUIVOS["status"], status)
    write_csv(ARQUIVOS["gaps"], gaps)
    write_csv(ARQUIVOS["evidence"], evidence)
    write_text(ARQUIVOS["report"], report)
    write_text(ARQUIVOS["log"], log)

    for nome, caminho in ARQUIVOS.items():
        if not caminho.exists():
            raise FileNotFoundError(f"Arquivo não criado: {nome} -> {caminho}")
        if caminho.stat().st_size == 0:
            raise ValueError(f"Arquivo vazio: {nome} -> {caminho}")

    print(log.strip())


if __name__ == "__main__":
    main()
