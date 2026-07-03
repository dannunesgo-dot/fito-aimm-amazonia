"""
Validadores específicos para AIMM.

Refactor/Phase2: Validadores de domínio AIMM.
"""

from typing import List, Dict, Any, Set, Optional
from .base_validator import BaseValidator
import yaml
from pathlib import Path


class AIMMEngineValidator(BaseValidator):
    """Validador específico do motor AIMM."""
    
    def __init__(self, rules_path: Optional[Path] = None, strict: bool = False):
        """
        Inicializa validador AIMM Engine.
        
        Args:
            rules_path: Caminho para arquivo de rules YAML
            strict: Se True, falha em primeira validação
        """
        super().__init__(strict)
        self.rules = {}
        
        if rules_path and rules_path.exists():
            with rules_path.open("r", encoding="utf-8") as f:
                self.rules = yaml.safe_load(f) or {}
    
    def validate_inputs(
        self,
        inputs: List[Dict[str, Any]],
        dim_policy: List[Dict[str, Any]],
        blockers: List[Dict[str, Any]]
    ) -> bool:
        """
        Valida inputs, políticas de dimensão e bloqueios.
        
        Args:
            inputs: Lista de indicadores
            dim_policy: Política de dimensões
            blockers: Bloqueios registrados
            
        Returns:
            True se válido
        """
        self.clear()
        
        # Validar dimensões
        valid_dims = set(self.rules.get("dimensoes", []))
        policy_dims = {r.get("dimensao_aimm") for r in dim_policy if "dimensao_aimm" in r}
        
        if policy_dims != valid_dims:
            self.add_error(
                f"Dimensões da política não coincidem com regras. "
                f"Policy: {sorted(policy_dims)}, Rules: {sorted(valid_dims)}"
            )
        
        # Validar pesos
        weight_sum = sum(float(r.get("peso", 0)) for r in dim_policy if "peso" in r)
        if abs(weight_sum - 1.0) > 0.001:
            self.add_error(f"Pesos das dimensões somam {weight_sum}, esperado 1.0")
        
        # Validar indicadores
        seen_ids: Set[str] = set()
        for i, row in enumerate(inputs, start=2):
            iid = str(row.get("id_indicador", "")).strip()
            
            if not iid:
                self.add_error(f"Linha {i}: id_indicador vazio")
            elif iid in seen_ids:
                self.add_error(f"Linha {i}: id_indicador duplicado: {iid}")
            
            seen_ids.add(iid)
            
            # Validar dimensão
            dim = str(row.get("dimensao_aimm", "")).strip()
            if dim and dim not in valid_dims:
                self.add_error(f"Linha {i}: dimensão inválida: {dim}")
            
            # Validar nível de confiança
            conf_level = str(row.get("nivel_confianca", "")).strip()
            valid_conf_levels = self.rules.get("tratamento_confianca", {}).keys()
            if conf_level and conf_level not in valid_conf_levels:
                self.add_error(f"Linha {i}: nível de confiança inválido: {conf_level}")
            
            # Validar score
            try:
                score = float(str(row.get("score_bruto_preliminar", "0")).replace(",", "."))
                if score < 0 or score > 100:
                    self.add_error(f"Linha {i}: score fora de 0-100: {score}")
            except (ValueError, TypeError):
                if str(row.get("status_prontidao_benchmark", "")) != "bloqueado":
                    self.add_error(f"Linha {i}: score_bruto_preliminar inválido")
        
        # Validar bloqueios
        if not blockers:
            self.add_warning("Lista de bloqueios vazia; motor deve registrar bloqueios/lacunas")
        
        return len(self.errors) == 0
    
    def validate(self, data: Any) -> bool:
        """Placeholder para interface BaseValidator."""
        return True


class OSCTriagemValidator(BaseValidator):
    """Validador para triagem de OSCs."""
    
    def __init__(self, strict: bool = False):
        """
        Inicializa validador de triagem OSC.
        
        Args:
            strict: Se True, falha em primeira validação
        """
        super().__init__(strict)
    
    def validate_osc(self, osc_data: Dict[str, Any]) -> bool:
        """
        Valida dados de OSC.
        
        Args:
            osc_data: Dados da organização
            
        Returns:
            True se válido
        """
        self.clear()
        
        # Campos obrigatórios
        required = ["cnpj_ou_id", "nome_organizacao", "municipio", "uf"]
        for field in required:
            if field not in osc_data or not str(osc_data[field]).strip():
                self.add_error(f"Campo obrigatório ausente: {field}")
        
        # Validar UF
        if "uf" in osc_data:
            uf = str(osc_data["uf"]).strip().upper()
            if len(uf) != 2 or not uf.isalpha():
                self.add_error(f"UF inválida: {uf}")
        
        # Validar email se presente
        if osc_data.get("email") and "@" not in str(osc_data["email"]):
            self.add_warning(f"Email com formato suspeito: {osc_data['email']}")
        
        # Validar score de triagem
        if "score_triagem" in osc_data:
            try:
                score = float(osc_data["score_triagem"])
                if score < 0 or score > 100:
                    self.add_error(f"Score de triagem fora de 0-100: {score}")
            except (ValueError, TypeError):
                self.add_error(f"Score de triagem inválido: {osc_data['score_triagem']}")
        
        return len(self.errors) == 0
    
    def validate(self, data: Any) -> bool:
        """Placeholder para interface BaseValidator."""
        return self.validate_osc(data) if isinstance(data, dict) else False


class EvidenceValidator(BaseValidator):
    """Validador para registros de evidência."""
    
    def __init__(self, strict: bool = False):
        """
        Inicializa validador de evidência.
        
        Args:
            strict: Se True, falha em primeira validação
        """
        super().__init__(strict)
    
    def validate_evidence(self, evidence_data: Dict[str, Any]) -> bool:
        """
        Valida dados de evidência.
        
        Args:
            evidence_data: Dados da evidência
            
        Returns:
            True se válido
        """
        self.clear()
        
        # Campos obrigatórios
        required = [
            "id_evidencia",
            "id_fonte",
            "tipo_evidencia",
            "pergunta_ou_lacuna",
            "url_ou_arquivo",
            "titulo_documento",
            "trecho_original_ou_descricao",
            "resumo_ptbr",
            "metodo_extracao",
            "uso_na_calculadora"
        ]
        
        for field in required:
            if field not in evidence_data or not str(evidence_data[field]).strip():
                self.add_error(f"Campo obrigatório ausente em evidência: {field}")
        
        # Validar ID
        if "id_evidencia" in evidence_data:
            idev = str(evidence_data["id_evidencia"]).strip()
            if not idev.startswith("EVD_"):
                self.add_warning(f"ID de evidência sem prefixo EVD_: {idev}")
        
        # Validar status
        valid_status = ["pendente", "validado", "descartado"]
        if evidence_data.get("status_evidencia") not in valid_status:
            self.add_error(
                f"Status de evidência inválido. "
                f"Esperado um de {valid_status}, recebido {evidence_data.get('status_evidencia')}"
            )
        
        return len(self.errors) == 0
    
    def validate(self, data: Any) -> bool:
        """Placeholder para interface BaseValidator."""
        return self.validate_evidence(data) if isinstance(data, dict) else False
