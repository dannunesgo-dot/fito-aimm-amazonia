import pandas as pd
import yaml

from fito_aimm.mapaosc.classifier import classificar_organizacao
from fito_aimm.mapaosc.normalizer import normalizar_texto


def test_classificador_prioriza_cooperativa_com_contato(fixtures_dir):
    criterios = yaml.safe_load((fixtures_dir.parents[1] / "config" / "criterios_triagem_mapaosc.yaml").read_text(encoding="utf-8"))
    row = pd.Series(
        {
            "nome": "Cooperativa Amazônia Viva",
            "situacao": "ativa",
            "email": "contato@coop.org",
            "telefone": "92999999999",
            "endereco": "Rua Rio Negro 10",
            "descricao": "cooperativa de bioeconomia amazônia agricultura",
        }
    )
    colmap = {
        "situacao": "situacao",
        "email": "email",
        "telefone": "telefone",
        "endereco": "endereco",
    }

    resultado = classificar_organizacao(
        row,
        colmap,
        criterios,
        " ".join(str(valor) for valor in row.values),
        normalizar_texto,
    )

    assert resultado["classificacao_triagem"] == "alta_prioridade"
    assert "cooperativa" in resultado["marcadores_triagem"]
