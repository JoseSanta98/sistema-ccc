import sqlite3

from box_domain import ESTADO_ABIERTA, puede_cerrar_caja, puede_reabrir_caja


class BoxService:
    def __init__(self, db_manager, hw_manager):
        self.db = db_manager
        self.hw_mgr = hw_manager

    def cerrar_caja(self, caja_id, canal, contenido, peso_final):
        conn = self.db._get_conn()
        conn.execute("BEGIN IMMEDIATE")
        _committed = False

        try:
            caja = conn.execute("SELECT * FROM cajas WHERE id=?", (caja_id,)).fetchone()
            if not caja or not puede_cerrar_caja(caja["estado"]):
                raise ValueError("La caja no existe o no se puede cerrar")

            if not contenido:
                raise ValueError("La caja no tiene contenido")

            ok_print, _msg_print = self.hw_mgr.print_master(
                dict(caja),
                canal,
                contenido,
                peso_manual_override=peso_final,
            )

            if not ok_print:
                raise RuntimeError("Error de impresión. La caja no fue cerrada.")

            self.db.cerrar_caja_conn(conn, caja_id)
            conn.commit()
            _committed = True
        except Exception:
            if not _committed:
                conn.rollback()
            raise
        finally:
            conn.close()

        return True

    def crear_o_recuperar_caja(self, canal_id, numero_caja):
        conn = self.db._get_conn()
        conn.execute("BEGIN IMMEDIATE")

        try:
            existe = conn.execute(
                f"SELECT id FROM cajas WHERE canal_id=? AND numero_caja=? AND estado='{ESTADO_ABIERTA}'",
                (canal_id, numero_caja),
            ).fetchone()
            if existe:
                conn.commit()
                return existe["id"]

            cursor = conn.execute(
                "INSERT INTO cajas (canal_id, numero_caja) VALUES (?, ?)",
                (canal_id, numero_caja),
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            conn.rollback()
            recuperada = conn.execute(
                f"SELECT id FROM cajas WHERE canal_id=? AND numero_caja=? AND estado='{ESTADO_ABIERTA}'",
                (canal_id, numero_caja),
            ).fetchone()
            if recuperada:
                return recuperada["id"]
            raise
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def reabrir_caja(self, caja):
        if not puede_reabrir_caja(caja['estado']):
            raise ValueError("La caja no puede reabrirse en su estado actual.")
        conn = self.db._get_conn()
        try:
            conn.execute("BEGIN IMMEDIATE")
            self.db.reabrir_caja_conn(conn, caja['id'])
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
