from pathlib import Path

import csv
import responses

from fito_aimm.coletor_mapaosc import coletar_mapaosc_municipios
from fito_aimm.coletor_ibge_geociencias import (
    AREA_XLS_CACHE_METADATA,
    AREA_XLS_RAW,
    AREA_XLS_URL,
    obter_xls_area_cacheado,
)
from fito_aimm.mapaosc.fetcher import MAPAOSC_DICIONARIO_URL
from fito_aimm.mapaosc import fetcher as mapaosc_fetcher


def _read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=";"))


@responses.activate
def test_mapaosc_pipeline_uses_local_base_and_mocked_dictionary(tmp_path: Path, fixtures_dir: Path, monkeypatch):
    raw_output = tmp_path / "raw.csv"
    processed_output = tmp_path / "processed.csv"
    summary_output = tmp_path / "summary.csv"
    log_output = tmp_path / "fetch_log.csv"
    dictionary_output = tmp_path / "dictionary.xlsx"
    local_base = tmp_path / "mapaosc_base.csv"
    evidence_output = Path("data/evidence/evidence_mapaosc_triagem.csv")
    original_evidence = evidence_output.read_bytes() if evidence_output.exists() else None

    local_base.write_text((fixtures_dir / "sample_mapaosc.csv").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(mapaosc_fetcher, "LOCAL_BASE_CANDIDATES", [local_base])

    responses.add(
        responses.GET,
        MAPAOSC_DICIONARIO_URL,
        body=b"fake-dictionary",
        status=200,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    try:
        result = coletar_mapaosc_municipios(
            arquivo_saida_raw=raw_output,
            arquivo_saida_processado=processed_output,
            arquivo_resumo=summary_output,
            arquivo_log=log_output,
            arquivo_dicionario=dictionary_output,
            max_linhas_saida=10,
        )
    finally:
        if original_evidence is None:
            evidence_output.unlink(missing_ok=True)
        else:
            evidence_output.write_bytes(original_evidence)

    processed = _read_csv(processed_output)
    summary = _read_csv(summary_output)

    assert result["chunksize"] == 50000
    assert len(processed) == 2
    assert {row["municipio"] for row in processed} == {"Manaus", "Santarém"}
    assert len(summary) == 4
    assert dictionary_output.exists()


@responses.activate
def test_ibge_xls_cache_respects_publication_date(tmp_path: Path):
    raw_path = tmp_path / AREA_XLS_RAW.name
    metadata_path = tmp_path / AREA_XLS_CACHE_METADATA.name
    raw_path.write_bytes(b"x" * 2048)
    metadata_path.write_text(
        '{"data_publicacao": "2025-06-29", "arquivo": "cache.xls"}',
        encoding="utf-8",
    )

    responses.add(
        responses.HEAD,
        AREA_XLS_URL,
        headers={"Last-Modified": "Sun, 29 Jun 2025 12:00:00 GMT"},
        status=200,
    )

    status, publication_date = obter_xls_area_cacheado(destino=raw_path, metadata_path=metadata_path)

    assert status == "cache_validado"
    assert publication_date == "2025-06-29"
