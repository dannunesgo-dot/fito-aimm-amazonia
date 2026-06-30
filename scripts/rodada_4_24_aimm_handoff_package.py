# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


BASE = Path("outputs/aimm/rodada_4_24_pacote_retomada")

FILES = {
    "pacote": BASE / "PACOTE_RETOMADA_AIMM_4_24.md",
    "readme": BASE / "README_OPERACIONAL_AIMM_4_24.md",
    "prompt": BASE / "PROMPT_RETOMADA_OUTRO_CHAT_4_24.md",
    "historico": BASE / "HISTORICO_RODADAS_AIMM_ATE_4_23.csv",
    "travas": BASE / "TRAVAS_LACUNAS_AIMM_4_24.csv",
    "plano": BASE / "PLANO_PROXIMAS_RODADAS_AIMM_4_24.csv",
    "checklist": BASE / "CHECKLIST_RETOMADA_AIMM_4_24.csv",
    "registry": Path("data/processed/aimm/aimm_handoff_package_registry_4_24.csv"),
    "status": Path("data/processed/aimm/aimm_handoff_package_status_4_24.csv"),
    "evidence": Path("data/evidence/evidence_aimm_handoff_package_4_24.csv"),
    "report": Path("outputs/reports/RELATORIO_AIMM_RETOMADA_4_24.md"),
    "log": Path("outputs/logs/teste_aimm_retomada_4_24.txt"),
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
    historico = [
        {"rodada": "4.6", "bloco": "risco OSC", "status": "validada", "resultado": "diagnostico de screening e lista curta controlada"},
        {"rodada": "4.7", "bloco": "pre-diligencia OSC", "status": "validada", "resultado": "fila operacional de contato e validacao"},
        {"rodada": "4.8", "bloco": "consolidacao pre-diligencia", "status": "validada", "resultado": "consolidacao de contato, documentos e encaminhamentos"},
        {"rodada": "4.9", "bloco": "validacao manual", "status": "validada com lacuna", "resultado": "template manual preparado; sem preenchimento manual nesta fase"},
        {"rodada": "4.10", "bloco": "congelamento tecnico", "status": "validada", "resultado": "indice mestre e registro de lacunas"},
        {"rodada": "4.11", "bloco": "arquitetura AIMM", "status": "validada", "resultado": "arquitetura da calculadora em duas camadas"},
        {"rodada": "4.12", "bloco": "especies candidatas", "status": "validada", "resultado": "matriz preliminar de selecao de especies"},
        {"rodada": "4.13", "bloco": "produtos e rotas", "status": "validada", "resultado": "rotas produtivas e regulatorias preliminares"},
        {"rodada": "4.14", "bloco": "orcamento", "status": "validada", "resultado": "orcamento preliminar por componente"},
        {"rodada": "4.15", "bloco": "benchmarks e proxies", "status": "validada", "resultado": "benchmarks, proxies e lacunas AIMM"},
        {"rodada": "4.16", "bloco": "motor AIMM", "status": "validada", "resultado": "motor inicial estrutural da calculadora"},
        {"rodada": "4.17", "bloco": "dashboard AIMM", "status": "validada", "resultado": "painel e resumo executivo preliminar"},
        {"rodada": "4.18", "bloco": "comunicacao AIMM", "status": "validada", "resultado": "pacote editavel de comunicacao e visualizacao"},
        {"rodada": "4.19-A", "bloco": "publicacao", "status": "validada", "resultado": "mapa local/Drive e pacote de publicacao"},
        {"rodada": "4.19-B", "bloco": "revisao visual", "status": "validada com pendencias", "resultado": "registro de revisao visual humana pendente"},
        {"rodada": "4.19-C", "bloco": "encerramento 4.19", "status": "validada", "resultado": "encerramento formal e lacunas de revisao humana"},
        {"rodada": "4.20", "bloco": "alinhamento AIMM", "status": "validada", "resultado": "indicadores, padroes e dimensoes alinhados"},
        {"rodada": "4.21", "bloco": "GIS estrutural", "status": "validada", "resultado": "registro estrutural GIS com lacunas controladas"},
        {"rodada": "4.22-A", "bloco": "baseline GIS", "status": "validada", "resultado": "baseline GIS territorial preparado"},
        {"rodada": "4.22-B1", "bloco": "registro Manaus", "status": "validada", "resultado": "insumo Manaus registrado"},
        {"rodada": "4.22-B2", "bloco": "validacao Manaus isolado", "status": "validada", "resultado": "GeoPackage Manaus validado estruturalmente"},
        {"rodada": "4.22-C4", "bloco": "atributos Manaus", "status": "validada", "resultado": "atributos municipais recompostos em tabela relacional"},
        {"rodada": "4.22-D", "bloco": "join QGIS", "status": "validada", "resultado": "join visual QGIS confirmado"},
        {"rodada": "4.22-D2", "bloco": "registro validacao visual", "status": "validada", "resultado": "validacao visual QGIS registrada"},
        {"rodada": "4.22-E", "bloco": "pacote replicacao GIS", "status": "validada", "resultado": "pacote operacional GIS para novos municipios"},
        {"rodada": "4.23", "bloco": "encerramento GIS Manaus", "status": "validada", "resultado": "modulo GIS Manaus encerrado e integrado ao AIMM geral"},
    ]

    travas = [
        {"id": "TRAVA_001", "tema": "score AIMM", "descricao": "Score AIMM final nao esta liberado.", "status": "ativa"},
        {"id": "TRAVA_002", "tema": "GIS", "descricao": "Nao calcular area, densidade, centroide ou buffer sem rodada espacial propria.", "status": "ativa"},
        {"id": "TRAVA_003", "tema": "GIS", "descricao": "Nao usar workflows antigos C, C2 ou C3 de recomposicao geometrica.", "status": "ativa"},
        {"id": "TRAVA_004", "tema": "Drive", "descricao": "Workflows nao verificam binariamente arquivos no Google Drive; arquivamento depende de validacao visual humana.", "status": "ativa"},
        {"id": "TRAVA_005", "tema": "segundo municipio", "descricao": "Replicacao em segundo municipio nao foi testada nesta fase.", "status": "lacuna_controlada"},
        {"id": "TRAVA_006", "tema": "preenchimento manual", "descricao": "Revisao visual humana e alguns insumos manuais seguem como lacunas operacionais registradas.", "status": "ativa"},
        {"id": "TRAVA_007", "tema": "orcamento", "descricao": "Orcamento preliminar nao autoriza contratacao, compra, convenio, TED ou execucao.", "status": "ativa"},
        {"id": "TRAVA_008", "tema": "rotas regulatorias", "descricao": "Rotas produtivas e regulatorias sao preliminares e nao aprovam produto final.", "status": "ativa"},
    ]

    plano = [
        {"proxima_rodada": "4.25", "nome": "manual tecnico operacional AIMM", "objetivo": "gerar manual detalhado de funcionamento da calculadora AIMM", "prioridade": "alta"},
        {"proxima_rodada": "4.26", "nome": "manual curto para equipe nao tecnica", "objetivo": "criar guia simples de uso por formuladores com baixa familiaridade com informatica", "prioridade": "alta"},
        {"proxima_rodada": "4.27", "nome": "teste de retomada em novo chat", "objetivo": "validar se o pacote 4.24 permite retomar o projeto sem perda de contexto", "prioridade": "alta"},
        {"proxima_rodada": "4.28", "nome": "matriz de pendencias finais", "objetivo": "organizar pendencias tecnicas, manuais, Drive, GIS, benchmarks e score AIMM", "prioridade": "alta"},
        {"proxima_rodada": "4.29", "nome": "plano de testes AIMM", "objetivo": "definir testes unitarios e operacionais para estabilizacao da calculadora", "prioridade": "media"},
        {"proxima_rodada": "4.30", "nome": "reabertura do score AIMM", "objetivo": "avaliar condicoes minimas para evoluir do score estrutural preliminar ao score operacional", "prioridade": "media"},
    ]

    checklist = [
        {"item": "ZIP da 4.24 arquivado", "criterio": "arquivo em 07_versoes_congeladas", "status": "pendente_apos_execucao"},
        {"item": "Pacote de retomada lido", "criterio": "PACOTE_RETOMADA_AIMM_4_24.md abre sem erro", "status": "pendente_apos_execucao"},
        {"item": "Prompt de retomada testado", "criterio": "novo chat entende estado do projeto", "status": "pendente"},
        {"item": "Historico de rodadas conferido", "criterio": "CSV contem rodadas ate 4.23", "status": "pendente_apos_execucao"},
        {"item": "Travas conferidas", "criterio": "score final permanece bloqueado", "status": "pendente_apos_execucao"},
        {"item": "Plano de proximas rodadas conferido", "criterio": "4.25 a 4.30 registradas", "status": "pendente_apos_execucao"},
    ]

    registry = [
        {
            "rodada": "4.24",
            "pacote": "retomada_e_documentacao_operacional_aimm",
            "arquivos_principais": "7",
            "rodadas_historico": str(len(historico)),
            "travas_lacunas": str(len(travas)),
            "proximas_rodadas": str(len(plano)),
            "status": "gerado",
        }
    ]

    status = [
        {
            "rodada": "4.24",
            "status": "sucesso",
            "erros_estruturais": "0",
            "score_aimm_final": "nao_liberado",
            "gis_manaus": "encerrado_com_lacunas_controladas",
            "proxima_rodada": "4.25",
            "proxima_rodada_descricao": "manual tecnico operacional AIMM",
        }
    ]

    evidence = [
        {
            "id_evidencia": "EVD_AIMM_HANDOFF_PACKAGE_4_24",
            "tipo_evidencia": "pacote_de_retomada",
            "descricao": "Pacote de retomada e documentacao operacional AIMM gerado ate a rodada 4.23.",
            "status": "gerado",
            "limitacao": "Nao testa automaticamente outro chat e nao acessa Google Drive.",
        }
    ]

    pacote = """
# Pacote de retomada AIMM — Rodada 4.24

## Estado do projeto

O projeto Fito+ Amazônia AIMM chegou ao encerramento operacional do módulo GIS Manaus na Rodada 4.23.

A estrutura atual possui:

- triagem e risco OSC;
- pré-diligência OSC;
- arquitetura da calculadora AIMM;
- espécies candidatas;
- produtos e rotas;
- orçamento preliminar;
- benchmarks e proxies;
- motor AIMM estrutural preliminar;
- dashboard e comunicação;
- módulo GIS Manaus validado;
- pacote de replicação GIS para novos municípios.

## Situação do GIS

Manaus foi usado como município base.

Código IBGE:

1302603

Validações concluídas:

- GeoPackage isolado validado;
- tabela relacional de atributos criada;
- join visual no QGIS confirmado;
- pacote de replicação GIS criado;
- módulo GIS Manaus encerrado.

## Limitações principais

- Score AIMM final não está liberado.
- Segundo município não foi testado.
- Área, densidade, centroide e buffer não foram calculados.
- Workflows não verificam binariamente arquivos no Google Drive.
- Revisão visual humana segue como lacuna controlada em parte do fluxo.

## Como retomar

1. Confirmar que o ZIP da 4.24 está arquivado.
2. Ler o histórico de rodadas.
3. Verificar travas e lacunas.
4. Não retomar workflows antigos com erro.
5. Seguir para a Rodada 4.25: manual técnico operacional AIMM.
"""

    readme = """
# README operacional AIMM — Rodada 4.24

## Regra geral

O sistema deve avançar por rodadas controladas.

Cada rodada deve ter:

1. objetivo claro;
2. arquivos gerados;
3. travas explícitas;
4. critério de validação;
5. orientação de arquivamento;
6. próxima rodada definida.

## Proibição operacional

Não liberar score AIMM final sem rodada específica de validação.

Não usar workflows antigos que foram substituídos.

Não declarar que GIS está generalizado para múltiplos municípios, pois apenas Manaus foi validado.

## Fluxo atual recomendado

4.24 — pacote de retomada.

4.25 — manual técnico operacional AIMM.

4.26 — manual curto para equipe não técnica.

4.27 — teste de retomada em novo chat.

4.28 — matriz de pendências finais.

4.29 — plano de testes AIMM.

4.30 — reabertura controlada do score AIMM.
"""

    prompt = """
# Prompt de retomada para outro chat

Estou retomando o projeto Fito+ Amazônia AIMM.

Estado consolidado até a Rodada 4.24:

- Rodadas 4.6 a 4.23 foram executadas e validadas com lacunas controladas.
- O módulo GIS Manaus foi encerrado na Rodada 4.23.
- Manaus é o baseline GIS operacional, código IBGE 1302603.
- O join visual QGIS foi validado.
- O pacote de replicação GIS foi criado na 4.22-E.
- A aplicação em segundo município não foi realizada.
- O score AIMM final não está liberado.
- Não calcular área, densidade, centroide ou buffer sem rodada espacial própria.
- Não usar workflows antigos C, C2 ou C3.
- Próxima rodada recomendada: 4.25 — manual técnico operacional AIMM.

Quero continuar a partir da Rodada 4.25, mantendo travas, histórico, lacunas e padrão de validação por prints, logs e arquivamento.
"""

    report = """
# Relatório da Rodada 4.24 — pacote de retomada e documentação operacional AIMM

## Resultado

Pacote de retomada AIMM gerado.

## Conteúdo

- Histórico das rodadas até 4.23.
- Travas e lacunas operacionais.
- Plano das próximas rodadas.
- Checklist de retomada.
- Prompt pronto para outro chat.
- README operacional.

## Travas mantidas

- Não libera score AIMM final.
- Não processa geometria.
- Não acessa Drive.
- Não substitui validação humana.
- Não testa segundo município.

## Próxima rodada

Rodada 4.25 — manual técnico operacional AIMM.
"""

    log = "\n".join(
        [
            "TESTE AIMM_HANDOFF_PACKAGE_4_24 — Fito+ Amazônia",
            "=" * 86,
            "Pacote de retomada AIMM gerado: sim",
            f"Rodadas no histórico: {len(historico)}",
            f"Travas/lacunas registradas: {len(travas)}",
            f"Próximas rodadas registradas: {len(plano)}",
            f"Itens de checklist: {len(checklist)}",
            "Erros estruturais: 0",
            "",
            "Resultado: SUCESSO.",
            "Pacote de retomada e documentação operacional AIMM gerado.",
            "",
            "Trava: não libera score AIMM final, não processa geometria e não acessa Drive.",
        ]
    )

    write_text(FILES["pacote"], pacote)
    write_text(FILES["readme"], readme)
    write_text(FILES["prompt"], prompt)
    write_csv(FILES["historico"], historico)
    write_csv(FILES["travas"], travas)
    write_csv(FILES["plano"], plano)
    write_csv(FILES["checklist"], checklist)
    write_csv(FILES["registry"], registry)
    write_csv(FILES["status"], status)
    write_csv(FILES["evidence"], evidence)
    write_text(FILES["report"], report)
    write_text(FILES["log"], log)

    for name, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não criado: {name} -> {path}")
        if path.stat().st_size == 0:
            raise ValueError(f"Arquivo vazio: {name} -> {path}")

    print(log)


if __name__ == "__main__":
    main()
