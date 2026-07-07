"""
API Backend Local - Fito AIMM Amazonia
Roda em: 127.0.0.1:8000
Gateway (Caddy): 127.0.0.1:8080
"""

import os
import logging
from datetime import datetime
from functools import wraps

import requests
from flask import Flask, request, jsonify, abort

# ========================================
# Configuração
# ========================================

app = Flask(__name__)

# Logger
logging.basicConfig(
    level=logging.DEBUG if os.getenv("DEBUG", "false").lower() == "true" else logging.INFO
)
logger = logging.getLogger(__name__)

# Variáveis de ambiente
WORLDBANK_API_URL = os.getenv("WORLDBANK_API_URL", "https://api.worldbank.org/v2").rstrip("/")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Timeout padrão para chamadas externas
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "15"))


# ========================================
# Helpers
# ========================================

def error_response(message: str, status_code: int = 400, details: str | None = None):
    payload = {"status": "error", "message": message}
    if details:
        payload["details"] = details
    return jsonify(payload), status_code


def parse_worldbank_response(response: requests.Response):
    """
    World Bank API geralmente retorna:
    [
      {pagination...},
      [items...]
    ]
    """
    try:
        data = response.json()
    except ValueError:
        return None, None, "Invalid JSON from World Bank API"

    if not isinstance(data, list) or len(data) < 2:
        return None, None, "Unexpected World Bank response format"

    meta = data[0]
    items = data[1]

    if not isinstance(meta, dict):
        return None, None, "Invalid metadata format from World Bank API"

    # Em alguns casos, items pode vir como mensagem de erro (dict) ou None
    if items is None:
        items = []
    if not isinstance(items, list):
        return None, None, "Invalid items format from World Bank API"

    return meta, items, None


def call_worldbank(path: str, params: dict):
    url = f"{WORLDBANK_API_URL}{path}"
    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        meta, items, parse_error = parse_worldbank_response(response)
        if parse_error:
            logger.error(f"❌ Parse World Bank falhou: {parse_error}")
            return None, None, error_response("World Bank response parse error", 502, parse_error)
        return meta, items, None

    except requests.Timeout:
        logger.error("❌ Timeout ao consultar World Bank API")
        return None, None, error_response("World Bank API timeout", 504)

    except requests.HTTPError as e:
        logger.error(f"❌ HTTP error na World Bank API: {str(e)}")
        status = e.response.status_code if e.response is not None else 502
        return None, None, error_response("World Bank API HTTP error", 502, f"upstream_status={status}")

    except requests.RequestException as e:
        logger.error(f"❌ Erro de conexão com World Bank API: {str(e)}")
        return None, None, error_response("World Bank API connection error", 502, str(e))


# ========================================
# Middleware: Validar Bearer Token
# ========================================

