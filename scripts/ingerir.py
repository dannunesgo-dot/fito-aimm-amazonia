#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         FITO+ AMAZÔNIA — Interface de Ingestão de Dados (AIMM)             ║
╚══════════════════════════════════════════════════════════════════════════════╝

Ferramenta para ingerir documentos, arquivos, URLs, DOIs e APIs no sistema AIMM.

FORMATOS SUPORTADOS
───────────────────
  Planilhas     : .xlsx  .xls  .ods
  Documentos    : .docx  .pdf
  Apresentações : .pptx
  Dados         : .json  .yaml  .yml  .csv  .tsv  .md  .txt
  GIS           : .geojson  .shp  .gpkg  .kml  .gml
  Remoto        : URL  DOI  API

EXEMPLOS RÁPIDOS
────────────────
  # Ingerir um arquivo local:
  python scripts/ingerir.py arquivo relatorio.pdf

  # Ingerir uma planilha e salvar resultado:
  python scripts/ingerir.py arquivo dados.xlsx --salvar outputs/ingestao/

  # Baixar e ingerir uma URL:
  python scripts/ingerir.py url https://exemplo.com/dados.json

  # Resolver metadados de um DOI:
  python scripts/ingerir.py doi 10.1016/j.forpol.2021.102447

  # Chamar um endpoint de API:
  python scripts/ingerir.py api https://servicodados.ibge.gov.br/api/v1/localidades/estados

  # Ingerir múltiplas fontes de um arquivo de lista:
  python scripts/ingerir.py lote fontes.txt --salvar outputs/ingestao/

  # Ver capacidades do sistema:
  python scripts/ingerir.py capacidades

  # Modo interativo (guiado):
  python scripts/ingerir.py interativo
