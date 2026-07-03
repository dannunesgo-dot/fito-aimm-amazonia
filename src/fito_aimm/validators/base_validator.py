"""
Validadores genéricos para dados CSV e schemas JSON.

Refactor/Phase2: Criação de camada de validação reutilizável.
Changelog:
- 2026-07-03: Implementação inicial de SchemaValidator e CSVValidator
"""

import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from abc import ABC, abstractmethod
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exceção customizada para erros de validação."""
    pass


class BaseValidator(ABC):
    """Classe base para validadores."""
    
    def __init__(self, strict: bool = False):
        """
        Inicializa validador.
        
        Args:
            strict: Se True, qualquer erro causa falha imediata
        """
        self.strict = strict
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """Valida dados. Retorna True se válido."""
        pass
    
    def add_error(self, msg: str) -> None:
        """Adiciona erro."""
        self.errors.append(msg)
        if self.strict:
            raise ValidationError(msg)
    
    def add_warning(self, msg: str) -> None:
        """Adiciona aviso."""
        self.warnings.append(msg)
    
    def clear(self) -> None:
        """Limpa erros e avisos."""
        self.errors = []
        self.warnings = []


class SchemaValidator(BaseValidator):
    """Validador de schema JSON contra modelo Pydantic."""
    
    def __init__(self, schema: Optional[Dict[str, Any]] = None, strict: bool = False):
        """
        Inicializa validador de schema.
        
        Args:
            schema: Dicionário de schema JSON (opcional)
            strict: Se True, falha em primeira validação
        """
        super().__init__(strict)
        self.schema = schema or {}
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Valida dados contra schema.
        
        Args:
            data: Dicionário a validar
            
        Returns:
            True se válido
        """
        self.clear()
        
        if not isinstance(data, dict):
            self.add_error(f"Dados deve ser um dicionário, recebido {type(data)}")
            return False
        
        # Verificar campos obrigatórios
        required_fields = self.schema.get("required", [])
        for field in required_fields:
            if field not in data:
                self.add_error(f"Campo obrigatório ausente: {field}")
            elif data[field] is None or str(data[field]).strip() == "":
                self.add_error(f"Campo obrigatório vazio: {field}")
        
        # Validar tipos
        properties = self.schema.get("properties", {})
        for field, field_schema in properties.items():
            if field not in data:
                continue
            
            value = data[field]
            if value is None:
                continue
            
            expected_type = field_schema.get("type", "string")
            if not self._validate_type(value, expected_type):
                self.add_error(
                    f"Campo {field}: tipo inválido. "
                    f"Esperado {expected_type}, recebido {type(value).__name__}"
                )
        
        return len(self.errors) == 0
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Valida tipo de valor."""
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        
        if expected_type not in type_map:
            return True  # Tipo desconhecido, não valida
        
        return isinstance(value, type_map[expected_type])


class CSVValidator(BaseValidator):
    """Validador de arquivos CSV."""
    
    def __init__(
        self,
        delimiter: str = ";",
        encoding: str = "utf-8-sig",
        required_columns: Optional[List[str]] = None,
        strict: bool = False
    ):
        """
        Inicializa validador CSV.
        
        Args:
            delimiter: Delimitador do CSV
            encoding: Encoding do arquivo
            required_columns: Colunas obrigatórias
            strict: Se True, falha em primeira validação
        """
        super().__init__(strict)
        self.delimiter = delimiter
        self.encoding = encoding
        self.required_columns = required_columns or []
        self.column_names: List[str] = []
    
    def validate(self, file_path: Union[str, Path]) -> bool:
        """
        Valida arquivo CSV.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            True se válido
        """
        self.clear()
        
        file_path = Path(file_path)
        if not file_path.exists():
            self.add_error(f"Arquivo não encontrado: {file_path}")
            return False
        
        if file_path.stat().st_size == 0:
            self.add_error(f"Arquivo vazio: {file_path}")
            return False
        
        try:
            with file_path.open("r", encoding=self.encoding, newline="") as f:
                reader = csv.DictReader(f, delimiter=self.delimiter)
                
                if not reader.fieldnames:
                    self.add_error("CSV sem cabeçalho")
                    return False
                
                self.column_names = reader.fieldnames
                
                # Validar colunas obrigatórias
                for col in self.required_columns:
                    if col not in self.column_names:
                        self.add_error(f"Coluna obrigatória ausente: {col}")
                
                # Validar linhas
                for i, row in enumerate(reader, start=2):
                    if not row or all(v is None or str(v).strip() == "" for v in row.values()):
                        self.add_warning(f"Linha {i}: vazia ou apenas NULL")
                
        except UnicodeDecodeError as e:
            self.add_error(f"Erro de encoding: {e}")
            return False
        except Exception as e:
            self.add_error(f"Erro ao ler CSV: {e}")
            return False
        
        return len(self.errors) == 0


class BusinessRuleValidator(BaseValidator):
    """Validador de regras de negócio."""
    
    def __init__(self, rules: Optional[Dict[str, Any]] = None, strict: bool = False):
        """
        Inicializa validador de regras de negócio.
        
        Args:
            rules: Dicionário de regras customizadas
            strict: Se True, falha em primeira validação
        """
        super().__init__(strict)
        self.rules = rules or {}
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Valida dados contra regras de negócio.
        
        Args:
            data: Dicionário a validar
            
        Returns:
            True se válido
        """
        self.clear()
        
        # Exemplo: validar que score está entre 0-100
        if "score" in data and (data["score"] < 0 or data["score"] > 100):
            self.add_error(f"Score fora de 0-100: {data['score']}")
        
        # Exemplo: validar que dimensões são válidas
        valid_dims = self.rules.get("valid_dimensions", [])
        if valid_dims and "dimensao_aimm" in data:
            if data["dimensao_aimm"] not in valid_dims:
                self.add_error(f"Dimensão inválida: {data['dimensao_aimm']}")
        
        # Exemplo: validar relacionamentos
        if "peso" in data and (data["peso"] < 0 or data["peso"] > 1):
            self.add_error(f"Peso deve estar entre 0-1: {data['peso']}")
        
        return len(self.errors) == 0


class AggregateValidator(BaseValidator):
    """Validador que agrupa múltiplos validadores."""
    
    def __init__(self, validators: Optional[List[BaseValidator]] = None, strict: bool = False):
        """
        Inicializa validador agregado.
        
        Args:
            validators: Lista de validadores
            strict: Se True, falha em primeira validação
        """
        super().__init__(strict)
        self.validators = validators or []
    
    def add_validator(self, validator: BaseValidator) -> None:
        """Adiciona validador."""
        self.validators.append(validator)
    
    def validate(self, data: Any) -> bool:
        """
        Executa todos os validadores.
        
        Args:
            data: Dados a validar
            
        Returns:
            True se todos validadores passam
        """
        self.clear()
        all_valid = True
        
        for validator in self.validators:
            if not validator.validate(data):
                all_valid = False
                self.errors.extend(validator.errors)
                self.warnings.extend(validator.warnings)
                
                if self.strict:
                    break
        
        return all_valid
