class ProductService:
    def __init__(self, db_manager):
        self.db = db_manager

    # --- API NUEVA SOLICITADA ---
    def get_producto(self, codigo):
        codigo_limpio = self._validar_codigo(codigo)
        conn = self.db._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM productos WHERE codigo=?", (codigo_limpio,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_producto_activo(self, codigo):
        codigo_limpio = self._validar_codigo(codigo)
        conn = self.db._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM productos WHERE codigo=? AND estado='ACTIVO'",
                (codigo_limpio,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_all_productos(self, incluir_inactivos=False):
        conn = self.db._get_conn()
        try:
            if incluir_inactivos:
                rows = conn.execute("SELECT * FROM productos ORDER BY codigo ASC").fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM productos WHERE estado='ACTIVO' ORDER BY codigo ASC"
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def upsert_producto(self, codigo, nombre, especie):
        codigo_limpio = self._validar_codigo(codigo)
        nombre_limpio = self._validar_texto(nombre, "nombre")
        especie_limpia = self._validar_texto(especie, "especie")

        conn = self.db._get_conn()
        try:
            conn.execute(
                """
                INSERT INTO productos (codigo, nombre, especie, estado)
                VALUES (?, ?, ?, 'ACTIVO')
                ON CONFLICT(codigo) DO UPDATE SET
                    nombre=excluded.nombre,
                    especie=excluded.especie
                """,
                (codigo_limpio, nombre_limpio, especie_limpia),
            )
            conn.commit()
        finally:
            conn.close()

    def desactivar_producto(self, codigo):
        self._set_estado(codigo, "INACTIVO")

    def activar_producto(self, codigo):
        self._set_estado(codigo, "ACTIVO")

    # --- COMPATIBILIDAD CON CÓDIGO ACTUAL ---
    def list_all(self, include_inactive=True):
        return self.get_all_productos(incluir_inactivos=include_inactive)

    def get(self, codigo):
        return self.get_producto(codigo)

    def create(self, codigo, nombre, especie):
        codigo_limpio = self._validar_codigo(codigo)
        nombre_limpio = self._validar_texto(nombre, "nombre")
        especie_limpia = self._validar_texto(especie, "especie")

        conn = self.db._get_conn()
        try:
            conn.execute("BEGIN IMMEDIATE")

            if self._existe_producto_conn(conn, codigo_limpio):
                raise ValueError(f"El producto '{codigo_limpio}' ya existe")

            conn.execute(
                "INSERT INTO productos (codigo, nombre, especie, estado) VALUES (?, ?, ?, 'ACTIVO')",
                (codigo_limpio, nombre_limpio, especie_limpia),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def update(self, codigo_original, nuevo_nombre, nueva_especie):
        codigo_limpio = self._validar_codigo(codigo_original)
        nombre_limpio = self._validar_texto(nuevo_nombre, "nombre")
        especie_limpia = self._validar_texto(nueva_especie, "especie")

        conn = self.db._get_conn()
        try:
            conn.execute("BEGIN IMMEDIATE")

            if not self._existe_producto_conn(conn, codigo_limpio):
                raise ValueError(f"El producto '{codigo_limpio}' no existe")

            conn.execute(
                "UPDATE productos SET nombre=?, especie=? WHERE codigo=?",
                (nombre_limpio, especie_limpia, codigo_limpio),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def change_codigo(self, codigo_original, nuevo_codigo):
        codigo_original_limpio = self._validar_codigo(codigo_original)
        nuevo_codigo_limpio = self._validar_codigo(nuevo_codigo)

        conn = self.db._get_conn()
        try:
            conn.execute("BEGIN IMMEDIATE")

            if not self._existe_producto_conn(conn, codigo_original_limpio):
                raise ValueError(f"El producto '{codigo_original_limpio}' no existe")

            if codigo_original_limpio != nuevo_codigo_limpio and self._existe_producto_conn(conn, nuevo_codigo_limpio):
                raise ValueError(f"El código '{nuevo_codigo_limpio}' ya existe")

            piezas_count = self._count_piezas_por_codigo_conn(conn, codigo_original_limpio)
            if piezas_count > 0:
                raise ValueError(
                    f"No se puede cambiar el código del producto '{codigo_original_limpio}' porque tiene piezas registradas"
                )

            conn.execute(
                "UPDATE productos SET codigo=? WHERE codigo=?",
                (nuevo_codigo_limpio, codigo_original_limpio),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def deactivate(self, codigo):
        self.desactivar_producto(codigo)

    def reactivate(self, codigo):
        self.activar_producto(codigo)

    def delete_if_unused(self, codigo):
        codigo_limpio = self._validar_codigo(codigo)

        conn = self.db._get_conn()
        try:
            conn.execute("BEGIN IMMEDIATE")

            if not self._existe_producto_conn(conn, codigo_limpio):
                raise ValueError(f"El producto '{codigo_limpio}' no existe")

            piezas_count = self._count_piezas_por_codigo_conn(conn, codigo_limpio)
            if piezas_count > 0:
                raise ValueError(
                    f"No se puede eliminar el producto '{codigo_limpio}' porque tiene piezas registradas"
                )

            conn.execute("DELETE FROM productos WHERE codigo=?", (codigo_limpio,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _set_estado(self, codigo, estado_objetivo):
        codigo_limpio = self._validar_codigo(codigo)

        conn = self.db._get_conn()
        try:
            conn.execute("UPDATE productos SET estado=? WHERE codigo=?", (estado_objetivo, codigo_limpio))
            conn.commit()
        finally:
            conn.close()

    def _count_piezas_por_codigo_conn(self, conn, codigo):
        row = conn.execute(
            "SELECT COUNT(*) FROM piezas WHERE codigo_producto = ?", (codigo,)
        ).fetchone()
        return row[0] if row else 0

    def _existe_producto_conn(self, conn, codigo):
        row = conn.execute("SELECT 1 FROM productos WHERE codigo=?", (codigo,)).fetchone()
        return row is not None

    def _validar_codigo(self, codigo):
        if codigo is None:
            raise ValueError("El código no puede estar vacío")

        codigo_limpio = str(codigo).strip()
        if not codigo_limpio:
            raise ValueError("El código no puede estar vacío")

        return codigo_limpio

    def _validar_texto(self, valor, campo):
        if valor is None:
            raise ValueError(f"El {campo} no puede estar vacío")

        valor_limpio = str(valor).strip()
        if not valor_limpio:
            raise ValueError(f"El {campo} no puede estar vacío")

        return valor_limpio
