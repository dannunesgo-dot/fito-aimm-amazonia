from pathlib import Path

from fito_aimm.validators import SchemaValidator


def test_schema_validator_accepts_valid_csv(fixtures_dir: Path):
    result = SchemaValidator("aimm_indicator_inputs").validate_csv(fixtures_dir / "sample_aimm_inputs_valid.csv")

    assert result.is_valid is True
    assert result.total_rows == 2
    assert len(result.validated_rows) == 2


def test_schema_validator_reports_typed_errors(fixtures_dir: Path):
    result = SchemaValidator("aimm_indicator_inputs").validate_csv(fixtures_dir / "sample_aimm_inputs_invalid.csv")

    assert result.is_valid is False
    messages = [issue.format(result.schema_name) for issue in result.errors]
    assert any("score_bruto_preliminar" in message for message in messages)
