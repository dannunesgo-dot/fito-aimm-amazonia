"""
Processamento GIS real: carregamento de camadas GeoJSON/shapefile,
filtragem por município do projeto, cálculo de estatísticas de área
e exportação de atributos em CSV.

Suporte primário: GeoJSON (sem dependências externas).
Suporte estendido: shapefile/GeoPackage via geopandas (opcional).
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

try:
    import geopandas as gpd
    _GEOPANDAS_OK = True
except ImportError:  # pragma: no cover
    _GEOPANDAS_OK = False


MUNICIPIOS_PROJETO = {
    "1302603": {"municipio": "Manaus", "uf": "AM"},
    "1300607": {"municipio": "Benjamin Constant", "uf": "AM"},
    "1501402": {"municipio": "Belém", "uf": "PA"},
    "1506807": {"municipio": "Santarém", "uf": "PA"},
}

# Formatos suportados e suas extensões
FORMATOS_SUPORTADOS = {
    ".geojson": "geojson",
    ".json": "geojson",
    ".shp": "shapefile",
    ".gpkg": "geopackage",
}


# ---------------------------------------------------------------------------
# Leitura GeoJSON nativa (sem dependências externas)
# ---------------------------------------------------------------------------

def carregar_geojson(caminho: Path) -> dict[str, Any]:
    """Carrega um arquivo GeoJSON."""
    with caminho.open("r", encoding="utf-8") as f:
        dados = json.load(f)
    if dados.get("type") not in ("FeatureCollection", "Feature"):
        raise ValueError(f"GeoJSON inválido em {caminho}: tipo '{dados.get('type')}' não suportado.")
    return dados


def _features_de(geojson: dict[str, Any]) -> list[dict[str, Any]]:
    """Extrai lista de features independente do tipo GeoJSON."""
    if geojson["type"] == "FeatureCollection":
        return geojson.get("features", [])
    return [geojson]


def _bbox_feature(feature: dict[str, Any]) -> tuple[float, float, float, float] | None:
    """Calcula bounding box de uma feature GeoJSON (minx, miny, maxx, maxy)."""
    geom = feature.get("geometry")
    if not geom:
        return None
    coords = _extrair_coordenadas(geom)
    if not coords:
        return None
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    return (min(lons), min(lats), max(lons), max(lats))


def _extrair_coordenadas(geom: dict[str, Any]) -> list[list[float]]:
    """Extrai pares [lon, lat] de qualquer geometria GeoJSON."""
    tipo = geom.get("type", "")
    coords = geom.get("coordinates", [])
    resultado: list[list[float]] = []

    if tipo == "Point":
        resultado.append(coords[:2])
    elif tipo in ("MultiPoint", "LineString"):
        resultado.extend(c[:2] for c in coords)
    elif tipo in ("Polygon", "MultiLineString"):
        for anel in coords:
            resultado.extend(c[:2] for c in anel)
    elif tipo == "MultiPolygon":
        for poligono in coords:
            for anel in poligono:
                resultado.extend(c[:2] for c in anel)
    elif tipo == "GeometryCollection":
        for sub_geom in geom.get("geometries", []):
            resultado.extend(_extrair_coordenadas(sub_geom))
    return resultado


def _area_poligono_graus(coords: list[list[float]]) -> float:
    """Aproximação de área usando fórmula de Shoelace (em graus quadrados)."""
    n = len(coords)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += coords[i][0] * coords[j][1]
        area -= coords[j][0] * coords[i][1]
    return abs(area) / 2.0


def _area_km2_aproximada(geom: dict[str, Any]) -> float:
    """Estimativa de área em km² a partir de geometria GeoJSON.

    Usa a fórmula de Shoelace com conversão aproximada de graus para km.
    Precisão suficiente para triagem; para análise rigorosa use geopandas/pyproj.
    """
    tipo = geom.get("type", "")
    coords = geom.get("coordinates", [])

    # Converte graus para km (~111 km/grau latitude; ~111*cos(lat) km/grau longitude)
    # Usamos o centroide para estimar fator de longitude
    todas = _extrair_coordenadas(geom)
    if not todas:
        return 0.0
    lat_media = sum(c[1] for c in todas) / len(todas)
    fator_lon = math.cos(math.radians(lat_media)) * 111.0
    fator_lat = 111.0

    def converter(c: list[float]) -> list[float]:
        return [c[0] * fator_lon, c[1] * fator_lat]

    area = 0.0
    if tipo == "Polygon":
        anel_externo = coords[0] if coords else []
        area = _area_poligono_graus([converter(c) for c in anel_externo])
        for anel_interno in coords[1:]:
            area -= _area_poligono_graus([converter(c) for c in anel_interno])
    elif tipo == "MultiPolygon":
        for poligono in coords:
            anel_externo = poligono[0] if poligono else []
            area += _area_poligono_graus([converter(c) for c in anel_externo])
            for anel_interno in poligono[1:]:
                area -= _area_poligono_graus([converter(c) for c in anel_interno])
    return max(0.0, area)


# ---------------------------------------------------------------------------
# Filtragem por municípios do projeto
# ---------------------------------------------------------------------------

_BBOX_MUNICIPIOS: dict[str, tuple[float, float, float, float]] = {
    # (minlon, minlat, maxlon, maxlat) — bounding boxes aproximadas
    "1302603": (-60.3, -3.3, -59.7, -2.8),   # Manaus
    "1300607": (-73.1, -4.5, -70.0, -4.0),   # Benjamin Constant
    "1501402": (-48.7, -1.6, -48.3, -1.2),   # Belém
    "1506807": (-55.0, -3.0, -54.5, -2.3),   # Santarém
}


def _bbox_intercepta(
    bbox1: tuple[float, float, float, float],
    bbox2: tuple[float, float, float, float],
) -> bool:
    """Verifica se dois bounding boxes se interceptam."""
    return not (
        bbox1[2] < bbox2[0]
        or bbox1[0] > bbox2[2]
        or bbox1[3] < bbox2[1]
        or bbox1[1] > bbox2[3]
    )


def filtrar_features_por_municipios(
    features: list[dict[str, Any]],
    codigos_municipios: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Filtra features GeoJSON que intersectam os municípios do projeto.

    Usa bounding box para filtragem rápida. Para precisão total (interseção exata),
    use a versão geopandas abaixo.

    Args:
        features: Lista de features GeoJSON.
        codigos_municipios: Codes IBGE a filtrar; usa todos do projeto se None.

    Returns:
        Lista de features que intersectam pelo menos um município alvo.
    """
    codigos = set(codigos_municipios or MUNICIPIOS_PROJETO.keys())
    bboxes_alvo = [_BBOX_MUNICIPIOS[c] for c in codigos if c in _BBOX_MUNICIPIOS]

    if not bboxes_alvo:
        return features

    resultado = []
    for feature in features:
        bbox = _bbox_feature(feature)
        if bbox is None:
            continue
        if any(_bbox_intercepta(bbox, alvo) for alvo in bboxes_alvo):
            resultado.append(feature)
    return resultado