"""
from __future__ import annotations

import argparse
import json
import sys
import textwrap
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers de exibição
# ---------------------------------------------------------------------------

_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║         FITO+ AMAZÔNIA — Interface de Ingestão de Dados (AIMM)             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

_SEP = "─" * 78


def _print_banner() -> None:
    print(_BANNER)


def _print_sep() -> None:
    print(_SEP)


def _print_ok(mensagem: str) -> None:
    print(f"  ✓  {mensagem}")


def _print_erro(mensagem: str) -> None:
    print(f"  ✗  ERRO: {mensagem}", file=sys.stderr)


def _print_aviso(mensagem: str) -> None:
    print(f"  ⚠  {mensagem}")


def _print_resultado(resultado: "ResultadoIngestao") -> None:  # type: ignore[name-defined]  # noqa: F821
    _print_sep()
    print(f"  Fonte    : {resultado.fonte}")
    print(f"  Tipo     : {resultado.tipo_fonte}")
    print(f"  Formato  : {resultado.formato}")
    print(f"  Título   : {resultado.titulo[:100] if resultado.titulo else '(sem título)'}")
    print(f"  Status   : {resultado.status.upper()}")

    if resultado.erro:
        _print_aviso(f"Aviso/Erro parcial: {resultado.erro}")

    # Métricas de conteúdo
    c = resultado.conteudo
    if "total_paginas" in c:
        print(f"  Páginas  : {c['total_paginas']}")
    if "total_slides" in c:
        print(f"  Slides   : {c['total_slides']}")
    if "total_linhas" in c:
        print(f"  Linhas   : {c['total_linhas']}")
    if "total_registros" in c:
        print(f"  Registros: {c['total_registros']}")
    if "total_features" in c:
        print(f"  Features : {c['total_features']}")
    if "abas" in c:
        nomes_abas = [a.get("nome", "?") for a in c["abas"]]
        print(f"  Abas     : {', '.join(nomes_abas)}")

    texto = c.get("texto", "")
    if texto:
        trecho = texto[:300].replace("\n", " ").strip()
        if len(texto) > 300:
            trecho += "…"
        print(f"\n  Trecho de texto:\n  {trecho}\n")

    # DOI — campos extras
    if resultado.tipo_fonte == "doi":
        if c.get("autores"):
            print(f"  Autores  : {'; '.join(c['autores'][:3])}")
        if c.get("ano_publicacao"):
            print(f"  Ano      : {c['ano_publicacao']}")
        if c.get("publicador"):
            print(f"  Publicador: {c['publicador']}")

    _print_sep()


# ---------------------------------------------------------------------------
# Importação do ingestor com fallback informativo
# ---------------------------------------------------------------------------

def _importar_ingestor():
    try:
        # Garante que src/ está no sys.path quando chamado de scripts/
        raiz = Path(__file__).resolve().parent.parent
        src = raiz / "src"
        if str(src) not in sys.path:
            sys.path.insert(0, str(src))
        from fito_aimm.ingestor import ingerir, ingerir_lote, capacidades, ResultadoIngestao
        return ingerir, ingerir_lote, capacidades, ResultadoIngestao
    except ImportError as exc:
        _print_erro(f"Não foi possível importar o módulo ingestor: {exc}")
        _print_aviso("Certifique-se de que as dependências estão instaladas:")
        _print_aviso("  pip install -r requirements.txt")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Subcomandos
# ---------------------------------------------------------------------------

def cmd_arquivo(args: argparse.Namespace) -> int:
    ingerir, _, _, _ = _importar_ingestor()
    salvar = Path(args.salvar) if args.salvar else None
    resultado = ingerir(args.caminho, tipo="arquivo", salvar_em=salvar)
    _print_resultado(resultado)
    if args.json:
        print(json.dumps({"status": resultado.status, "titulo": resultado.titulo, "erro": resultado.erro}, ensure_ascii=False, indent=2))
    return 0 if resultado.status != "erro" else 1


def cmd_url(args: argparse.Namespace) -> int:
    ingerir, _, _, _ = _importar_ingestor()
    salvar = Path(args.salvar) if args.salvar else None
    resultado = ingerir(args.url, tipo="url", salvar_em=salvar)
    _print_resultado(resultado)
    if args.json:
        print(json.dumps({"status": resultado.status, "titulo": resultado.titulo, "erro": resultado.erro}, ensure_ascii=False, indent=2))
    return 0 if resultado.status != "erro" else 1


def cmd_doi(args: argparse.Namespace) -> int:
    ingerir, _, _, _ = _importar_ingestor()
    salvar = Path(args.salvar) if args.salvar else None
    resultado = ingerir(args.doi, tipo="doi", salvar_em=salvar)
    _print_resultado(resultado)
    if args.json:
        print(json.dumps(resultado.conteudo, ensure_ascii=False, indent=2))
    return 0 if resultado.status != "erro" else 1


def cmd_api(args: argparse.Namespace) -> int:
    ingerir, _, _, _ = _importar_ingestor()
    salvar = Path(args.salvar) if args.salvar else None

    # Parâmetros adicionais passados como chave=valor
    parametros: dict[str, str] = {}
    if args.param:
        for p in args.param:
            if "=" in p:
                k, v = p.split("=", 1)
                parametros[k.strip()] = v.strip()
            else:
                _print_aviso(f"Parâmetro ignorado (formato esperado chave=valor): {p}")

    cabecalhos: dict[str, str] = {}
    if args.header:
        for h in args.header:
            if ":" in h:
                k, v = h.split(":", 1)
                cabecalhos[k.strip()] = v.strip()

    resultado = ingerir(
        args.endpoint,
        tipo="api",
        metodo_api=args.metodo,
        parametros_api=parametros or None,
        cabecalhos_api=cabecalhos or None,
        salvar_em=salvar,
    )
    _print_resultado(resultado)
    if args.json:
        dados = resultado.conteudo.get("dados", {})
        print(json.dumps(dados, ensure_ascii=False, indent=2))
    return 0 if resultado.status != "erro" else 1


def cmd_lote(args: argparse.Namespace) -> int:
    _, ingerir_lote, _, _ = _importar_ingestor()
    salvar = Path(args.salvar) if args.salvar else None

    arquivo_lista = Path(args.arquivo_lista)
    if not arquivo_lista.exists():
        _print_erro(f"Arquivo de lista não encontrado: {arquivo_lista}")
        return 1

    linhas = arquivo_lista.read_text(encoding="utf-8").splitlines()
    fontes = [l.strip() for l in linhas if l.strip() and not l.strip().startswith("#")]

    if not fontes:
        _print_aviso("Nenhuma fonte encontrada no arquivo de lista (linhas em branco ou comentadas com # são ignoradas).")
        return 0

    print(f"\n  Ingerindo {len(fontes)} fonte(s)...\n")
    resultados = ingerir_lote(fontes, salvar_em=salvar)

    sucessos = sum(1 for r in resultados if r.status == "sucesso")
    parciais = sum(1 for r in resultados if r.status == "parcial")
    erros_count = sum(1 for r in resultados if r.status == "erro")

    for r in resultados:
        _print_resultado(r)

    _print_sep()
    print(f"  RESUMO: {len(resultados)} fontes — {sucessos} sucesso(s) | {parciais} parcial(is) | {erros_count} erro(s)")
    _print_sep()
    return 0 if erros_count == 0 else 1


def cmd_capacidades(args: argparse.Namespace) -> int:
    _, _, capacidades, _ = _importar_ingestor()
    caps = capacidades()

    print("\n  FORMATOS DE ARQUIVO SUPORTADOS")
    print("  " + _SEP[2:])
    for categoria, exts in caps["formatos_arquivo"].items():
        lista = "  ".join(exts)
        print(f"  {categoria:<15}: {lista}")

    print("\n  FONTES REMOTAS SUPORTADAS")
    print("  " + _SEP[2:])
    for fonte in caps["fontes_remotas"]:
        descricoes = {
            "url": "Download e extração de páginas web ou arquivos remotos",
            "doi": "Resolução de metadados via CrossRef API (api.crossref.org)",
            "api": "Chamadas a endpoints REST com suporte a GET/POST/PUT/DELETE",
        }
        print(f"  {fonte.upper():<10}: {descricoes.get(fonte, fonte)}")

    print("\n  DEPENDÊNCIAS OPCIONAIS")
    print("  " + _SEP[2:])
    for lib, ok in caps["dependencias"].items():
        status = "✓ disponível" if ok else "✗ não instalada"
        print(f"  {status}  —  {lib}")

    print()
    return 0


def cmd_interativo(args: argparse.Namespace) -> int:
    """Modo interativo guiado passo a passo."""
    ingerir, _, _, _ = _importar_ingestor()

    _print_banner()
    print("  Modo interativo — responda às perguntas abaixo.\n")
    print("  Tipos de fonte disponíveis:")
    print("    1. arquivo  — arquivo local (pdf, xlsx, docx, pptx, json, md, shp…)")
    print("    2. url      — URL de página web ou arquivo remoto")
    print("    3. doi      — DOI de publicação científica")
    print("    4. api      — endpoint de API REST")
    print()

    while True:
        tipo_input = input("  Tipo de fonte [1-4 ou nome]: ").strip().lower()
        mapa = {"1": "arquivo", "2": "url", "3": "doi", "4": "api",
                 "arquivo": "arquivo", "url": "url", "doi": "doi", "api": "api"}
        if tipo_input in mapa:
            tipo = mapa[tipo_input]
            break
        print("  Por favor, escolha um tipo válido (1, 2, 3, 4 ou nome).")

    print()
    prompts = {
        "arquivo": "  Caminho do arquivo: ",
        "url": "  URL (ex: https://exemplo.com/dados.json): ",
        "doi": "  DOI (ex: 10.1016/j.forpol.2021.102447): ",
        "api": "  Endpoint da API (ex: https://api.ibge.gov.br/v3/...): ",
    }
    fonte = input(prompts[tipo]).strip()
    if not fonte:
        _print_erro("Fonte não pode ser vazia.")
        return 1

    salvar_input = input("\n  Diretório para salvar resultado JSON (deixe vazio para não salvar): ").strip()
    salvar = Path(salvar_input) if salvar_input else None

    print(f"\n  Processando '{fonte}'...\n")

    kwargs: dict = {"tipo": tipo, "salvar_em": salvar}

    if tipo == "api":
        metodo = input("  Método HTTP [GET]: ").strip().upper() or "GET"
        kwargs["metodo_api"] = metodo

    resultado = ingerir(fonte, **kwargs)
    _print_resultado(resultado)

    continuar = input("\n  Deseja ingerir outra fonte? [s/N]: ").strip().lower()
    if continuar in ("s", "sim", "y", "yes"):
        return cmd_interativo(args)

    return 0 if resultado.status != "erro" else 1


# ---------------------------------------------------------------------------
# Parser principal
# ---------------------------------------------------------------------------

def _criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ingerir",
        description=textwrap.dedent("""\
            FITO+ AMAZÔNIA — Interface de Ingestão de Dados (AIMM)
            ─────────────────────────────────────────────────────────
            Ingere documentos, arquivos, URLs, DOIs e APIs no sistema.
        """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            exemplos:
              %(prog)s arquivo relatorio.pdf
              %(prog)s arquivo dados.xlsx --salvar outputs/ingestao/
              %(prog)s url https://exemplo.com/dados.json
              %(prog)s doi 10.1016/j.forpol.2021.102447
              %(prog)s api https://servicodados.ibge.gov.br/api/v1/localidades/estados
              %(prog)s lote lista_fontes.txt --salvar outputs/ingestao/
              %(prog)s capacidades
              %(prog)s interativo
        """),
    )
    sub = parser.add_subparsers(dest="comando", metavar="COMANDO")

    # --- arquivo ---
    p_arquivo = sub.add_parser(
        "arquivo",
        help="Ingerir arquivo local (pdf, xlsx, docx, pptx, json, md, shp…)",
        description="Ingere e extrai conteúdo de um arquivo local.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            formatos suportados:
              planilhas     : .xlsx  .xls  .ods
              documentos    : .docx  .pdf
              apresentações : .pptx
              dados         : .json  .yaml  .csv  .tsv  .md  .txt
              GIS           : .geojson  .shp  .gpkg  .kml  .gml

            exemplos:
              %(prog)s relatorio_ambiental.pdf
              %(prog)s indicadores.xlsx --salvar outputs/ingestao/
              %(prog)s mapa_manaus.geojson --json
        """),
    )
    p_arquivo.add_argument("caminho", help="Caminho do arquivo a ingerir")
    p_arquivo.add_argument("--salvar", metavar="DIR", help="Diretório para salvar resultado em JSON")
    p_arquivo.add_argument("--json", action="store_true", help="Exibir resultado em formato JSON")
    p_arquivo.set_defaults(func=cmd_arquivo)

    # --- url ---
    p_url = sub.add_parser(
        "url",
        help="Baixar e ingerir uma URL (página web ou arquivo remoto)",
        description="Baixa e extrai conteúdo de uma URL.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            exemplos:
              %(prog)s https://exemplo.com/relatorio.pdf
              %(prog)s https://dados.gov.br/api/publico/dados.json --salvar outputs/
              %(prog)s https://mapas.ibge.gov.br/open/dados/municipios.geojson
        """),
    )
    p_url.add_argument("url", help="URL a baixar e ingerir")
    p_url.add_argument("--salvar", metavar="DIR", help="Diretório para salvar resultado em JSON")
    p_url.add_argument("--json", action="store_true", help="Exibir resultado em formato JSON")
    p_url.set_defaults(func=cmd_url)

    # --- doi ---
    p_doi = sub.add_parser(
        "doi",
        help="Resolver metadados de um DOI via CrossRef",
        description="Resolve metadados bibliográficos de um DOI usando a API CrossRef.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            O DOI pode ser informado em qualquer um destes formatos:
              10.1016/j.forpol.2021.102447
              doi:10.1016/j.forpol.2021.102447
              https://doi.org/10.1016/j.forpol.2021.102447

            exemplos:
              %(prog)s 10.1016/j.forpol.2021.102447
              %(prog)s https://doi.org/10.18542/amazonica.v11i2.8765 --json
        """),
    )
    p_doi.add_argument("doi", help="DOI da publicação")
    p_doi.add_argument("--salvar", metavar="DIR", help="Diretório para salvar resultado em JSON")
    p_doi.add_argument("--json", action="store_true", help="Exibir metadados completos em JSON")
    p_doi.set_defaults(func=cmd_doi)

    # --- api ---
    p_api = sub.add_parser(
        "api",
        help="Chamar um endpoint de API REST",
        description="Faz uma requisição HTTP a um endpoint de API e retorna os dados.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            exemplos:
              %(prog)s https://servicodados.ibge.gov.br/api/v1/localidades/estados
              %(prog)s https://api.exemplo.com/dados -m GET -p municipio=Manaus -p uf=AM
              %(prog)s https://api.exemplo.com/upload -m POST --header "Authorization: ******"
        """),
    )
    p_api.add_argument("endpoint", help="URL do endpoint de API")
    p_api.add_argument("-m", "--metodo", default="GET", metavar="MÉTODO",
                        help="Método HTTP (GET, POST, PUT, DELETE — padrão: GET)")
    p_api.add_argument("-p", "--param", action="append", metavar="CHAVE=VALOR",
                        help="Parâmetro de query string (pode ser repetido)")
    p_api.add_argument("--header", action="append", metavar="CHAVE: VALOR",
                        help="Cabeçalho HTTP adicional (pode ser repetido)")
    p_api.add_argument("--salvar", metavar="DIR", help="Diretório para salvar resultado em JSON")
    p_api.add_argument("--json", action="store_true", help="Exibir dados da API em formato JSON")
    p_api.set_defaults(func=cmd_api)

    # --- lote ---
    p_lote = sub.add_parser(
        "lote",
        help="Ingerir múltiplas fontes a partir de um arquivo de lista",
        description="Ingere múltiplas fontes listadas em um arquivo de texto (uma por linha).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            formato do arquivo de lista:
              # comentários são ignorados (linha começa com #)
              # URLs, DOIs e caminhos locais são detectados automaticamente

              relatorio.pdf
              dados.xlsx
              https://exemplo.com/municipios.geojson
              10.1016/j.forpol.2021.102447
              https://api.ibge.gov.br/v1/...

            exemplos:
              %(prog)s fontes.txt
              %(prog)s fontes.txt --salvar outputs/ingestao/
        """),
    )
    p_lote.add_argument("arquivo_lista", help="Arquivo .txt com uma fonte por linha")
    p_lote.add_argument("--salvar", metavar="DIR", help="Diretório para salvar resultados em JSON")
    p_lote.set_defaults(func=cmd_lote)

    # --- capacidades ---
    p_caps = sub.add_parser(
        "capacidades",
        help="Listar formatos e fontes suportados e dependências instaladas",
        description="Exibe todos os formatos suportados e o status das dependências opcionais.",
    )
    p_caps.set_defaults(func=cmd_capacidades)

    # --- interativo ---
    p_inter = sub.add_parser(
        "interativo",
        help="Modo interativo guiado — responda às perguntas para ingerir dados",
        description="Modo guiado passo a passo para ingestão de dados.",
    )
    p_inter.set_defaults(func=cmd_interativo)

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = _criar_parser()
    args = parser.parse_args(argv)

    _print_banner()

    if not args.comando:
        parser.print_help()
        print("\n  Dica: use  python scripts/ingerir.py interativo  para o modo guiado.\n")
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