def verify_bearer_token(f):
    """Decorator para validar Bearer token (vindo do Caddy)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "").strip()

        # Esperado: "Bearer <token>"
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning("❌ Requisição sem Bearer token válido")
            abort(401)

        token = auth_header.split(" ", 1)[1].strip() if " " in auth_header else ""
        if not token:
            logger.warning("❌ Token vazio")
            abort(401)

        # Não logar token completo por segurança
        logger.info("✅ Bearer token recebido e validado (formato)")
        return f(*args, **kwargs)

    return decorated_function


# ========================================
# ROTAS: Públicas
# ========================================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "service": "Fito AIMM Amazonia API",
        "version": "1.1.0",
        "status": "online",
        "environment": ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "fito-aimm-amazonia-backend",
        "environment": ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 200


# ========================================
# ROTAS: World Bank Indicators
# ========================================

@app.route("/worldbank/countries", methods=["GET"])
@verify_bearer_token
def get_countries():
    """
    GET /worldbank/countries?per_page=50&page=1
    """
    logger.info("📤 Consultando World Bank: listando países...")

    per_page = request.args.get("per_page", "50")
    page = request.args.get("page", "1")

    if not per_page.isdigit() or not page.isdigit():
        return error_response("Query params 'per_page' e 'page' devem ser numéricos", 400)

    params = {"format": "json", "per_page": per_page, "page": page}
    meta, items, err = call_worldbank("/country", params)
    if err:
        return err

    logger.info(f"✅ Resposta: {len(items)} países")
    return jsonify({
        "status": "success",
        "source": "World Bank API",
        "pagination": {
            "page": meta.get("page"),
            "pages": meta.get("pages"),
            "per_page": meta.get("per_page"),
            "total": meta.get("total")
        },
        "data": items
    }), 200


@app.route("/worldbank/indicators", methods=["GET"])
@verify_bearer_token
def get_indicators():
    """
    GET /worldbank/indicators?search=gdp&per_page=50&page=1
    """
    search = request.args.get("search", "").strip()
    logger.info(f"📤 Consultando World Bank: indicadores (search='{search}')...")

    per_page = request.args.get("per_page", "50")
    page = request.args.get("page", "1")

    if not per_page.isdigit() or not page.isdigit():
        return error_response("Query params 'per_page' e 'page' devem ser numéricos", 400)

    params = {"format": "json", "per_page": per_page, "page": page}
    meta, items, err = call_worldbank("/indicator", params)
    if err:
        return err

    if search:
        items = [ind for ind in items if search.lower() in (ind.get("name") or "").lower()]

    logger.info(f"✅ Resposta: {len(items)} indicadores (filtrados)")
    return jsonify({
        "status": "success",
        "source": "World Bank API",
        "search_filter": search,
        "pagination": {
            "page": meta.get("page"),
            "pages": meta.get("pages"),
            "per_page": meta.get("per_page"),
            "total": meta.get("total"),
            "total_found": len(items)
        },
        "data": items[:10]  # Top 10
    }), 200


@app.route("/worldbank/data/<country>/<indicator>", methods=["GET"])
@verify_bearer_token
def get_country_indicator(country: str, indicator: str):
    """
    GET /worldbank/data/BR/SP.POP.TOTL?date=2010:2024
    """
    country = (country or "").upper().strip()
    indicator = (indicator or "").strip()

    if len(country) not in (2, 3):
        return error_response("Country deve ter 2 ou 3 letras (ex.: BR, USA)", 400)
    if not indicator:
        return error_response("Indicator é obrigatório", 400)

    logger.info(f"📤 Consultando World Bank: {country} / {indicator}...")

    params = {
        "format": "json",
        "per_page": 500
    }
    date_filter = request.args.get("date", "").strip()
    if date_filter:
        params["date"] = date_filter

    path = f"/country/{country}/indicator/{indicator}"
    meta, items, err = call_worldbank(path, params)
    if err:
        return err

    if not items:
        logger.warning(f"⚠️ Nenhum dado encontrado para {country}/{indicator}")
        return jsonify({
            "status": "not_found",
            "country": country,
            "indicator": indicator,
            "message": "No data available for this country/indicator combination"
        }), 404

    # Dados de contexto
    first_item = items[0] if items else {}
    country_info = first_item.get("country", {}) if isinstance(first_item, dict) else {}
    indicator_info = first_item.get("indicator", {}) if isinstance(first_item, dict) else {}

    # Normalizar série temporal com valores não nulos
    series = []
    for v in items:
        if not isinstance(v, dict):
            continue
        value = v.get("value")
        if value is None:
            continue
        series.append({
            "year": v.get("date"),
            "value": value,
            "obs_status": v.get("obs_status"),
            "decimal": v.get("decimal")
        })

    logger.info(f"✅ Resposta: {len(series)} registros com valor")
    return jsonify({
        "status": "success",
        "source": "World Bank API",
        "pagination": {
            "page": meta.get("page"),
            "pages": meta.get("pages"),
            "per_page": meta.get("per_page"),
            "total": meta.get("total")
        },
        "country": {
            "code": country_info.get("id", country),
            "name": country_info.get("value")
        },
        "indicator": {
            "code": indicator,
            "name": indicator_info.get("value", "Unknown")
        },
        "data": series
    }), 200


# ========================================
# ROTAS: Teste
# ========================================

@app.route("/test", methods=["GET"])
@verify_bearer_token
def test_auth():
    auth_header = request.headers.get("Authorization", "")
    token_type = auth_header.split()[0] if auth_header.split() else None

    return jsonify({
        "status": "success",
        "message": "Authentication successful",
        "auth_header_received": bool(auth_header),
        "token_type": token_type,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 200


# ========================================
# Error Handlers
# ========================================

@app.errorhandler(401)
def unauthorized(_error):
    return jsonify({"status": "error", "message": "Unauthorized"}), 401


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"status": "error", "message": "Not Found"}), 404


@app.errorhandler(500)
def internal_error(_error):
    return jsonify({"status": "error", "message": "Internal Server Error"}), 500


# ========================================
# Main
# ========================================

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🚀 Iniciando API Backend")
    logger.info(f"Environment     : {ENVIRONMENT}")
    logger.info(f"World Bank URL  : {WORLDBANK_API_URL}")
    logger.info(f"Timeout (s)     : {REQUEST_TIMEOUT_SECONDS}")
    logger.info("=" * 60)

    app.run(
        host="127.0.0.1",
        port=8000,
        debug=(ENVIRONMENT == "development"),
        use_reloader=False
    )