# ---------------------------------------------------------------------------
# Cálculo de estatísticas por camada
# ---------------------------------------------------------------------------

def calcular_estatisticas_camada(
    features: list[dict[str, Any]],
    nome_camada: str,
    campo_area_atributo: str | None = None,
) -> dict[str, Any]:
    """Calcula estatísticas de área e contagem para uma camada GeoJSON.

    Args:
        features: Lista de features GeoJSON.
        nome_camada: Nome descritivo da camada.
        campo_area_atributo: Campo de atributo com área pré-calculada (opcional).

    Returns:
        Dicionário com total_features, area_total_km2, area_media_km2, etc.
    """
    total = len(features)
    areas: list[float] = []

    for feature in features:
        geom = feature.get("geometry")
        if not geom:
            continue
        props = feature.get("properties") or {}

        if campo_area_atributo and campo_area_atributo in props:
            try:
                areas.append(float(props[campo_area_atributo]))
                continue
            except (TypeError, ValueError):
                pass

        tipo = geom.get("type", "")
        if tipo in ("Polygon", "MultiPolygon"):
            areas.append(_area_km2_aproximada(geom))

    area_total = sum(areas)
    area_media = (area_total / len(areas)) if areas else 0.0

    return {
        "camada": nome_camada,
        "total_features": total,
        "features_com_area": len(areas),
        "area_total_km2": round(area_total, 4),
        "area_media_km2": round(area_media, 4),
        "area_min_km2": round(min(areas), 4) if areas else 0.0,
        "area_max_km2": round(max(areas), 4) if areas else 0.0,
    }


