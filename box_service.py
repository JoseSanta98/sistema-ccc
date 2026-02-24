from box_domain import puede_cerrar_caja, puede_reabrir_caja
from peso_policy import calcular_peso_caja, resolver_peso_cierre, PesoInvalidoError


class BoxService:
    def __init__(self, db_manager, hw_manager):
        self.db = db_manager
        self.hw_mgr = hw_manager

    def cerrar_caja(self, caja_id, canal, contenido, peso_final):
        conn = self.db._get_conn()
        conn.execute("BEGIN IMMEDIATE")

        try:
            caja = conn.execute("SELECT * FROM cajas WHERE id=?", (caja_id,)).fetchone()
            if not caja or caja["estado"] != "ABIERTA":
                conn.rollback()
                raise ValueError("Caja inexistente o no abierta")

            if not contenido:
                conn.rollback()
                raise ValueError("La caja no tiene contenido")

            self.db.cerrar_caja_conn(conn, caja_id)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        try:
            self.hw_mgr.print_master(
                dict(caja),
                canal,
                contenido,
                peso_manual_override=peso_final,
            )
        except Exception as exc:
            self.db.reabrir_caja(caja_id)
            raise RuntimeError("Error de impresión, caja reabierta") from exc

        return True


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
