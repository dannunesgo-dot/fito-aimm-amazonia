"""
Módulo inicial de normalização.
"""
def por_milhao(valor: float, investimento: float) -> float:
    if investimento <= 0:
        raise ValueError("Investimento deve ser maior que zero.")
    return valor / (investimento / 1_000_000)

def percentual(parte: float, total: float) -> float:
    if total == 0:
        return 0.0
    return parte / total
