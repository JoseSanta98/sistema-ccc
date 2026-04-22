from box_domain import ESTADO_ABIERTA
from peso_policy import PesoConfig


class PieceService:
    def __init__(self, db_manager, product_service):
        self.db = db_manager
        self.product_service = product_service

    def registrar_pieza(self, caja_id, codigo_producto, peso):
        caja = self.db.get_caja_by_id(caja_id)
        if not caja:
            raise ValueError("Caja no existe")

        if caja["estado"] != ESTADO_ABIERTA:
            raise ValueError("La caja no está abierta")

        if peso < PesoConfig.MIN_PIEZA:
            raise ValueError(f"El peso debe ser al menos {PesoConfig.MIN_PIEZA}")

        if not codigo_producto:
            raise ValueError("El código no puede estar vacío")

        producto = self.product_service.get_producto_activo(codigo_producto)
        if producto is None:
            raise ValueError("Producto inexistente o INACTIVO")

        nombre_producto = producto["nombre"]

        return self.db.registrar_pieza(caja_id, codigo_producto, nombre_producto, peso)

    def editar_pieza(self, pieza_id, nuevo_peso):
        pieza = self.db.get_pieza_by_id(pieza_id)
        if not pieza:
            raise ValueError("Pieza no existe")

        caja = self.db.get_caja_by_id(pieza["caja_id"])
        if caja["estado"] != ESTADO_ABIERTA:
            raise ValueError("La caja no está abierta")

        if nuevo_peso < PesoConfig.MIN_PIEZA:
            raise ValueError(f"El peso debe ser al menos {PesoConfig.MIN_PIEZA}")

        return self.db.editar_pieza(pieza_id, nuevo_peso)

    def borrar_pieza(self, pieza_id):
        pieza = self.db.get_pieza_by_id(pieza_id)
        if not pieza:
            raise ValueError("Pieza no existe")

        caja = self.db.get_caja_by_id(pieza["caja_id"])
        if caja["estado"] != ESTADO_ABIERTA:
            raise ValueError("La caja no está abierta")

        return self.db.borrar_pieza(pieza_id)
