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


def write_text(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


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
            "uso_pratico": "baixar o ZIP e organizar nas pastas do Drive",
            "risco": "medio",
            "observacao": "workflow não confirma Drive automaticamente",
        },
        {
            "funcionalidade": "API GitHub-Drive",
            "situacao": "nao_implementada",
            "uso_pratico": "ainda não há upload/download automático entre GitHub e Drive",
            "risco": "alto_se_assumir_que_funciona",
            "observacao": "exige rodada própria de autenticação, secrets e testes",
        },
        {
            "funcionalidade": "Módulo de ingestão de arquivos",
            "situacao": "nao_implementado",
            "uso_pratico": "ainda não há entrada automática padronizada para arquivos novos",
            "risco": "alto",
            "observacao": "deve ser construído em rodada específica",
        },
        {
            "funcionalidade": "Módulo de extração e normalização de dados",
            "situacao": "nao_implementado",
            "uso_pratico": "ainda não extrai, valida e normaliza dados automaticamente",
            "risco": "alto",
            "observacao": "deve ser construído antes do score operacional",
        },
        {
            "funcionalidade": "Benchmarks e proxies",
            "situacao": "estrutura_preliminar",
            "uso_pratico": "registrar benchmarks, fontes, proxies e lacunas",
            "risco": "medio",
            "observacao": "não há coleta automática externa validada",
        },
        {
            "funcionalidade": "Módulo GIS Manaus",
            "situacao": "funciona_com_lacunas",
            "uso_pratico": "baseline territorial Manaus e join visual QGIS",
            "risco": "medio",
            "observacao": "não calcula área, densidade, centroide ou buffer",
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
    ]

    checklist = [
        {
            "ordem": "1",
            "acao": "Conferir workflow verde",
            "como_fazer": "abrir Actions e verificar status succeeded",
            "nao_fazer": "não seguir com workflow vermelho",
        },
        {
            "ordem": "2",
            "acao": "Abrir o log",
            "como_fazer": "procurar Resultado: SUCESSO e Erros estruturais: 0",
            "nao_fazer": "não validar somente pelo nome da rodada",
        },
        {
            "ordem": "3",
            "acao": "Baixar o ZIP",
            "como_fazer": "baixar o artefato publicado pelo GitHub Actions",
            "nao_fazer": "não usar execução antiga ou link quebrado",
        },
        {
            "ordem": "4",
            "acao": "Arquivar o ZIP",
            "como_fazer": "salvar ZIP completo em 07_versoes_congeladas",
            "nao_fazer": "não apagar o ZIP depois de extrair",
        },
        {
            "ordem": "5",
            "acao": "Arquivar arquivos internos",
            "como_fazer": "mover relatórios, logs, evidências e outputs para pastas indicadas",
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
            "nao_fazer": "não declarar sincronização automática Drive-GitHub",
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
            "ingestao_arquivos": "nao_implementada",
            "benchmarks_automaticos": "nao_implementados",
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
            "ingestao_arquivos": "nao_implementada",
            "benchmarks_automaticos": "nao_implementados",
            "proxima_rodada": "4.27",
            "proxima_rodada_descricao": "diagnostico funcional de automacoes, Drive-GitHub e modulos de ingestao",
        }
    ]

    evidence = [
        {
            "id_evidencia": "EVD_AIMM_SHORT_TEAM_MANUAL_4_26",
            "tipo_evidencia": "manual_curto_equipe",
            "descricao": "Manual curto ilustrado para equipe não técnica, com status real das funcionalidades.",
            "status": "gerado",
            "limitacao": "Não ativa API Drive-GitHub, não processa benchmarks e não libera score final.",
        }
    ]

    manual_curto = [
        "# Manual curto ilustrado AIMM — equipe não técnica",
        "",
        "## 1. O que é o AIMM",
        "",
        "O AIMM é uma calculadora em construção para organizar informações do projeto Fito+ Amazônia.",
        "",
        "Ela ajuda a reunir, conferir e documentar informações sobre território, organizações, espécies, produtos, orçamento, riscos, benchmarks, GIS, lacunas e próximos passos.",
        "",
        "## 2. O que já funciona",
        "",
        "| Parte | Funciona? | Observação |",
        "|---|---|---|",
        "| GitHub Actions por rodada | sim | gera arquivos e logs |",
        "| Artefatos ZIP | sim | devem ser baixados e arquivados |",
        "| Manual técnico | sim | gerado na 4.25 |",
        "| Manual curto | sim | gerado nesta 4.26 |",
        "| GIS Manaus | sim, com lacunas | não calcula área, densidade, centroide ou buffer |",
        "| Dashboard preliminar | sim | não aprova decisão final |",
        "| Pacote de retomada | sim | ajuda a continuar em outro chat |",
        "",
        "## 3. O que ainda não funciona automaticamente",
        "",
        "| Parte | Situação |",
        "|---|---|",
        "| API automática GitHub-Drive | não implementada |",
        "| Upload automático para o Drive | não implementado |",
        "| Download automático do Drive pelo GitHub | não implementado |",
        "| Módulo de ingestão de arquivos | não implementado |",
        "| Extração e normalização automática de dados | não implementada |",
        "| Coleta automática de benchmarks | não implementada |",
        "| Score AIMM final | bloqueado |",
        "| Segundo município GIS | não testado |",
        "",
        "## 4. Como a equipe deve usar",
        "",
        "1. Receber orientação da coordenação.",
        "2. Abrir o material compartilhável.",
        "3. Não editar scripts.",
        "4. Não apagar arquivos do GitHub.",
        "5. Não mover arquivos do Drive sem orientação.",
        "6. Conferir se o workflow ficou verde.",
        "7. Arquivar o ZIP completo.",
        "8. Registrar dúvidas e lacunas.",
        "",
        "## 5. Fluxo simples",
        "",
        "ENTRADA DE DADOS → VALIDAÇÃO NO GITHUB → ARTEFATO ZIP → ARQUIVAMENTO NO DRIVE → REVISÃO HUMANA → PRÓXIMA RODADA",
        "",
        "## 6. Avisos importantes",
        "",
        "- Resultado preliminar não é decisão final.",
        "- Score AIMM final ainda não existe.",
        "- API Drive-GitHub ainda não está ativa.",
        "- Benchmarks automáticos ainda não estão ativos.",
        "- GIS Manaus é base validada, mas não prova replicação para todos os municípios.",
    ]

    guia_operador = [
        "# Guia rápido do operador AIMM — Rodada 4.26",
        "",
        "## Antes de executar uma rodada",
        "",
        "1. Confirmar o nome correto do workflow.",
        "2. Confirmar se o workflow é novo ou validado.",
        "3. Confirmar que não está usando versão antiga com erro.",
        "4. Executar manualmente pelo botão Run workflow.",
        "5. Aguardar status verde.",
        "",
        "## Depois de executar",
        "",
        "1. Abrir log.",
        "2. Confirmar Resultado: SUCESSO.",
        "3. Confirmar Erros estruturais: 0.",
        "4. Baixar artefato ZIP.",
        "5. Arquivar ZIP completo.",
        "6. Distribuir arquivos internos nas pastas corretas.",
        "7. Registrar print de validação.",
        "",
        "## Atenção",
        "",
        "A API Drive-GitHub não está ativa.",
        "",
        "Até que haja rodada específica de integração, todo arquivamento no Drive é manual.",
    ]

    fluxo_mermaid = [
        "flowchart TD",
        "    A[Equipe reúne dados] --> B[Operador confere entrada]",
        "    B --> C[Executa workflow no GitHub]",
        "    C --> D{Workflow verde?}",
        "    D -- Não --> E[Parar e corrigir erro]",
        "    D -- Sim --> F[Baixar artefato ZIP]",
        "    F --> G[Arquivar ZIP no Drive]",
        "    G --> H[Arquivar relatórios, logs e evidências]",
        "    H --> I[Revisão humana]",
        "    I --> J{Há lacuna?}",
        "    J -- Sim --> K[Registrar lacuna controlada]",
        "    J -- Não --> L[Validar rodada]",
        "    K --> L",
        "    L --> M[Avançar para próxima rodada]",
    ]

    perguntas = [
        "# Perguntas e respostas — AIMM para equipe",
        "",
        "## 1. A calculadora já decide sozinha?",
        "",
        "Não. Ela organiza informações e gera apoio técnico. Decisão final continua bloqueada.",
        "",
        "## 2. O score AIMM final já existe?",
        "",
        "Não. Existe apenas score estrutural preliminar em rodadas anteriores.",
        "",
        "## 3. O Drive está conectado automaticamente ao GitHub?",
        "",
        "Não. O arquivamento no Drive ainda é manual.",
        "",
        "## 4. Posso alterar arquivos no GitHub?",
        "",
        "Somente com orientação. Alterações erradas podem quebrar workflows.",
        "",
        "## 5. Posso usar o GIS de Manaus para outros municípios?",
        "",
        "Não diretamente. Manaus foi validado. Outros municípios precisam replicação própria.",
        "",
        "## 6. Benchmarks já são coletados automaticamente?",
        "",
        "Não. Há estrutura preliminar de benchmarks e proxies, mas não coleta automática validada.",
        "",
        "## 7. O que faço quando o workflow fica vermelho?",
        "",
        "Parar. Não arquivar como válido. Registrar print do erro e corrigir antes de avançar.",
    ]

    report = [
        "# Relatório da Rodada 4.26 — manual curto ilustrado para equipe não técnica",
        "",
        "## Resultado",
        "",
        "Manual curto ilustrado gerado.",
        "",
        "## Conteúdo",
        "",
        "- Manual curto para equipe.",
        "- Guia rápido do operador.",
        "- Fluxo visual editável em Mermaid.",
        "- Status real das funcionalidades AIMM.",
        "- Checklist de uso seguro.",
        "- Perguntas e respostas.",
        "",
        "## Pontos críticos registrados",
        "",
        "- API GitHub-Drive não implementada.",
        "- Automação Drive não implementada.",
        "- Módulo de ingestão de arquivos não implementado.",
        "- Extração e normalização automática de dados não implementada.",
        "- Benchmarks automáticos não implementados.",
        "- Score AIMM final não liberado.",
        "- GIS validado apenas para Manaus.",
        "",
        "## Próxima rodada recomendada",
        "",
        "Rodada 4.27 — diagnóstico funcional de automações, Drive-GitHub e módulos de ingestão.",
    ]

    log_lines = [
        "TESTE AIMM_SHORT_TEAM_MANUAL_4_26 — Fito+ Amazônia",
        "=" * 86,
        "Manual curto ilustrado gerado: sim",
        "Guia rápido do operador gerado: sim",
        "Fluxo visual Mermaid gerado: sim",
        f"Funcionalidades classificadas: {len(status_funcionalidades)}",
        f"Itens de checklist: {len(checklist)}",
        "API GitHub-Drive ativa: nao",
        "Automacao Drive ativa: nao",
        "Ingestao automatica de arquivos ativa: nao",
        "Benchmarks automaticos ativos: nao",
        "Score AIMM final liberado: nao",
        "Erros estruturais: 0",
        "",
        "Resultado: SUCESSO.",
        "Manual curto ilustrado para equipe não técnica gerado.",
        "",
        "Trava: não ativa API, não acessa Drive, não processa benchmarks e não libera score AIMM final.",
    ]

    write_text(FILES["manual_curto"], manual_curto)
    write_text(FILES["guia_operador"], guia_operador)
    write_text(FILES["fluxo_mermaid"], fluxo_mermaid)
    write_csv(FILES["status_funcionalidades"], status_funcionalidades)
    write_csv(FILES["checklist"], checklist)
    write_text(FILES["perguntas"], perguntas)
    write_csv(FILES["registry"], registry)
    write_csv(FILES["status"], status)
    write_csv(FILES["evidence"], evidence)
    write_text(FILES["report"], report)
    write_text(FILES["log"], log_lines)

    for name, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não criado: {name} -> {path}")
        if path.stat().st_size == 0:
            raise ValueError(f"Arquivo vazio: {name} -> {path}")

    print("\n".join(log_lines))


if __name__ == "__main__":
    main()
