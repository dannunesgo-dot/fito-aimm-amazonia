"""
Coleta de métricas reais por etapa do pipeline:
tempo decorrido, linhas lidas, linhas filtradas e throughput.
"""
from __future__ import annotations

import csv
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator


@dataclass
class MetricaEtapa:
    """Métricas de desempenho de uma etapa do pipeline."""

    etapa: str
    linhas_entrada: int = 0
    linhas_saida: int = 0
    linhas_filtradas: int = 0
    tempo_s: float = 0.0
    throughput_por_s: float = 0.0
    timestamp_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).replace(microsecond=0).isoformat())
    status: str = "ok"
    observacao: str = ""

    def finalizar(
        self,
        linhas_saida: int,
        *,
        status: str = "ok",
        observacao: str = "",
    ) -> None:
        """Registra linhas de saída, calcula filtradas e throughput."""
        self.linhas_saida = linhas_saida
        self.linhas_filtradas = max(0, self.linhas_entrada - linhas_saida)
        self.status = status
        self.observacao = observacao
        self._calcular_throughput()

    def _calcular_throughput(self) -> None:
        if self.tempo_s > 0 and self.linhas_entrada > 0:
            self.throughput_por_s = round(self.linhas_entrada / self.tempo_s, 2)
        else:
            self.throughput_por_s = 0.0


class ColetorMetricas:
    """Coleta e registra métricas de desempenho por etapa do pipeline."""

    def __init__(self, pipeline_id: str = "") -> None:
        self.pipeline_id = pipeline_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self._metricas: list[MetricaEtapa] = []

    @contextmanager
    def etapa(self, nome: str, linhas_entrada: int = 0) -> Generator[MetricaEtapa, None, None]:
        """Context manager que mede o tempo de uma etapa e coleta métricas.

        Exemplo::

            coletor = ColetorMetricas("pipeline_ibge")
            with coletor.etapa("coleta_populacao", linhas_entrada=4) as m:
                resultado = coletar_populacao_estimada_municipios()
                m.finalizar(len(resultado))
        """
        metrica = MetricaEtapa(etapa=nome, linhas_entrada=linhas_entrada)
        inicio = time.perf_counter()
        try:
            yield metrica
        except Exception as exc:
            metrica.tempo_s = round(time.perf_counter() - inicio, 4)
            metrica.status = "erro"
            metrica.observacao = str(exc)
            self._metricas.append(metrica)
            raise
        else:
            metrica.tempo_s = round(time.perf_counter() - inicio, 4)
            if metrica.throughput_por_s == 0.0:
                metrica._calcular_throughput()
        self._metricas.append(metrica)

    def registrar(self, metrica: MetricaEtapa) -> None:
        """Registra uma métrica construída externamente."""
        self._metricas.append(metrica)

    @property
    def metricas(self) -> list[MetricaEtapa]:
        """Lista de métricas coletadas (cópia)."""
        return list(self._metricas)

    def resumo(self) -> dict[str, Any]:
        """Retorna resumo agregado do pipeline."""
        total_tempo = sum(m.tempo_s for m in self._metricas)
        total_entrada = sum(m.linhas_entrada for m in self._metricas)
        total_saida = sum(m.linhas_saida for m in self._metricas)
        erros = [m.etapa for m in self._metricas if m.status == "erro"]
        throughput_medio = (
            round(total_entrada / total_tempo, 2) if total_tempo > 0 else 0.0
        )
        return {
            "pipeline_id": self.pipeline_id,
            "total_etapas": len(self._metricas),
            "tempo_total_s": round(total_tempo, 4),
            "total_linhas_entrada": total_entrada,
            "total_linhas_saida": total_saida,
            "total_linhas_filtradas": total_entrada - total_saida,
            "throughput_medio_por_s": throughput_medio,
            "etapas_com_erro": erros,
            "status_geral": "erro" if erros else "ok",
        }

    def salvar_csv(self, caminho: Path) -> None:
        """Salva métricas por etapa em arquivo CSV."""
        caminho = Path(caminho)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        if not self._metricas:
            return
        campos = list(asdict(self._metricas[0]).keys()) + ["pipeline_id"]
        with caminho.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=campos, delimiter=";")
            w.writeheader()
            for m in self._metricas:
                row = asdict(m)
                row["pipeline_id"] = self.pipeline_id
                w.writerow(row)

    def salvar_storage(self, storage: Any) -> int:
        """Salva métricas na tabela 'pipeline_metricas' do storage SQLite."""
        if not self._metricas:
            return 0
        registros = []
        for m in self._metricas:
            r = asdict(m)
            r["pipeline_id"] = self.pipeline_id
            registros.append({k: str(v) for k, v in r.items()})
        return storage.salvar_registros("pipeline_metricas", registros)

    def imprimir_resumo(self) -> None:
        """Imprime resumo formatado no stdout."""
        r = self.resumo()
        print(
            f"[Métricas] pipeline={r['pipeline_id']} "
            f"etapas={r['total_etapas']} "
            f"tempo={r['tempo_total_s']}s "
            f"entradas={r['total_linhas_entrada']} "
            f"saidas={r['total_linhas_saida']} "
            f"filtradas={r['total_linhas_filtradas']} "
            f"throughput={r['throughput_medio_por_s']}/s "
            f"status={r['status_geral']}"
        )
        for m in self._metricas:
            print(
                f"  etapa={m.etapa} "
                f"t={m.tempo_s}s "
                f"in={m.linhas_entrada} "
                f"out={m.linhas_saida} "
                f"filtradas={m.linhas_filtradas} "
                f"throughput={m.throughput_por_s}/s "
                f"status={m.status}"
                + (f" obs={m.observacao}" if m.observacao else "")
            )
