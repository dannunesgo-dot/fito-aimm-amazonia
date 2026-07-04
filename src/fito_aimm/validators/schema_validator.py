from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator


class SchemaValidationIssue(BaseModel):
    row_number: int
    field: str
    message: str
    value: str = ""

    def format(self, schema_name: str) -> str:
        suffix = f" (valor={self.value})" if self.value else ""
        return f"{schema_name} linha {self.row_number}: {self.field} {self.message}{suffix}"


class SchemaValidationResult(BaseModel):
    schema_name: str
    total_rows: int
    validated_rows: list[BaseModel] = Field(default_factory=list)
    errors: list[SchemaValidationIssue] = Field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


class AIMMIndicatorInputRow(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id_indicador: str = Field(min_length=1)
    dimensao_aimm: str
    score_bruto_preliminar: float | None = None
    nivel_confianca: str
    status_prontidao_benchmark: str
    id_benchmark: str = Field(min_length=1)
    limitacao: str = ""

    allowed_dimensions: ClassVar[set[str]] = {"gap", "intensidade", "mercado", "risco", "monitoramento"}
    allowed_confidence: ClassVar[set[str]] = {"alto", "medio", "baixo", "bloqueado"}
    allowed_readiness: ClassVar[set[str]] = {
        "benchmark_utilizavel",
        "proxy_utilizavel_com_validacao",
        "proxy_baixa_confianca",
        "bloqueado",
        "revisar",
    }

    @field_validator("score_bruto_preliminar", mode="before")
    @classmethod
    def parse_score(cls, value: Any) -> float | None:
        if value is None:
            return None
        texto = str(value).strip()
        if not texto:
            return None
        return float(texto.replace(",", "."))

    @field_validator("dimensao_aimm")
    @classmethod
    def validate_dimension(cls, value: str) -> str:
        if value not in cls.allowed_dimensions:
            raise ValueError(f"deve estar em {sorted(cls.allowed_dimensions)}")
        return value

    @field_validator("nivel_confianca")
    @classmethod
    def validate_confidence(cls, value: str) -> str:
        if value not in cls.allowed_confidence:
            raise ValueError(f"deve estar em {sorted(cls.allowed_confidence)}")
        return value

    @field_validator("status_prontidao_benchmark")
    @classmethod
    def validate_readiness(cls, value: str) -> str:
        if value not in cls.allowed_readiness:
            raise ValueError(f"deve estar em {sorted(cls.allowed_readiness)}")
        return value

    @model_validator(mode="after")
    def validate_score_rules(self) -> "AIMMIndicatorInputRow":
        if self.status_prontidao_benchmark == "bloqueado":
            return self
        if self.score_bruto_preliminar is None:
            raise ValueError("score_bruto_preliminar deve ser informado quando o benchmark não estiver bloqueado")
        if not 0 <= self.score_bruto_preliminar <= 100:
            raise ValueError("score_bruto_preliminar deve ficar entre 0 e 100")
        return self


class AIMMDimensionPolicyRow(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    dimensao_aimm: str
    peso: float
    papel: str
    descricao: str = ""

    allowed_dimensions: ClassVar[set[str]] = AIMMIndicatorInputRow.allowed_dimensions
    allowed_roles: ClassVar[set[str]] = {"beneficio", "penalizador", "confianca"}

    @field_validator("peso", mode="before")
    @classmethod
    def parse_weight(cls, value: Any) -> float:
        return float(str(value).strip().replace(",", "."))

    @field_validator("dimensao_aimm")
    @classmethod
    def validate_dimension(cls, value: str) -> str:
        if value not in cls.allowed_dimensions:
            raise ValueError(f"deve estar em {sorted(cls.allowed_dimensions)}")
        return value

    @field_validator("papel")
    @classmethod
    def validate_role(cls, value: str) -> str:
        if value not in cls.allowed_roles:
            raise ValueError(f"deve estar em {sorted(cls.allowed_roles)}")
        return value

    @model_validator(mode="after")
    def validate_weight_range(self) -> "AIMMDimensionPolicyRow":
        if not 0 <= self.peso <= 1:
            raise ValueError("peso deve ficar entre 0 e 1")
        return self


class AIMMBlockerRow(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id_bloqueio: str = Field(min_length=1)
    bloqueio: str = Field(min_length=1)
    criticidade: str
    area: str = Field(min_length=1)
    efeito_no_score: str = Field(min_length=1)

    allowed_criticality: ClassVar[set[str]] = {"alta", "media", "média", "baixa"}

    @field_validator("criticidade")
    @classmethod
    def validate_criticality(cls, value: str) -> str:
        if value not in cls.allowed_criticality:
            raise ValueError(f"deve estar em {sorted(cls.allowed_criticality)}")
        return value


class SchemaValidator:
    registry: ClassVar[dict[str, type[BaseModel]]] = {
        "aimm_indicator_inputs": AIMMIndicatorInputRow,
        "aimm_dimension_policy": AIMMDimensionPolicyRow,
        "aimm_blockers": AIMMBlockerRow,
    }

    def __init__(self, model: str | type[BaseModel], delimiter: str = ";"):
        if isinstance(model, str):
            try:
                self.model = self.registry[model]
            except KeyError as exc:
                raise ValueError(f"Schema desconhecido: {model}") from exc
            self.schema_name = model
        else:
            self.model = model
            self.schema_name = model.__name__
        self.delimiter = delimiter

    def read_csv(self, path: Path) -> list[dict[str, str]]:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle, delimiter=self.delimiter))

    def validate_csv(self, path: Path) -> SchemaValidationResult:
        return self.validate_rows(self.read_csv(path))

    def validate_rows(self, rows: list[dict[str, Any]]) -> SchemaValidationResult:
        validated_rows: list[BaseModel] = []
        errors: list[SchemaValidationIssue] = []

        for row_number, row in enumerate(rows, start=2):
            try:
                validated_rows.append(self.model.model_validate(row))
            except ValidationError as exc:
                errors.extend(self._convert_errors(exc, row_number, row))

        return SchemaValidationResult(
            schema_name=self.schema_name,
            total_rows=len(rows),
            validated_rows=validated_rows,
            errors=errors,
        )

    def _convert_errors(
        self,
        exc: ValidationError,
        row_number: int,
        row: dict[str, Any],
    ) -> list[SchemaValidationIssue]:
        issues: list[SchemaValidationIssue] = []
        for error in exc.errors():
            loc = ".".join(str(part) for part in error.get("loc", [])) or "__root__"
            issues.append(
                SchemaValidationIssue(
                    row_number=row_number,
                    field=loc,
                    message=error.get("msg", "inválido"),
                    value=str(row.get(loc, "") or ""),
                )
            )
        return issues
