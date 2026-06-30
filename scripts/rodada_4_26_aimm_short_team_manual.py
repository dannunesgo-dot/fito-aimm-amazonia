# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


BASE = Path("outputs/aimm/rodada_4_26_manual_curto_equipe")

FILES = {
    "manual_curto": BASE / "MANUAL_CURTO_ILUSTRADO_EQUIPE_AIMM_4_26.md",
    "guia_operador": BASE / "GUIA_RAPIDO_OPERADOR_AIMM_4_26.md",
    "fluxo_mermaid": BASE / "FLUXO_VISUAL_AIMM_4_26.mmd",
    "status_funcionalidades": BASE / "STATUS_FUNCIONALIDADES_AIMM_4_26.csv",
    "checklist": BASE / "CHECKLIST_USO_SEGURO_EQUIPE_AIMM_4_26.csv",
    "perguntas": BASE / "PERGUNTAS_RESPOSTAS_AIMM_4_26.md",
    "registry": Path("data/processed/aimm/aimm_short_team_manual_registry_4_26.csv"),
    "status": Path("data/processed/aimm/aimm_short_team_manual_status_4_26.csv"),
    "evidence": Path("data/evidence/evidence_aimm_short_team_manual_4_26.csv"),
    "report": Path("outputs/reports/RELATORIO_AIMM_MANUAL_CURTO_EQUIPE_4_26.md"),
    "log": Path("outputs/logs/teste_aimm_manual_curto_equipe_4_26.txt"),
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
    status_funcionalidades = [
        {
            "funcionalidade": "GitHub Actions por rodada",
            "situacao": "funciona",
            "uso_pratico": "executar rodadas controladas e gerar artefatos",
            "risco": "baixo",
            "observacao": "usar apenas workflows validados",
        },
        {
            "funcionalidade": "Geração de artefatos ZIP",
            "situacao": "funciona",
            "uso_pratico": "baixar pacote de cada rodada",
            "risco": "baixo",
            "observacao": "arquivar ZIP completo em 07_versoes_congeladas",
        },
        {
            "funcionalidade": "Arquivamento no Google Drive",
            "situacao": "manual",
            "uso_pratico": "usuário baixa o ZIP e organiza nas pastas do Drive",
            "risco": "medio",
            "observacao": "workflow não confirma Drive automaticamente",
        },
        {
            "funcionalidade": "API GitHub-Drive",
            "situacao": "nao_implementada",
            "uso_pratico": "ainda não há upload/download automático entre GitHub e Drive",
            "risco": "alto_se_assumir_que_funciona",
            "observacao": "exige rodada própria de autenticação e testes",
        },
        {
            "funcionalidade": "Módulo GIS Manaus",
            "situacao": "funciona_com_lacunas",
            "uso_pratico": "baseline territorial Manaus e join visual QGIS",
            "risco": "medio",
            "observacao": "não calcula área, densidade, centroide ou buffer",
        },
        {
            "funcionalidade": "Replicação GIS para novo município",
            "situacao": "preparada_nao_testada",
            "uso_pratico": "usar pacote 4.22-E como guia",
            "risco": "medio",
            "observacao": "segundo município ainda não foi testado",
        },
        {
            "funcionalidade": "Benchmarks e proxies",
            "situacao": "estrutura_preliminar",
            "uso_pratico": "registrar benchmarks, fontes, proxies e lacunas",
            "risco": "medio",
            "observacao": "não há coleta automática externa validada",
        },
        {
            "funcionalidade": "Motor AIMM",
            "situacao": "estrutural_preliminar",
            "uso_pratico": "calcular score estrutural preliminar",
            "risco": "alto_se_usar_como_final",
            "observacao": "score AIMM final permanece bloqueado",
        },
        {
            "funcionalidade": "Dashboard e comunicação",
            "situacao": "funciona_preliminar",
            "uso_pratico": "gerar cards, briefing e outputs visuais",
            "risco": "medio",
            "observacao": "não aprova decisão executiva",
        },
        {
            "funcionalidade": "Retomada em outro chat",
            "situacao": "preparada",
            "uso_pratico": "usar pacote 4.24",
            "risco": "baixo",
            "observacao": "ainda precisa teste prático de retomada",
        },
    ]

    checklist = [
        {
            "ordem": "1",
            "acao": "Conferir se o workflow ficou verde",
            "como_fazer": "abrir Actions e verificar status succeeded",
            "nao_fazer": "não seguir com workflow vermelho",
        },
        {
            "ordem": "2",
            "acao": "Abrir o log",
            "como_fazer": "procurar Resultado: SUCESSO e Erros estruturais: 0",
            "nao_fazer": "não validar só pelo nome da rodada",
        },
        {
            "ordem": "3",
            "acao": "Baixar o ZIP",
            "como_fazer": "baixar artefato publicado pelo GitHub Actions",
            "nao_fazer": "não usar link quebrado ou execução antiga",
        },
        {
            "ordem": "4",
            "acao": "Arquivar o ZIP",
            "como_fazer": "salvar ZIP completo em 07_versoes_congeladas",
            "nao_fazer": "não apagar ZIP após extrair",
        },
        {
            "ordem": "5",
            "acao": "Arquivar arquivos internos",
            "como_fazer": "mover relatórios, logs, evidências e outputs para as pastas indicadas",
            "nao_fazer": "não misturar GIS, evidências, logs e relatórios",
        },
        {
            "ordem": "6",
            "acao": "Registrar lacunas",
            "como_fazer": "manter lacunas em CSV e relatório",
            "nao_fazer": "não esconder pendência operacional",
        },
        {
            "ordem": "7",
            "acao": "Compartilhar somente material apropriado",
            "como_fazer": "usar manual curto para equipe e manual técnico para operadores",
            "nao_fazer": "não compartilhar scripts como instrução para equipe não técnica",
        },
        {
            "ordem": "8",
            "acao": "Manter score AIMM bloqueado",
            "como_fazer": "tratar todo score atual como preliminar",
            "nao_fazer": "não usar score estrutural como decisão final",
        },
        {
            "ordem": "9",
            "acao": "Não presumir API Drive-GitHub",
            "como_fazer": "arquivar manualmente até existir rodada de integração",
            "nao_fazer": "não dizer que Drive e GitHub estão sincronizados automaticamente",
        },
    ]

    registry = [
        {
            "rodada": "4.26",
            "pacote": "manual_curto_ilustrado_equipe_nao_tecnica",
            "status_funcionalidades": str(len(status_funcionalidades)),
            "itens_checklist": str(len(checklist)),
            "fluxo_visual": "mermaid_editavel",
            "api_drive_github": "nao_implementada",
            "score_aimm_final": "nao_liberado",
            "status": "gerado",
        }
    ]

    status = [
        {
            "rodada": "4.26",
            "status": "sucesso",
            "erros_estruturais": "0",
            "manual_curto": "gerado",
            "fluxo_visual": "gerado",
            "api_drive_github": "nao_implementada",
            "automacao_drive": "nao_implementada",
            "benchmarks_automaticos": "nao_implementados",
            "proxima_rodada": "4.27",
            "proxima_rodada_descricao": "diagnostico funcional de automacoes, Drive-GitHub e modulos de ingestao",
        }
    ]

    evidence = [
        {
            "id_evidencia": "EVD_AIMM_SHORT_TEAM_MANUAL_4_26",
            "tipo_evidencia": "manual_curto_equipe",
            "descricao": "Manual curto ilustrado para uso por equipe não técnica, com status real das funcionalidades.",
            "status": "gerado",
            "limitacao": "Não ativa API Drive-GitHub, não processa benchmarks e não libera score final.",
        }
    ]

    manual_curto = """
# Manual curto ilustrado AIMM — equipe não técnica

## 1. O que é o AIMM

O AIMM é uma calculadora em construção para organizar informações do projeto Fito+ Amazônia.

Ela ajuda a reunir, conferir e documentar informações sobre:

- território;
- organizações;
- espécies;
- produtos;
- orçamento;
- riscos;
- benchmarks;
- GIS;
- lacunas;
- próximos passos.

## 2. O que já funciona

| Parte | Funciona? | Observação |
|---|---|---|
| GitHub Actions por rodada | sim | gera arquivos e logs |
| Artefatos ZIP | sim | devem ser baixados e arquivados |
| Manual técnico | sim | gerado na 4.25 |
| Manual curto | sim | gerado nesta 4.26 |
| GIS Manaus | sim, com lacunas | não calcula área, densidade, centroide ou buffer |
| Dashboard preliminar | sim | não aprova decisão final |
| Pacote de retomada | sim | ajuda a continuar em outro chat |

## 3. O que ainda não funciona automaticamente

| Parte | Situação |
|---|---|
| API automática GitHub-Drive | não implementada |
| Upload automático para o Drive | não implementado |
| Download automático do Drive pelo GitHub | não implementado |
| Coleta automática de benchmarks | não implementada |
| Score AIMM final | bloqueado |
| Segundo município GIS | não testado |

## 4. Como a equipe deve usar

```text
1. Receber orientação da coordenação.
2. Abrir o material compartilhável.
3. Não editar scripts.
4. Não apagar arquivos do GitHub.
5. Não mover arquivos do Drive sem orientação.
6. Conferir se o workflow ficou verde.
7. Arquivar o ZIP completo.
8. Registrar dúvidas e lacunas.
