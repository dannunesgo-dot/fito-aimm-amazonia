
from __future__ import annotations

import csv
import json
import html
from pathlib import Path
from typing import Any
import yaml


RULES = Path("config/aimm_communication_rules.yaml")
MESSAGES_SEED = Path("data/reference/aimm_communication_messages_seed.csv")
LAYOUT_SEED = Path("data/reference/aimm_visual_layout_seed.csv")

DASH_SUMMARY = Path("data/processed/aimm_executive_summary.csv")
DASH_CARDS = Path("data/processed/aimm_dashboard_cards.csv")
DASH_AXES = Path("data/processed/aimm_dashboard_axes_view.csv")
DASH_NEXT_ACTIONS = Path("data/processed/aimm_next_actions.csv")
DASH_PAYLOAD = Path("outputs/reports/aimm_dashboard_payload.json")

OUT_MESSAGES = Path("data/processed/aimm_communication_messages.csv")
OUT_VISUAL_INDEX = Path("data/processed/aimm_visual_outputs_index.csv")
OUT_PACKAGE_MANIFEST = Path("data/processed/aimm_communication_package_manifest.csv")
OUT_EVIDENCE = Path("data/evidence/evidence_aimm_communication.csv")

OUT_HTML = Path("outputs/visuals/aimm_dashboard_executivo.html")
OUT_SVG = Path("outputs/visuals/aimm_dashboard_cards.svg")
OUT_MERMAID = Path("outputs/visuals/aimm_dashboard_flow.mmd")
OUT_BRIEF = Path("outputs/reports/aimm_communication_brief.md")
OUT_JSON = Path("outputs/reports/aimm_communication_payload.json")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo obrigatório ausente: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        w.writeheader()
        w.writerows(rows)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo obrigatório ausente: {path}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def ensure_dashboard_outputs() -> None:
    required = [DASH_SUMMARY, DASH_CARDS, DASH_AXES, DASH_NEXT_ACTIONS]
    if all(p.exists() for p in required):
        return

    try:
        from fito_aimm.aimm_dashboard import execute_aimm_dashboard
    except Exception as exc:
        missing = ", ".join(str(p) for p in required if not p.exists())
        raise RuntimeError(f"Outputs do dashboard ausentes e não foi possível importar aimm_dashboard. Ausentes: {missing}. Erro: {exc}") from exc

    result = execute_aimm_dashboard()
    if result.get("errors"):
        raise RuntimeError(f"Falha ao executar dashboard como pré-etapa de comunicação: {result['errors']}")


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def build_html(summary, cards, dimensions, messages, next_actions, rules) -> str:
    s = summary[0]
    project = (rules.get("projeto") or {}).get("nome", "Fito+ Amazônia")

    cards_html = "\n".join(
        f"""
        <section class="card {esc(c.get('tipo',''))}">
          <h3>{esc(c.get('titulo',''))}</h3>
          <p class="value">{esc(c.get('valor',''))}</p>
          <p>{esc(c.get('interpretacao',''))}</p>
          <small>{esc(c.get('trava',''))}</small>
        </section>
        """
        for c in cards
    )
    dim_rows = "\n".join(
        f"<tr><td>{esc(d.get('eixo',''))}</td><td>{esc(d.get('rating',''))}</td><td>{esc(d.get('risco',''))}</td><td>{esc(d.get('pontos_ajustados',''))}</td></tr>"
        for d in dimensions
    )
    message_blocks = "\n".join(
        f"""
        <article class="message">
          <h3>{esc(m.get('tema',''))}</h3>
          <p><strong>Mensagem:</strong> {esc(m.get('mensagem_principal',''))}</p>
          <p><strong>Limitação:</strong> {esc(m.get('limitacao',''))}</p>
          <p><strong>Próxima ação:</strong> {esc(m.get('proxima_acao',''))}</p>
        </article>
        """
        for m in messages
    )
    action_items = "\n".join(
        f"<li><strong>{esc(a.get('prioridade',''))}</strong> — {esc(a.get('acao',''))}: {esc(a.get('justificativa',''))}</li>"
        for a in next_actions
    )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>{esc(project)} — Dashboard AIMM preliminar</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 32px; color: #111827; background: #ffffff; }}
  h1 {{ font-size: 28px; margin-bottom: 4px; }}
  h2 {{ margin-top: 32px; border-bottom: 2px solid #111827; padding-bottom: 6px; }}
  .warning {{ border: 2px solid #92400e; background: #fffbeb; padding: 14px; margin: 18px 0; font-weight: 700; }}
  .grid {{ display: grid; grid-template-columns: repeat(3, minmax(180px, 1fr)); gap: 14px; }}
  .card {{ border: 1px solid #374151; padding: 14px; border-radius: 10px; background: #f9fafb; }}
  .card .value {{ font-size: 26px; font-weight: 700; margin: 6px 0; }}
  .score {{ border-left: 8px solid #1f2937; }}
  .risco {{ border-left: 8px solid #991b1b; }}
  .monitoramento {{ border-left: 8px solid #1d4ed8; }}
  .bloqueio {{ border-left: 8px solid #92400e; }}
  .processo {{ border-left: 8px solid #166534; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
  th, td {{ border: 1px solid #9ca3af; padding: 8px; text-align: left; }}
  th {{ background: #e5e7eb; }}
  .message {{ border: 1px solid #d1d5db; padding: 12px; margin: 10px 0; border-radius: 8px; }}
  code {{ background: #f3f4f6; padding: 2px 4px; }}
</style>
</head>
<body>
<h1>{esc(project)} — Painel AIMM preliminar</h1>
<p>Base: Rodada 4.17, a partir do motor estrutural da Rodada 4.16.</p>

<div class="warning">
  TRAVA: o score exibido é estrutural, preliminar e não pode ser usado como score AIMM final validado.
  Não aprova orçamento, OSCs, espécies, produtos ou rotas regulatórias.
</div>

<h2>Resumo executivo</h2>
<p><strong>Score estrutural preliminar:</strong> {esc(s.get('score_estrutural_preliminar',''))}</p>
<p><strong>Status de prontidão:</strong> {esc(s.get('status_prontidao',''))}</p>
<p><strong>Interpretação:</strong> {esc(s.get('interpretacao_executiva',''))}</p>

<h2>Cards principais</h2>
<div class="grid">
{cards_html}
</div>

<h2>Dimensões AIMM</h2>
<table>
<thead><tr><th>Dimensão</th><th>Papel</th><th>Score preliminar</th><th>Status</th></tr></thead>
<tbody>
{dim_rows}
</tbody>
</table>

<h2>Matriz de mensagens</h2>
{message_blocks}

<h2>Próximas ações</h2>
<ol>
{action_items}
</ol>

<h2>Nota de leitura</h2>
<p>Score baixo nesta etapa indica baixa maturidade de evidências, presença de proxies e bloqueios operacionais.
Não deve ser usado como julgamento substantivo definitivo do mérito do projeto.</p>
</body>
</html>"""


def build_svg(summary, cards, dimensions, messages):
    s = summary[0]
    # SVG simples, editável e sem dependências externas.
    width = 1200
    height = 900
    y = 40

    def text(x, y, content, size=22, weight="normal"):
        return f'<text x="{x}" y="{y}" font-family="Arial" font-size="{size}" font-weight="{weight}" fill="#111827">{esc(content)}</text>'

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect x="0" y="0" width="1200" height="900" fill="#ffffff"/>',
        text(40, y, "Fito+ Amazônia — Dashboard AIMM preliminar", 30, "bold"),
    ]
    y += 40
    parts.append('<rect x="40" y="70" width="1120" height="62" fill="#fffbeb" stroke="#92400e" stroke-width="2"/>')
    parts.append(text(60, 105, "TRAVA: score estrutural preliminar. Não é AIMM final; não aprova decisões executivas.", 20, "bold"))

    y = 170
    parts.append(text(40, y, f"Score estrutural preliminar: {s.get('score_estrutural_preliminar','')}", 26, "bold"))
    parts.append(text(500, y, f"Status: {s.get('status_prontidao','')}", 24, "bold"))
    y += 50

    # Cards
    x_positions = [40, 420, 800]
    card_w = 340
    card_h = 110
    for idx, c in enumerate(cards[:6]):
        x = x_positions[idx % 3]
        row = idx // 3
        cy = y + row * 140
        parts.append(f'<rect x="{x}" y="{cy}" width="{card_w}" height="{card_h}" rx="12" fill="#f9fafb" stroke="#374151" stroke-width="1.5"/>')
        parts.append(text(x + 18, cy + 32, c.get("titulo", ""), 18, "bold"))
        parts.append(text(x + 18, cy + 68, c.get("valor", ""), 28, "bold"))
        parts.append(text(x + 18, cy + 95, "preliminar — não usar como decisão final", 13, "normal"))

    y += 310
    parts.append(text(40, y, "Dimensões AIMM", 24, "bold"))
    y += 35

    for idx, d in enumerate(dimensions):
        cy = y + idx * 42
        parts.append(f'<rect x="40" y="{cy-25}" width="1120" height="34" fill="#f3f4f6" stroke="#d1d5db"/>')
        parts.append(text(60, cy, d.get("eixo", ""), 18, "bold"))
        parts.append(text(250, cy, f"papel: {d.get('papel','')}", 16))
        parts.append(text(500, cy, f"pontos: {d.get('pontos_ajustados','')}", 16))
        parts.append(text(720, cy, f"{d.get('rating','')} / {d.get('risco','')}", 16))

    y += 250
    parts.append(text(40, y, "Mensagem de leitura", 24, "bold"))
    y += 35
    parts.append(text(60, y, "O score baixo nesta fase sinaliza maturidade insuficiente de dados/proxies e bloqueios ativos.", 18))
    y += 28
    parts.append(text(60, y, "A próxima etapa deve priorizar validação documental, normativa, orçamentária e de mercado.", 18))
    parts.append("</svg>")
    return "\n".join(parts)


def build_mermaid():
    return """flowchart TD
    A["Rodada 4.16: motor AIMM estrutural"] --> B["Rodada 4.17: painel e outputs"]
    B --> C["Rodada 4.18: pacote editável de comunicação"]
    C --> D["HTML executivo"]
    C --> E["SVG editável"]
    C --> F["Mermaid editável"]
    C --> G["Briefing Markdown"]
    C --> H["Payload JSON"]
    A --> I["Bloqueios e lacunas"]
    I --> J["Pré-diligência OSC"]
    I --> K["Normativa ANVISA/MAPA"]
    I --> L["Mercado/NCM/ComexStat"]
    I --> M["Orçamento com pesquisa de preços"]
    D --> N["Uso: alinhamento executivo"]
    E --> N
    F --> N
    G --> N
    H --> O["Uso futuro: dashboard web"]
    N --> P["Trava: não é score AIMM final"]
"""


def build_brief(summary, cards, dimensions, messages, next_actions):
    s = summary[0]
    lines = [
        "# Fito+ Amazônia — Briefing de Comunicação AIMM",
        "",
        "## 1. Mensagem central",
        "",
        f"O sistema já executa um motor estrutural preliminar e produz um score inicial de **{s.get('score_estrutural_preliminar')}**.",
        "",
        "Esse valor **não é score AIMM final**. Ele mede a maturidade atual da arquitetura, das evidências, dos proxies e dos bloqueios.",
        "",
        "## 2. Leitura correta",
        "",
        "- Score baixo nesta etapa não significa fracasso do projeto.",
        "- Score baixo indica que o sistema ainda depende de validações substantivas.",
        "- O uso correto é priorizar próximas rodadas e lacunas críticas.",
        "",
        "## 3. Cards principais",
        "",
    ]
    for c in cards:
        lines.append(f"- **{c.get('titulo')}**: {c.get('valor')} — {c.get('interpretacao')}")
    lines.extend(["", "## 4. Dimensões AIMM", ""])
    for d in dimensions:
        lines.append(f"- **{d.get('eixo')}**: {d.get('rating')} / {d.get('risco')} — {d.get('pontos_ajustados')} pontos")
    lines.extend(["", "## 5. Mensagens por tema", ""])
    for m in messages:
        lines.append(f"### {m.get('tema')}")
        lines.append(f"- Mensagem: {m.get('mensagem_principal')}")
        lines.append(f"- Limitação: {m.get('limitacao')}")
        lines.append(f"- Próxima ação: {m.get('proxima_acao')}")
        lines.append("")
    lines.extend(["## 6. Próximas ações priorizadas", ""])
    for a in next_actions:
        lines.append(f"- **{a.get('prioridade')}** — {a.get('acao')}: {a.get('justificativa')}")
    lines.extend([
        "",
        "## 7. Trava",
        "",
        "Este pacote é comunicacional, preliminar e editável. Não aprova OSCs, espécies, produtos, orçamento, rotas regulatórias ou score AIMM final.",
    ])
    return "\n".join(lines)


def build_manifest(paths: dict[str, Path]):
    rows = []
    for key, path in paths.items():
        rows.append({
            "id_arquivo": key,
            "arquivo": str(path),
            "existe": "sim" if path.exists() else "não",
            "formato": path.suffix.replace(".", "").upper() or "NA",
            "editavel": "sim",
            "uso": "pacote comunicação dashboard AIMM",
            "status": "ativo",
        })
    return rows


def execute_aimm_communication() -> dict[str, Any]:
    rules = load_yaml(RULES)
    ensure_dashboard_outputs()

    messages = read_csv(MESSAGES_SEED)
    layout = read_csv(LAYOUT_SEED)
    summary = read_csv(DASH_SUMMARY)
    cards = read_csv(DASH_CARDS)
    dimensions = read_csv(DASH_AXES)
    next_actions = read_csv(DASH_NEXT_ACTIONS)

    if not summary:
        return {"errors": ["aimm_executive_summary.csv vazio"]}

    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_SVG.parent.mkdir(parents=True, exist_ok=True)
    OUT_BRIEF.parent.mkdir(parents=True, exist_ok=True)

    html_text = build_html(summary, cards, dimensions, messages, next_actions, rules)
    svg_text = build_svg(summary, cards, dimensions, messages)
    mermaid_text = build_mermaid()
    brief_text = build_brief(summary, cards, dimensions, messages, next_actions)

    OUT_HTML.write_text(html_text, encoding="utf-8")
    OUT_SVG.write_text(svg_text, encoding="utf-8")
    OUT_MERMAID.write_text(mermaid_text, encoding="utf-8")
    OUT_BRIEF.write_text(brief_text, encoding="utf-8")

    payload = {
        "summary": summary[0],
        "cards": cards,
        "dimensions": dimensions,
        "messages": messages,
        "next_actions": next_actions,
        "layout": layout,
        "trava": "Pacote editável preliminar; não é score AIMM final.",
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    write_csv(OUT_MESSAGES, messages)
    write_csv(OUT_VISUAL_INDEX, layout)

    outputs = {
        "communication_messages": OUT_MESSAGES,
        "visual_outputs_index": OUT_VISUAL_INDEX,
        "html_dashboard": OUT_HTML,
        "svg_dashboard": OUT_SVG,
        "mermaid_flow": OUT_MERMAID,
        "communication_brief": OUT_BRIEF,
        "communication_payload": OUT_JSON,
        "evidence": OUT_EVIDENCE,
        "package_manifest": OUT_PACKAGE_MANIFEST,
    }

    evidence = [{
        "id_evidencia": "EVD_AIMM_COMMUNICATION_4_18",
        "id_fonte": "AIMM_COMMUNICATION_PACKAGE",
        "id_indicador": "MONITORAMENTO; COMUNICAÇÃO; GOVERNANÇA",
        "tipo_evidencia": "pacote_comunicacao_visualizacao",
        "pergunta_ou_lacuna": "O sistema gerou pacote editável de comunicação e visualização do dashboard AIMM?",
        "url_ou_arquivo": "outputs/visuals/aimm_dashboard_executivo.html; outputs/visuals/aimm_dashboard_cards.svg; outputs/visuals/aimm_dashboard_flow.mmd; outputs/reports/aimm_communication_brief.md",
        "titulo_documento": "Pacote editável de comunicação e visualização — Rodada 4.18",
        "pagina_tabela_secao": "HTML; SVG; Mermaid; Markdown; CSV; JSON",
        "trecho_original_ou_descricao": f"Mensagens: {len(messages)}; cards: {len(cards)}; dimensões: {len(dimensions)}; próximas ações: {len(next_actions)}; score exibido: {summary[0].get('score_estrutural_preliminar')}.",
        "resumo_ptbr": "Evidência de geração de pacote editável de comunicação; não representa score final.",
        "valor_extraido": summary[0].get("score_estrutural_preliminar", ""),
        "unidade": "score 0-100",
        "periodo_referencia": "Rodada 4.18",
        "territorio": "Fito+ Amazônia",
        "metodo_extracao": "consolidação automatizada dos outputs da Rodada 4.17 em formatos editáveis",
        "nivel_confianca": "médio_para_comunicação; baixo_para_decisão_final",
        "data_coleta": "",
        "conferido_por": "workflow GitHub Actions",
        "status_conferencia": "pendente_validação_visual_humana",
        "limitacoes": "Comunicação preliminar; mantém bloqueios e não substitui validação técnica.",
        "uso_na_calculadora": "Camada de comunicação, visualização e auditoria executiva.",
        "status_evidencia": "pendente",
    }]
    write_csv(OUT_EVIDENCE, evidence)

    manifest = build_manifest(outputs)
    write_csv(OUT_PACKAGE_MANIFEST, manifest)

    return {
        "errors": [],
        "score": summary[0].get("score_estrutural_preliminar", ""),
        "messages": len(messages),
        "cards": len(cards),
        "dimensions": len(dimensions),
        "next_actions": len(next_actions),
        "outputs": {k: str(v) for k, v in outputs.items()},
    }