# ---------------------------------------------------------------------------
# Extração de atributos para CSV
# ---------------------------------------------------------------------------

def extrair_atributos_csv(
    features: list[dict[str, Any]],
    arquivo_saida: Path,
    campos_extras: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Extrai atributos de features GeoJSON para arquivo CSV.

    Cada feature gera uma linha; colunas derivadas incluem:
    - Todos os atributos de ``properties``
    - ``geometry_type``, ``area_km2_aprox``, ``centroide_lon``, ``centroide_lat``

    Args:
        features: Lista de features GeoJSON.
        arquivo_saida: Caminho para o CSV de saída.
        campos_extras: Campos adicionais a incluir além dos properties.

    Returns:
        Lista de dicionários com os atributos de cada feature.
    """
    linhas: list[dict[str, Any]] = []

    for i, feature in enumerate(features):
        geom = feature.get("geometry") or {}
        props = dict(feature.get("properties") or {})

        tipo_geom = geom.get("type", "")
        todas_coords = _extrair_coordenadas(geom)
        if todas_coords:
            centroide_lon = round(sum(c[0] for c in todas_coords) / len(todas_coords), 6)
            centroide_lat = round(sum(c[1] for c in todas_coords) / len(todas_coords), 6)
        else:
            centroide_lon = centroide_lat = None

        area = 0.0
        if tipo_geom in ("Polygon", "MultiPolygon"):
            area = _area_km2_aproximada(geom)

        linha: dict[str, Any] = {
            "feature_index": i,
            "geometry_type": tipo_geom,
            "centroide_lon": centroide_lon,
            "centroide_lat": centroide_lat,
            "area_km2_aprox": round(area, 4),
        }
        linha.update(props)

        if campos_extras:
            for campo in campos_extras:
                if campo not in linha:
                    linha[campo] = ""

        linhas.append(linha)

    if linhas:
        arquivo_saida = Path(arquivo_saida)
        arquivo_saida.parent.mkdir(parents=True, exist_ok=True)
        campos = list(linhas[0].keys())
        with arquivo_saida.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=campos, delimiter=";", extrasaction="ignore")
            w.writeheader()
            for l in linhas:
                w.writerow({k: str(v) if v is not None else "" for k, v in l.items()})

    return linhas


# ---------------------------------------------------------------------------
# Função principal de processamento de camada
# ---------------------------------------------------------------------------

def processar_camada_geojson(
    arquivo_entrada: Path,
    arquivo_atributos_csv: Path,
    nome_camada: str = "",
    filtrar_por_municipios: bool = True,
    codigos_municipios: list[str] | None = None,
) -> dict[str, Any]:
    """Processa uma camada GeoJSON: filtragem, estatísticas e exportação de atributos.

    Args:
        arquivo_entrada: Arquivo GeoJSON de entrada.
        arquivo_atributos_csv: CSV de saída com atributos de cada feature.
        nome_camada: Nome descritivo da camada (usa nome do arquivo se omitido).
        filtrar_por_municipios: Se True, filtra features pelos municípios do projeto.
        codigos_municipios: Códigos IBGE específicos para filtrar (todos se None).

    Returns:
        Dicionário com ``features_totais``, ``features_filtradas``, ``estatisticas``,
        ``atributos`` e ``arquivo_csv``.
    """
    arquivo_entrada = Path(arquivo_entrada)
    if not arquivo_entrada.exists():
        raise FileNotFoundError(f"Arquivo GeoJSON não encontrado: {arquivo_entrada}")

    sufixo = arquivo_entrada.suffix.lower()
    if sufixo not in FORMATOS_SUPORTADOS:
        raise ValueError(
            f"Formato '{sufixo}' não suportado. Suportados: {list(FORMATOS_SUPORTADOS.keys())}"
        )

    if sufixo in (".shp", ".gpkg") and _GEOPANDAS_OK:
        return _processar_com_geopandas(
            arquivo_entrada,
            arquivo_atributos_csv,
            nome_camada or arquivo_entrada.stem,
            filtrar_por_municipios,
            codigos_municipios,
        )

    # Processamento nativo GeoJSON
    geojson = carregar_geojson(arquivo_entrada)
    features = _features_de(geojson)
    total = len(features)

    if filtrar_por_municipios:
        features = filtrar_features_por_municipios(features, codigos_municipios)

    nome = nome_camada or arquivo_entrada.stem
    estatisticas = calcular_estatisticas_camada(features, nome)
    atributos = extrair_atributos_csv(features, arquivo_atributos_csv)

    return {
        "camada": nome,
        "arquivo_entrada": str(arquivo_entrada),
        "arquivo_csv": str(arquivo_atributos_csv),
        "features_totais": total,
        "features_filtradas": len(features),
        "estatisticas": estatisticas,
        "atributos": atributos,
    }


def _processar_com_geopandas(
    arquivo_entrada: Path,
    arquivo_atributos_csv: Path,
    nome_camada: str,
    filtrar_por_municipios: bool,
    codigos_municipios: list[str] | None,
) -> dict[str, Any]:
    """Versão geopandas para shapefiles/GeoPackage com projeção real."""
    gdf = gpd.read_file(arquivo_entrada)
    total = len(gdf)

    if filtrar_por_municipios:
        codigos = list(codigos_municipios or MUNICIPIOS_PROJETO.keys())
        # Constrói GeoDataFrame das bboxes dos municípios alvo
        from shapely.geometry import box as shapely_box
        import pandas as pd
        caixas = [shapely_box(*_BBOX_MUNICIPIOS[c]) for c in codigos if c in _BBOX_MUNICIPIOS]
        if caixas:
            from shapely.ops import unary_union
            regiao_alvo = unary_union(caixas)
            gdf_wgs = gdf.to_crs(epsg=4326) if gdf.crs and gdf.crs.to_epsg() != 4326 else gdf
            gdf = gdf[gdf_wgs.geometry.intersects(regiao_alvo)].copy()

    gdf_m = gdf.to_crs(epsg=5880)  # SIRGAS 2000 / Brazil Polyconic
    if "area_km2" not in gdf_m.columns:
        gdf_m["area_km2"] = gdf_m.geometry.area / 1e6

    arquivo_atributos_csv = Path(arquivo_atributos_csv)
    arquivo_atributos_csv.parent.mkdir(parents=True, exist_ok=True)
    df_attrs = gdf_m.drop(columns=["geometry"], errors="ignore")
    df_attrs.to_csv(arquivo_atributos_csv, sep=";", index=False, encoding="utf-8-sig")

    areas = gdf_m["area_km2"].dropna().tolist()
    estatisticas = {
        "camada": nome_camada,
        "total_features": total,
        "features_com_area": len(areas),
        "area_total_km2": round(sum(areas), 4),
        "area_media_km2": round(sum(areas) / len(areas), 4) if areas else 0.0,
        "area_min_km2": round(min(areas), 4) if areas else 0.0,
        "area_max_km2": round(max(areas), 4) if areas else 0.0,
    }

    return {
        "camada": nome_camada,
        "arquivo_entrada": str(arquivo_entrada),
        "arquivo_csv": str(arquivo_atributos_csv),
        "features_totais": total,
        "features_filtradas": len(gdf),
        "estatisticas": estatisticas,
        "atributos": df_attrs.to_dict(orient="records"),
    }
