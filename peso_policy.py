class PesoInvalidoError(Exception):
    pass

class PesoConfig:
    CORRECCION_BASCULA = -0.02
    MIN_PIEZA = 0.01
    MIN_CIERRE = 0.10
    MAX_CIERRE = 100.00
    DECIMALES = 2
    TOLERANCIA_CIERRE = 0.05

def _redondear(valor: float) -> float:
    return round(valor, PesoConfig.DECIMALES)

def calcular_peso_pieza(raw: float, aplicar_correccion: bool) -> float:
    if raw <= 0:
        raise PesoInvalidoError(f"Peso de pieza inválido: {raw}")

    peso = raw

    if aplicar_correccion:
        candidato = raw + PesoConfig.CORRECCION_BASCULA
        if candidato > 0:
            peso = candidato

    peso = _redondear(peso)

    if peso < PesoConfig.MIN_PIEZA:
        raise PesoInvalidoError(f"Peso de pieza por debajo del mínimo: {peso}")

    return peso

def calcular_peso_caja(piezas: list[dict]) -> float:
    total = sum(p.get("peso", 0) for p in piezas)
    return _redondear(total)

def resolver_peso_cierre(peso_calculado: float, peso_override: float | None):
    if peso_override is not None:
        if peso_override <= 0:
            raise PesoInvalidoError(f"Override de cierre inválido: {peso_override}")

        if not (PesoConfig.MIN_CIERRE <= peso_override <= PesoConfig.MAX_CIERRE):
            raise PesoInvalidoError(f"Override de cierre fuera de rango: {peso_override}")

        peso_final = _redondear(peso_override)
    else:
        peso_final = _redondear(peso_calculado)

    delta = peso_final - _redondear(peso_calculado)
    hay_diferencia = abs(delta) > PesoConfig.TOLERANCIA_CIERRE

    return {
        "peso_final": peso_final,
        "delta": delta,
        "hay_diferencia": hay_diferencia,
    }
