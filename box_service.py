import sqlite3

from box_domain import puede_reabrir_caja


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
            if not caja or caja["estado"] != "ABIERTA":
                raise ValueError("Caja inexistente o no abierta")

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
                "SELECT id FROM cajas WHERE canal_id=? AND numero_caja=? AND estado='ABIERTA'",
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
                "SELECT id FROM cajas WHERE canal_id=? AND numero_caja=? AND estado='ABIERTA'",
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
