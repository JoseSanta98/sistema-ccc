from box_domain import puede_cerrar_caja, puede_reabrir_caja
from peso_policy import calcular_peso_caja, resolver_peso_cierre, PesoInvalidoError


def cerrar_caja(db, hw_mgr, caja, canal, contenido, peso_final):
    if not puede_cerrar_caja(caja['estado']):
        return False

    peso_calculado = calcular_peso_caja(contenido)

    try:
        resultado = resolver_peso_cierre(peso_calculado, peso_final)
    except PesoInvalidoError:
        raise

    peso_final_validado = resultado["peso_final"]

    hw_mgr.print_master(
        caja,
        canal,
        contenido,
        peso_manual_override=peso_final_validado
    )

    db.cerrar_caja(caja['id'])
    return True


def reabrir_caja(db, caja):
    if not puede_reabrir_caja(caja['estado']):
        return False

    db.reabrir_caja(caja['id'])
    return True
