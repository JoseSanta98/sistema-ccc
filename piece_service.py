from box_domain import ESTADO_ABIERTA

class PieceService:
    def __init__(self, db_manager):
        self.db = db_manager

    def registrar_pieza(self, caja_id, codigo, nombre, peso):
        caja = self.db.get_caja_by_id(caja_id)
        if not caja:
            raise ValueError("Caja no existe")

        if caja['estado'] != ESTADO_ABIERTA:
            raise ValueError("La caja no está abierta")

        if peso <= 0:
            raise ValueError("El peso debe ser mayor a 0")

        if not codigo:
            raise ValueError("El código no puede estar vacío")

        if not nombre:
            raise ValueError("El nombre no puede estar vacío")

        return self.db.registrar_pieza(caja_id, codigo, nombre, peso)

    def editar_pieza(self, pieza_id, nuevo_peso):
        pieza = self.db.get_pieza_by_id(pieza_id)
        if not pieza:
            raise ValueError("Pieza no existe")

        caja = self.db.get_caja_by_id(pieza['caja_id'])
        if caja['estado'] != ESTADO_ABIERTA:
            raise ValueError("La caja no está abierta")

        if nuevo_peso <= 0:
            raise ValueError("El peso debe ser mayor a 0")

        return self.db.editar_pieza(pieza_id, nuevo_peso)

    def borrar_pieza(self, pieza_id):
        pieza = self.db.get_pieza_by_id(pieza_id)
        if not pieza:
            raise ValueError("Pieza no existe")

        caja = self.db.get_caja_by_id(pieza['caja_id'])
        if caja['estado'] != ESTADO_ABIERTA:
            raise ValueError("La caja no está abierta")

        return self.db.borrar_pieza(pieza_id)
