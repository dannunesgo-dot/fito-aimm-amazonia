"""
Modelos de dados Pydantic para AIMM.

Refactor/Phase2: Criação de modelos de validação estruturados.
Changelog:
- 2026-07-03: Implementação inicial com AIMMIndicator, AIMMDimension, etc.
"""

from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
from datetime import datetime


class NivelConfianca(str, Enum):
    """Níveis de confiança para indicadores."""
    MUITO_BAIXO = "muito_baixo"
    BAIXO = "baixo"
    MEDIO = "medio"
    ALTO = "alto"
    MUITO_ALTO = "muito_alto"
    BLOQUEADO = "bloqueado"


class StatusProntidao(str, Enum):
    """Status de prontidão de benchmarks."""
    COMPLETO = "completo"
    PARCIAL = "parcial"
    PRELIMINAR = "preliminar"
    BLOQUEADO = "bloqueado"


class Papel(str, Enum):
    """Papel das dimensões no cálculo AIMM."""
    BENEFICIO = "beneficio"
    PENALIZADOR = "penalizador"
    CONFIANCA = "confianca"


class FaixaScore(str, Enum):
    """Faixas de escore."""
    MUITO_BAIXO = "muito_baixo"
    BAIXO = "baixo"
    MEDIO = "medio"
    ALTO = "alto"
    MUITO_ALTO = "muito_alto"


class AIMMIndicator(BaseModel):
    """Indicador AIMM com validação estruturada."""
    
    id_indicador: str = Field(..., min_length=1, description="ID único do indicador")
    dimensao_aimm: str = Field(..., description="Dimensão AIMM (GAP, INTENSIDADE, MERCADO, RISCO, MONITORAMENTO)")
    id_benchmark: str = Field(..., description="ID do benchmark relacionado")
    score_bruto_preliminar: float = Field(..., ge=0, le=100, description="Score bruto (0-100)")
    nivel_confianca: NivelConfianca = Field(..., description="Nível de confiança do indicador")
    status_prontidao_benchmark: StatusProntidao = Field(..., description="Status de prontidão")
    limitacao: Optional[str] = Field(None, description="Limitações conhecidas")
    
    @validator("id_indicador")
    def validate_id(cls, v):
        if not v.strip():
            raise ValueError("id_indicador não pode estar vazio")
        return v.strip()
    
    class Config:
        use_enum_values = False


class AIMMIndicatorScore(BaseModel):
    """Score calculado de um indicador."""
    
    id_indicador: str
    dimensao_aimm: str
    score_bruto_preliminar: float
    fator_confianca: float
    fator_prontidao: float
    score_ajustado_preliminar: float
    faixa_score_ajustado: FaixaScore
    bloqueado_para_score_final: bool
    limitacao: Optional[str] = None


class AIMMDimensionPolicy(BaseModel):
    """Política de dimensão AIMM (pesos e papéis)."""
    
    dimensao_aimm: str = Field(..., description="Nome da dimensão")
    papel: Papel = Field(..., description="Papel na calculadora")
    peso: float = Field(..., ge=0, le=1, description="Peso da dimensão (0-1)")
    descricao: Optional[str] = None
    
    @validator("peso")
    def validate_peso(cls, v):
        if v < 0 or v > 1:
            raise ValueError("Peso deve estar entre 0 e 1")
        return v


class AIMMDimensionScore(BaseModel):
    """Score calculado de uma dimensão."""
    
    dimensao_aimm: str
    papel: Papel
    peso: float
    indicadores_considerados: int
    indicadores_bloqueados_ou_baixa_prontidao: int
    score_dimensao_preliminar: float
    faixa_score_dimensao: FaixaScore
    status_dimensao: str
    limitacao: Optional[str] = None


