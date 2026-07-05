from __future__ import annotations

from math import cos, pi, sin
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from fito_aimm.models import ComparisonRow, ProjectRecord, ProjectVersion
from fito_aimm.utils import qualitative_label, slugify


class ExecutivePdfExporter:
    def __init__(self, output_dir: Path = Path("outputs/reports")):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(self, project: ProjectRecord, version: ProjectVersion) -> Path:
        filename = f"fito_aimm_{slugify(project.nome_projeto)}_{project.data_referencia.isoformat()}_v{version.numero_versao}.pdf"
        path = self.output_dir / filename
        pdf = canvas.Canvas(str(path), pagesize=A4)
        width, height = A4

        self._draw_cover(pdf, width, height, project, version)
        self._footer(pdf, width, project, version)
        pdf.showPage()

        self._draw_score_summary(pdf, width, height, project, version)
        self._footer(pdf, width, project, version)
        pdf.showPage()

        self._draw_blockers_and_comparison(pdf, width, height, version)
        self._footer(pdf, width, project, version)
        pdf.showPage()

        self._draw_evidences(pdf, width, height, version)
        self._footer(pdf, width, project, version)
        pdf.save()
        return path

    def _watermark(self, pdf: canvas.Canvas, width: float, height: float, approved: bool) -> None:
        if approved:
            return
        pdf.saveState()
        pdf.setFillColor(colors.Color(0.85, 0.2, 0.2, alpha=0.2))
        pdf.setFont("Helvetica-Bold", 46)
        pdf.translate(width / 2, height / 2)
        pdf.rotate(35)
        pdf.drawCentredString(0, 0, "PRELIMINAR")
        pdf.restoreState()

    def _draw_cover(self, pdf: canvas.Canvas, width: float, height: float, project: ProjectRecord, version: ProjectVersion) -> None:
        approved = version.aprovacao is not None and version.aprovacao.decisao != "Reprovado"
        self._watermark(pdf, width, height, approved)
        pdf.setFillColor(colors.HexColor("#0F172A"))
        pdf.rect(0, height - 55 * mm, width, 55 * mm, fill=1, stroke=0)
        pdf.setFillColor(colors.white)
        pdf.setFont("Helvetica-Bold", 22)
        pdf.drawString(20 * mm, height - 22 * mm, "Fito+ Amazônia AIMM")
        pdf.setFont("Helvetica", 14)
        pdf.drawString(20 * mm, height - 32 * mm, "Relatório executivo de projeto")
        pdf.setFillColor(colors.HexColor("#111827"))
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawString(20 * mm, height - 80 * mm, project.nome_projeto)
        pdf.setFont("Helvetica", 12)
        lines = [
            f"Territórios: {', '.join(project.territorios)}",
            f"Responsável técnico: {project.tecnico_responsavel_nome}",
            f"Data de referência: {project.data_referencia.isoformat()}",
            f"Versão analisada: {version.numero_versao}",
            f"Pontuação geral: {version.pontuacao_geral:.2f} ({version.rotulo_geral})",
            f"Status: {version.status}",
        ]
        ypos = height - 95 * mm
        for line in lines:
            pdf.drawString(20 * mm, ypos, line)
            ypos -= 8 * mm

    def _draw_score_summary(self, pdf: canvas.Canvas, width: float, height: float, project: ProjectRecord, version: ProjectVersion) -> None:
        approved = version.aprovacao is not None and version.aprovacao.decisao != "Reprovado"
        self._watermark(pdf, width, height, approved)
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(20 * mm, height - 20 * mm, "Resumo de pontuação")
        pdf.setFont("Helvetica-Bold", 34)
        pdf.setFillColor(colors.HexColor("#166534") if version.elegivel_analise_formal else colors.HexColor("#92400E"))
        pdf.drawString(20 * mm, height - 38 * mm, f"{version.pontuacao_geral:.2f}")
        pdf.setFillColor(colors.black)
        pdf.setFont("Helvetica", 12)
        pdf.drawString(48 * mm, height - 36 * mm, f"{version.rotulo_geral} — {qualitative_label(version.pontuacao_geral)}")
        self._draw_dimension_table(pdf, version)
        self._draw_radar_chart(pdf, width - 78 * mm, height - 82 * mm, 28 * mm, version)

    def _draw_dimension_table(self, pdf: canvas.Canvas, version: ProjectVersion) -> None:
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(20 * mm, 215 * mm, "Dimensão")
        pdf.drawString(80 * mm, 215 * mm, "Pontuação")
        pdf.drawString(110 * mm, 215 * mm, "Leitura")
        pdf.line(20 * mm, 213 * mm, 175 * mm, 213 * mm)
        y = 206 * mm
        pdf.setFont("Helvetica", 10)
        for dimension in version.dimensoes:
            pdf.drawString(20 * mm, y, dimension.nome)
            pdf.drawRightString(104 * mm, y, f"{dimension.pontuacao:.2f}")
            pdf.drawString(110 * mm, y, dimension.rotulo_qualitativo)
            y -= 8 * mm

    def _draw_radar_chart(self, pdf: canvas.Canvas, center_x: float, center_y: float, radius: float, version: ProjectVersion) -> None:
        dimensions = version.dimensoes[:5]
        if not dimensions:
            return
        pdf.setStrokeColor(colors.HexColor("#CBD5E1"))
        for factor in (0.25, 0.5, 0.75, 1.0):
            points = self._radar_points(center_x, center_y, radius * factor, [100.0] * len(dimensions))
            self._polygon(pdf, points, stroke=1, fill=0)
        points = self._radar_points(center_x, center_y, radius, [item.pontuacao for item in dimensions])
        pdf.setFillColor(colors.Color(0.2, 0.4, 0.8, alpha=0.25))
        pdf.setStrokeColor(colors.HexColor("#1D4ED8"))
        self._polygon(pdf, points, stroke=1, fill=1)
        pdf.setFillColor(colors.black)
        pdf.setFont("Helvetica", 8)
        label_points = self._radar_points(center_x, center_y, radius + 12 * mm, [100.0] * len(dimensions))
        for point, dimension in zip(label_points, dimensions):
            pdf.drawCentredString(point[0], point[1], dimension.nome[:18])

    def _radar_points(self, center_x: float, center_y: float, radius: float, scores: list[float]) -> list[tuple[float, float]]:
        total = len(scores)
        points = []
        for index, score in enumerate(scores):
            angle = -pi / 2 + (2 * pi * index / total)
            scaled = radius * (score / 100)
            points.append((center_x + cos(angle) * scaled, center_y + sin(angle) * scaled))
        return points

    def _polygon(self, pdf: canvas.Canvas, points: list[tuple[float, float]], stroke: int, fill: int) -> None:
        path = pdf.beginPath()
        start = points[0]
        path.moveTo(*start)
        for point in points[1:]:
            path.lineTo(*point)
        path.close()
        pdf.drawPath(path, stroke=stroke, fill=fill)

    def _draw_blockers_and_comparison(self, pdf: canvas.Canvas, width: float, height: float, version: ProjectVersion) -> None:
        approved = version.aprovacao is not None and version.aprovacao.decisao != "Reprovado"
        self._watermark(pdf, width, height, approved)
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(20 * mm, height - 18 * mm, "Impedimentos, lacunas e comparativos")
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(20 * mm, height - 32 * mm, "Impedimentos ativos")
        pdf.setFont("Helvetica", 10)
        y = height - 40 * mm
        for blocker in version.bloqueios[:6]:
            pdf.drawString(22 * mm, y, f"• {blocker.descricao} ({blocker.criticidade})")
            y -= 7 * mm
        y -= 4 * mm
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(20 * mm, y, "Lacunas prioritárias")
        pdf.setFont("Helvetica", 10)
        y -= 8 * mm
        for gap in version.lacunas[:5]:
            pdf.drawString(22 * mm, y, f"• {gap.descricao} — Estimativa usada: {gap.proxy_utilizada}")
            y -= 7 * mm
        y -= 4 * mm
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(20 * mm, y, "Comparativo")
        y -= 8 * mm
        pdf.setFont("Helvetica", 9)
        for row in version.comparativos[:6]:
            marker = "▲" if row.delta > 0 else "▼" if row.delta < 0 else "•"
            pdf.drawString(
                22 * mm,
                y,
                f"{marker} {row.dimensao}: projeto {row.pontuacao_projeto:.1f} vs {row.referencia_nome} {row.pontuacao_referencia:.1f} ({row.delta:+.1f})",
            )
            y -= 6.5 * mm

    def _draw_evidences(self, pdf: canvas.Canvas, width: float, height: float, version: ProjectVersion) -> None:
        approved = version.aprovacao is not None and version.aprovacao.decisao != "Reprovado"
        self._watermark(pdf, width, height, approved)
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(20 * mm, height - 18 * mm, "Evidências principais")
        pdf.setFont("Helvetica", 9)
        y = height - 30 * mm
        for evidence in version.evidencias[:10]:
            pdf.setFont("Helvetica-Bold", 9)
            pdf.drawString(20 * mm, y, evidence.titulo[:80])
            y -= 5 * mm
            pdf.setFont("Helvetica", 8)
            pdf.drawString(22 * mm, y, f"Fonte: {evidence.fonte} | Valor: {evidence.valor} | Confiança: {evidence.nivel_confianca}")
            y -= 4.5 * mm
            pdf.drawString(22 * mm, y, evidence.resumo[:110])
            y -= 7 * mm
            if y < 35 * mm:
                break

    def _footer(self, pdf: canvas.Canvas, width: float, project: ProjectRecord, version: ProjectVersion) -> None:
        pdf.setStrokeColor(colors.HexColor("#CBD5E1"))
        pdf.line(15 * mm, 15 * mm, width - 15 * mm, 15 * mm)
        pdf.setFont("Helvetica", 8)
        footer = "Documento gerado por Fito+ Amazônia AIMM — uso interno"
        pdf.drawString(18 * mm, 10 * mm, footer)
        pdf.drawRightString(width - 18 * mm, 10 * mm, f"Hash: {version.hash_documento[:16]}…")
