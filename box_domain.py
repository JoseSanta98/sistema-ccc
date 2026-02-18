ESTADO_ABIERTA = "ABIERTA"
ESTADO_CERRADA = "CERRADA"


def puede_agregar_pieza(estado_caja):
    return estado_caja == ESTADO_ABIERTA


def puede_cerrar_caja(estado_caja):
    return estado_caja == ESTADO_ABIERTA


def puede_reabrir_caja(estado_caja):
    return estado_caja == ESTADO_CERRADA