class AIMMOverallScore(BaseModel):
    """Score estrutural geral da calculadora AIMM."""
    
    id_resultado: str
    score_bruto_beneficio_preliminar: float
    risk_penalty_preliminar: float
    monitoring_factor_preliminar: float
    score_ajustado_risco_preliminar: float
    score_estrutural_preliminar: float
    faixa_score_estrutural: FaixaScore
    status_resultado: str
    pode_ser_usado_como_score_final: bool
    interpretacao: str


class AIMMBlocker(BaseModel):
    """Bloqueio ou lacuna registrado no motor AIMM."""
    
    id_bloqueio: str
    tipo_bloqueio: str  # "ausencia_dado", "inconsistencia", "limite_confanca", etc.
    descricao: str
    afeta_dimensoes: List[str] = []
    severidade: str = Field(..., regex="^(critica|alta|media|baixa)$")
    resolvido: bool = False


class OSCClassificacao(str, Enum):
    """Classificação de triagem de OSC."""
    ALTA_PRIORIDADE = "alta_prioridade"
    MEDIA_PRIORIDADE = "media_prioridade"
    BAIXA_PRIORIDADE = "baixa_prioridade"


class OSCOrganizacao(BaseModel):
    """Organização (OSC/cooperativa/associação) com validação."""
    
    cnpj_ou_id: str = Field(..., description="CNPJ ou ID da organização")
    nome_organizacao: str = Field(..., min_length=1, description="Nome da organização")
    municipio: str = Field(..., description="Município")
    uf: str = Field(..., min_length=2, max_length=2, description="UF (sigla)")
    codigo_municipio_ibge: Optional[str] = None
    natureza_juridica_ou_classe: Optional[str] = None
    situacao_cadastral_ou_status: Optional[str] = None
    area_atuacao_ou_atividade: Optional[str] = None
    email: Optional[str] = Field(None, regex=r"^[^@]+@[^@]+\.[^@]+$")
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    score_triagem: int = Field(default=0, ge=0, le=100)
    classificacao_triagem: OSCClassificacao
    marcadores_triagem: List[str] = []
    fonte: str = "SRC_MAPA_OSC"
    limitacao: Optional[str] = None
    
    @validator("uf")
    def validate_uf(cls, v):
        if not v.strip().isalpha():
            raise ValueError("UF deve conter apenas letras")
        return v.upper()
    
    class Config:
        use_enum_values = False


class Evidence(BaseModel):
    """Registro de evidência para rastreabilidade."""
    
    id_evidencia: str = Field(..., description="ID único da evidência")
    id_fonte: str = Field(..., description="ID da fonte de dados")
    id_indicador: Optional[str] = None
    tipo_evidencia: str = Field(..., description="Tipo: base_publica_filtrada, motor_calculo_preliminar, etc.")
    pergunta_ou_lacuna: str = Field(..., description="Pergunta que a evidência responde")
    url_ou_arquivo: str = Field(..., description="URL ou caminho do arquivo")
    titulo_documento: str
    pagina_tabela_secao: Optional[str] = None
    trecho_original_ou_descricao: str
    resumo_ptbr: str
    valor_extraido: Optional[str] = None
    unidade: Optional[str] = None
    periodo_referencia: Optional[str] = None
    territorio: Optional[str] = None
    metodo_extracao: str
    nivel_confianca: str = Field(..., regex="^(baixo|medio|alto).*")
    data_coleta: Optional[datetime] = None
    conferido_por: Optional[str] = None
    status_conferencia: str = Field(default="pendente", regex="^(ok|pendente|erro).*")
    limitacoes: Optional[str] = None
    uso_na_calculadora: str
    status_evidencia: str = Field(default="pendente", regex="^(pendente|validado|descartado)$")


class ValidationResult(BaseModel):
    """Resultado de validação."""
    
    valido: bool
    erros: List[str] = []
    avisos: List[str] = []
    total_registros: int = 0
    total_erros: int = 0
    total_avisos: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    def tem_erros(self) -> bool:
        """Verifica se há erros."""
        return len(self.erros) > 0
    
    def tem_avisos(self) -> bool:
        """Verifica se há avisos."""
        return len(self.avisos) > 0
