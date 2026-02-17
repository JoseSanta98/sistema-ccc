from box_domain import puede_cerrar_caja, puede_reabrir_caja


def cerrar_caja(db, hw_mgr, caja, canal, contenido, peso_final):
    if not puede_cerrar_caja(caja['estado']):
        return False

    hw_mgr.print_master(caja, canal, contenido, peso_manual_override=peso_final)
    db.cerrar_caja(caja['id'])
    return True


def reabrir_caja(db, caja):
    if not puede_reabrir_caja(caja['estado']):
        return False

    db.reabrir_caja(caja['id'])
    return True
