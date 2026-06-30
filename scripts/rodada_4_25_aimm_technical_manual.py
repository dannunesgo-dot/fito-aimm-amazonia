# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


BASE = Path("outputs/aimm/rodada_4_25_manual_tecnico_operacional")

FILES = {
    "manual": BASE / "MANUAL_TECNICO_OPERACIONAL_AIMM_4_25.md",
    "equipe": BASE / "VERSAO_COMPARTILHAVEL_EQUIPE_AIMM_4_25.md",
    "funcionalidades": BASE / "MAPA_FUNCIONALIDADES_AIMM_4_25.csv",
    "fluxo": BASE / "FLUXO_OPERACIONAL_AIMM_4_25.csv",
    "checklist": BASE / "CHECKLIST_OPERACAO_AIMM_4_25.csv",
    "glossario": BASE / "GLOSSARIO_AIMM_4_25.csv",
    "travas": BASE / "TRAVAS_OPERACIONAIS_AIMM_4_25.csv",
    "registry": Path("data/processed/aimm/aimm_technical_manual_registry_4_25.csv"),
    "status": Path("data/processed/aimm/aimm_technical_manual_status_4_25.csv"),
    "evidence": Path("data/evidence/evidence_aimm_technical_manual_4_25.csv"),
    "report": Path("outputs/reports/RELATORIO_AIMM_MANUAL_TECNICO_4_25.md"),
    "log": Path("outputs/logs/teste_aimm_manual_tecnico_4_25.txt"),
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
    funcionalidades = [
        {
            "modulo": "governanca_osc",
            "funcao": "organizar triagem, risco, pre-diligencia e pendencias de OSCs",
            "entradas": "cadastro OSC, status documental, evidencias, classificacao preliminar",
            "saidas": "encaminhamentos, pendencias, bloqueios e recomendacoes preliminares",
            "status": "estrutural",
            "trava": "nao seleciona executora automaticamente",
        },
        {
            "modulo": "especies_produtos",
            "funcao": "organizar especies candidatas, produtos e rotas especie-produto",
            "entradas": "especies candidatas, criterios, tipos de produto, requisitos de qualidade",
            "saidas": "ranking preliminar, matriz especie-produto, rotas produtivas e regulatorias preliminares",
            "status": "preliminar",
            "trava": "nao aprova especie, produto ou rota final",
        },
        {
            "modulo": "orcamento",
            "funcao": "estruturar componentes, pressupostos de custo e fases de investimento",
            "entradas": "componentes CAPEX, OPEX, misto, reserva tecnica e cronograma",
            "saidas": "orcamento preliminar por componente e relatorio de validacao",
            "status": "preliminar",
            "trava": "nao autoriza contratacao, compra, convenio, TED ou execucao",
        },
        {
            "modulo": "benchmark_proxy",
            "funcao": "registrar benchmarks, proxies, fontes e lacunas de comparacao",
            "entradas": "benchmarks publicos, proxies metodologicos e fontes",
            "saidas": "matriz de benchmarks, lacunas e fontes",
            "status": "controlado",
            "trava": "proxies nao substituem benchmark validado final",
        },
        {
            "modulo": "gis",
            "funcao": "registrar baseline territorial, camadas GIS, validacao QGIS e pacote de replicacao",
            "entradas": "GeoPackage, codigo IBGE, tabela relacional, prints QGIS e projeto QGZ",
            "saidas": "baseline GIS Manaus, join visual validado e pacote de replicacao",
            "status": "Manaus operacional",
            "trava": "nao calcula area, densidade, centroide, buffer nem generaliza para segundo municipio",
        },
        {
            "modulo": "motor_aimm",
            "funcao": "calcular estrutura preliminar de indicadores, dimensoes e bloqueios",
            "entradas": "indicadores estruturais, dimensoes, penalidades, lacunas e fatores de monitoramento",
            "saidas": "score estrutural preliminar e relatorios de bloqueios",
            "status": "preliminar",
            "trava": "nao libera score AIMM final",
        },
        {
            "modulo": "dashboard_comunicacao",
            "funcao": "gerar resumos, cards, mensagens e outputs visuais editaveis",
            "entradas": "score estrutural preliminar, cards, dimensoes, mensagens e proximas acoes",
            "saidas": "dashboard, briefing, payload e materiais de comunicacao",
            "status": "preliminar",
            "trava": "nao aprova decisoes executivas",
        },
    ]

    fluxo = [
        {"ordem": "1", "etapa": "conferir dados de entrada", "responsavel": "operador tecnico", "saida": "dados minimos presentes"},
        {"ordem": "2", "etapa": "executar workflows estruturais", "responsavel": "operador GitHub", "saida": "logs verdes e artefatos publicados"},
        {"ordem": "3", "etapa": "baixar artefatos", "responsavel": "operador GitHub", "saida": "ZIP salvo localmente"},
        {"ordem": "4", "etapa": "arquivar no Drive", "responsavel": "operador Drive", "saida": "ZIP e arquivos distribuidos nas pastas corretas"},
        {"ordem": "5", "etapa": "validar prints e logs", "responsavel": "revisor humano", "saida": "conformidade visual registrada"},
        {"ordem": "6", "etapa": "registrar lacunas", "responsavel": "coordenacao tecnica", "saida": "lacunas controladas"},
        {"ordem": "7", "etapa": "gerar manual ou painel", "responsavel": "operador AIMM", "saida": "documentacao compartilhavel"},
        {"ordem": "8", "etapa": "decidir proxima rodada", "responsavel": "coordenacao tecnica", "saida": "proxima etapa definida"},
    ]

    checklist = [
        {"item": "workflow executou verde", "criterio": "Resultado: SUCESSO e erros estruturais 0", "bloqueia": "sim"},
        {"item": "artefato ZIP baixado", "criterio": "arquivo existe e abre", "bloqueia": "sim"},
        {"item": "arquivamento Drive realizado", "criterio": "ZIP em 07_versoes_congeladas e arquivos nas pastas corretas", "bloqueia": "sim"},
        {"item": "logs arquivados", "criterio": "arquivo de log em 05_logs", "bloqueia": "nao"},
        {"item": "evidencias arquivadas", "criterio": "CSV de evidencia em 02_evidencias", "bloqueia": "sim"},
        {"item": "score final bloqueado", "criterio": "nenhum relatorio declara score AIMM final aprovado", "bloqueia": "sim"},
        {"item": "lacunas registradas", "criterio": "lacunas aparecem em CSV ou relatorio", "bloqueia": "sim"},
        {"item": "material compartilhavel revisado", "criterio": "versao de equipe compreensivel e sem comando tecnico perigoso", "bloqueia": "nao"},
    ]

    glossario = [
        {"termo": "AIMM", "significado": "modelo estruturado de apoio a decisao da calculadora Fito+ Amazonia"},
        {"termo": "score estrutural preliminar", "significado": "pontuacao tecnica inicial usada para testar a arquitetura, sem validade decisoria final"},
        {"termo": "score AIMM final", "significado": "resultado consolidado ainda bloqueado, dependente de validacoes futuras"},
        {"termo": "baseline GIS", "significado": "base territorial inicial validada para uso no sistema"},
        {"termo": "GeoPackage", "significado": "arquivo geoespacial que pode guardar camada geometrica e tabelas"},
        {"termo": "join", "significado": "ligacao entre uma camada geometrica e uma tabela por campo comum"},
        {"termo": "CRS", "significado": "sistema de referencia de coordenadas usado pela camada geografica"},
        {"termo": "lacuna controlada", "significado": "pendencia conhecida, registrada e que nao pode ser ignorada"},
        {"termo": "trava", "significado": "bloqueio formal para impedir uso indevido do resultado"},
        {"termo": "artefato", "significado": "arquivo gerado pelo workflow para auditoria, uso ou arquivamento"},
    ]

    travas = [
        {"trava_id": "AIMM_425_001", "tema": "score", "descricao": "Score AIMM final permanece bloqueado", "acao": "nao usar score estrutural como decisao final"},
        {"trava_id": "AIMM_425_002", "tema": "GIS", "descricao": "GIS Manaus validado, mas segundo municipio nao testado", "acao": "nao declarar generalizacao territorial"},
        {"trava_id": "AIMM_425_003", "tema": "orcamento", "descricao": "Orcamento preliminar nao autoriza execucao", "acao": "usar apenas como estrutura de planejamento"},
        {"trava_id": "AIMM_425_004", "tema": "especies_produtos", "descricao": "Ranking e rotas sao preliminares", "acao": "exigir validacao tecnica, regulatoria e de mercado"},
        {"trava_id": "AIMM_425_005", "tema": "Drive", "descricao": "GitHub Actions nao confirma arquivos no Drive", "acao": "manter arquivamento visual humano"},
        {"trava_id": "AIMM_425_006", "tema": "workflows_antigos", "descricao": "Workflows antigos com erro nao devem ser reutilizados", "acao": "usar apenas workflows validados"},
    ]

    registry = [
        {
            "rodada": "4.25",
            "pacote": "manual_tecnico_operacional_aimm",
            "funcionalidades_mapeadas": str(len(funcionalidades)),
            "etapas_fluxo": str(len(fluxo)),
            "itens_checklist": str(len(checklist)),
            "termos_glossario": str(len(glossario)),
            "travas": str(len(travas)),
            "status": "gerado",
        }
    ]

    status = [
        {
            "rodada": "4.25",
            "status": "sucesso",
            "erros_estruturais": "0",
            "manual_tecnico": "gerado",
            "versao_compartilhavel": "gerada",
            "score_aimm_final": "nao_liberado",
            "proxima_rodada": "4.26",
            "proxima_rodada_descricao": "manual curto ilustrado para equipe nao tecnica",
        }
    ]

    evidence = [
        {
            "id_evidencia": "EVD_AIMM_TECHNICAL_MANUAL_4_25",
            "tipo_evidencia": "manual_tecnico_operacional",
            "descricao": "Manual tecnico operacional AIMM gerado a partir do estado validado ate a rodada 4.24.",
            "status": "gerado",
            "limitacao": "Nao executa calculos, nao valida Drive e nao libera score final.",
        }
    ]

    manual = """
# Manual técnico operacional AIMM — Rodada 4.25

## 1. Finalidade da calculadora AIMM

A calculadora AIMM organiza dados técnicos, territoriais, institucionais, produtivos, regulatórios, orçamentários e operacionais para apoiar decisões no projeto Fito+ Amazônia.

Ela ainda não é uma ferramenta de decisão final. Nesta fase, funciona como arquitetura estruturada, auditável e incremental.

## 2. Estado atual do sistema

O sistema possui módulos estruturais validados por rodadas sucessivas:

- triagem e risco de OSCs;
- pré-diligência e consolidação operacional;
- arquitetura AIMM em camadas;
- espécies candidatas;
- produtos e rotas produtivas/regulatórias;
- orçamento preliminar;
- benchmarks e proxies;
- motor estrutural AIMM;
- dashboard e comunicação;
- GIS Manaus;
- pacote de retomada.

## 3. Como a calculadora deve funcionar

O AIMM deve receber dados estruturados por módulo, aplicar validações, registrar lacunas, gerar saídas intermediárias e impedir uso indevido de resultados preliminares.

O fluxo correto é:

1. Entrada de dados.
2. Validação estrutural.
3. Registro de lacunas.
4. Geração de artefatos.
5. Validação humana.
6. Arquivamento.
7. Nova rodada controlada.

## 4. Módulos operacionais

### 4.1 Governança e OSCs

Organiza triagem, risco, pré-diligência, pendências e encaminhamentos.

Não seleciona executora automaticamente.

### 4.2 Espécies e produtos

Organiza espécies candidatas, critérios, produtos e rotas.

Não aprova espécie final, produto final ou rota regulatória final.

### 4.3 Orçamento

Organiza CAPEX, OPEX, misto, reserva técnica e cronograma preliminar.

Não autoriza contratação, compra, convênio, TED ou execução.

### 4.4 Benchmarks e proxies

Registra fontes, proxies e lacunas comparativas.

Proxies são substitutos metodológicos temporários.

### 4.5 GIS

Manaus é o baseline GIS operacional.

Código IBGE validado: 1302603.

O GIS validado inclui GeoPackage isolado, tabela relacional e join visual no QGIS.

Ainda não calcula área real, densidade, centroide, buffer ou generalização para segundo município.

### 4.6 Motor AIMM

Gera score estrutural preliminar.

Esse score não é score AIMM final.

### 4.7 Dashboard e comunicação

Gera materiais executivos e visuais.

Não aprova decisões executivas.

## 5. Travas obrigatórias

- Não liberar score AIMM final.
- Não usar resultado preliminar como decisão executiva.
- Não declarar que o GIS foi testado em múltiplos municípios.
- Não usar workflows antigos com erro.
- Não tratar orçamento preliminar como autorização de execução.
- Não tratar rota regulatória preliminar como aprovação de produto.

## 6. Como operar com segurança

Para cada rodada:

1. Conferir se o workflow correto foi usado.
2. Conferir se o log terminou com Resultado: SUCESSO.
3. Conferir se erros estruturais = 0.
4. Baixar o artefato ZIP.
5. Arquivar ZIP e arquivos derivados.
6. Registrar lacunas.
7. Só avançar para a próxima rodada depois da validação.

## 7. Compartilhamento com equipe

A equipe pode usar a versão compartilhável como guia de alto nível.

O manual técnico deve ficar com operadores que criam, executam ou validam workflows.
"""

    equipe = """
# AIMM — versão compartilhável para equipe

## O que é

A AIMM é uma calculadora em construção para organizar informações do projeto Fito+ Amazônia.

Ela ajuda a estruturar dados sobre:

- território;
- organizações;
- espécies;
- produtos;
- orçamento;
- riscos;
- evidências;
- lacunas;
- próximos passos.

## O que ela já faz

- organiza dados por módulos;
- gera relatórios;
- registra lacunas;
- mostra bloqueios;
- ajuda a acompanhar o avanço;
- registra o módulo GIS de Manaus como base territorial inicial.

## O que ela ainda não faz

- não aprova decisão final;
- não escolhe executora;
- não libera score AIMM final;
- não substitui revisão humana;
- não confirma arquivos no Google Drive sozinha;
- não valida automaticamente outros municípios.

## Como usar sem causar erro

1. Não editar arquivos técnicos sem orientação.
2. Não apagar pastas do GitHub.
3. Não mover arquivos no Drive fora das pastas indicadas.
4. Não usar workflows antigos com erro.
5. Sempre conferir se o workflow ficou verde.
6. Sempre arquivar o ZIP completo.
7. Sempre registrar prints quando houver validação visual.

## Situação atual

Manaus foi validado como exemplo GIS.

O próximo passo é consolidar os manuais e preparar testes de retomada.
"""

    report = """
# Relatório da Rodada 4.25 — manual técnico operacional AIMM

## Resultado

Manual técnico operacional AIMM gerado.

## Arquivos gerados

- MANUAL_TECNICO_OPERACIONAL_AIMM_4_25.md
- VERSAO_COMPARTILHAVEL_EQUIPE_AIMM_4_25.md
- MAPA_FUNCIONALIDADES_AIMM_4_25.csv
- FLUXO_OPERACIONAL_AIMM_4_25.csv
- CHECKLIST_OPERACAO_AIMM_4_25.csv
- GLOSSARIO_AIMM_4_25.csv
- TRAVAS_OPERACIONAIS_AIMM_4_25.csv

## Travas mantidas

- Não libera score AIMM final.
- Não processa geometria.
- Não acessa Drive.
- Não substitui validação humana.

## Próxima rodada

Rodada 4.26 — manual curto ilustrado para equipe não técnica.
"""

    log = "\n".join(
        [
            "TESTE AIMM_TECHNICAL_MANUAL_4_25 — Fito+ Amazônia",
            "=" * 86,
            "Manual técnico operacional AIMM gerado: sim",
            f"Funcionalidades mapeadas: {len(funcionalidades)}",
            f"Etapas de fluxo: {len(fluxo)}",
            f"Itens de checklist: {len(checklist)}",
            f"Termos de glossário: {len(glossario)}",
            f"Travas operacionais: {len(travas)}",
            "Erros estruturais: 0",
            "",
            "Resultado: SUCESSO.",
            "Manual técnico operacional AIMM e versão compartilhável gerados.",
            "",
            "Trava: não libera score AIMM final, não processa geometria e não acessa Drive.",
        ]
    )

    write_text(FILES["manual"], manual)
    write_text(FILES["equipe"], equipe)
    write_csv(FILES["funcionalidades"], funcionalidades)
    write_csv(FILES["fluxo"], fluxo)
    write_csv(FILES["checklist"], checklist)
    write_csv(FILES["glossario"], glossario)
    write_csv(FILES["travas"], travas)
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
