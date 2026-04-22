import sqlite3

from box_domain import ESTADO_ABIERTA, puede_agregar_pieza
from peso_policy import PesoConfig


class PieceService:
    def __init__(self, db_manager, product_service):
        self.db = db_manager
        self.product_service = product_service

    def registrar_pieza(self, caja_id, codigo_producto, peso):
        conn = self.db._get_conn()
        try:
            conn.execute("BEGIN IMMEDIATE")

            caja = conn.execute("SELECT * FROM cajas WHERE id=?", (caja_id,)).fetchone()
            if not caja:
                raise ValueError("Caja no existe")

            if not puede_agregar_pieza(caja["estado"]):
                raise ValueError("El estado de la caja no permite esta operación")

            if peso < PesoConfig.MIN_PIEZA:
                raise ValueError(f"El peso debe ser al menos {PesoConfig.MIN_PIEZA}")

            if not codigo_producto:
                raise ValueError("El código no puede estar vacío")

            producto = self.product_service.get_producto_activo(codigo_producto)
            if producto is None:
                raise ValueError("Producto inexistente o INACTIVO")

            nombre_producto = producto["nombre"]

            consecutivo, pieza_id = self.db.registrar_pieza_conn(
                conn, caja_id, codigo_producto, nombre_producto, peso
            )
            conn.commit()
            return consecutivo, pieza_id

        except sqlite3.IntegrityError as e:
            conn.rollback()
            if "UNIQUE constraint failed: piezas.caja_id, piezas.consecutivo" in str(e):
                raise ValueError("Conflicto de consecutivo en la caja") from e
            raise ValueError("Error de integridad al registrar pieza") from e
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def editar_pieza(self, pieza_id, nuevo_peso):
        if nuevo_peso < PesoConfig.MIN_PIEZA:
            raise ValueError(f"El peso debe ser al menos {PesoConfig.MIN_PIEZA}")

        conn = self.db._get_conn()
        try:
            conn.execute("BEGIN IMMEDIATE")

            pieza = conn.execute("SELECT caja_id FROM piezas WHERE id=?", (pieza_id,)).fetchone()
            if not pieza:
                raise ValueError("Pieza no existe")

            caja = conn.execute("SELECT estado FROM cajas WHERE id=?", (pieza["caja_id"],)).fetchone()
            if not caja or not puede_agregar_pieza(caja["estado"]):
                raise ValueError("El estado de la caja no permite esta operación")

            self.db.editar_pieza_conn(conn, pieza_id, nuevo_peso)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def borrar_pieza(self, pieza_id):
        conn = self.db._get_conn()
        try:
            conn.execute("BEGIN IMMEDIATE")

            pieza = conn.execute("SELECT caja_id FROM piezas WHERE id=?", (pieza_id,)).fetchone()
            if not pieza:
                raise ValueError("Pieza no existe")

            caja = conn.execute("SELECT estado FROM cajas WHERE id=?", (pieza["caja_id"],)).fetchone()
            if not caja or not puede_agregar_pieza(caja["estado"]):
                raise ValueError("El estado de la caja no permite esta operación")

            self.db.borrar_pieza_conn(conn, pieza_id)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
