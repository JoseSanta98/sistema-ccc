# db_manager.py
import sqlite3
import os
from datetime import datetime

DB_FILE = "produccion_local.db"
SCHEMA_FILE = "schema.sql"
MIGRATIONS_DIR = os.path.join("tools", "migrations")
PRODUCTOS_ESTADO_MIGRATION = "001_add_estado_to_productos.sql"
PIEZAS_CODIGO_INDEX_MIGRATION = "002_add_index_piezas_codigo_producto.sql"

class DatabaseManager:
    def __init__(self):
        self._ensure_db_exists()
        self._run_pending_migrations()

    def _get_conn(self):
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _ensure_db_exists(self):
        if not os.path.exists(DB_FILE):
            print("⚠️ Base de datos no encontrada. Inicializando nueva estructura...")
            self._init_schema()

    def _init_schema(self):
        if os.path.exists(SCHEMA_FILE):
            with open(SCHEMA_FILE, 'r') as f:
                script = f.read()
            conn = self._get_conn()
            conn.executescript(script)
            conn.close()
            print("✅ Estructura de base de datos creada exitosamente.")
        else:
            print("❌ Error: No se encuentra schema.sql")

    def _run_pending_migrations(self):
        conn = self._get_conn()
        try:
            self._run_productos_estado_migration(conn)
            self._run_piezas_codigo_index_migration(conn)
        finally:
            conn.close()

    def _run_productos_estado_migration(self, conn):
        if not self._table_exists(conn, "productos"):
            return

        if self._column_exists(conn, "productos", "estado"):
            return

        migration_path = os.path.join(MIGRATIONS_DIR, PRODUCTOS_ESTADO_MIGRATION)
        if not os.path.exists(migration_path):
            print(f"❌ Error: No se encuentra migración {migration_path}")
            return

        with open(migration_path, "r", encoding="utf-8") as f:
            script = f.read()

        conn.executescript(script)
        conn.commit()
        print("✅ Migración aplicada: productos.estado agregado con valor por defecto ACTIVO.")

    def _run_piezas_codigo_index_migration(self, conn):
        if not self._table_exists(conn, "piezas"):
            return

        if self._index_exists(conn, "piezas", "idx_piezas_codigo_producto"):
            return

        migration_path = os.path.join(MIGRATIONS_DIR, PIEZAS_CODIGO_INDEX_MIGRATION)
        if not os.path.exists(migration_path):
            print(f"❌ Error: No se encuentra migración {migration_path}")
            return

        with open(migration_path, "r", encoding="utf-8") as f:
            script = f.read()

        conn.executescript(script)
        conn.commit()
        print("✅ Migración aplicada: índice idx_piezas_codigo_producto creado.")

    def _table_exists(self, conn, table_name):
        row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone()
        return row is not None

    def _column_exists(self, conn, table_name, column_name):
        rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        return any(row[1] == column_name for row in rows)

    def _index_exists(self, conn, table_name, index_name):
        rows = conn.execute(f"PRAGMA index_list('{table_name}')").fetchall()
        return any(row[1] == index_name for row in rows)

    # --- 1. PRODUCTOS ---
    def get_producto(self, codigo):
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM productos WHERE codigo=?", (codigo.strip(),)).fetchone()
        conn.close()
        return dict(row) if row else None

    def get_all_productos(self):
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM productos ORDER BY codigo ASC").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def upsert_producto(self, codigo, nombre, especie):
        conn = self._get_conn()
        conn.execute("""
            INSERT INTO productos (codigo, nombre, especie) VALUES (?, ?, ?)
            ON CONFLICT(codigo) DO UPDATE SET nombre=excluded.nombre, especie=excluded.especie
        """, (codigo.strip(), nombre.strip(), especie.strip()))
        conn.commit()
        conn.close()

    def delete_producto(self, codigo):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM productos WHERE codigo=?", (codigo.strip(),))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    # --- 2. CANALES ---
    def get_canales_activos(self):
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM canales WHERE estado='ACTIVO' ORDER BY id DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_all_canales(self, incluir_cerrados=False):
        conn = self._get_conn()
        if incluir_cerrados:
            query = "SELECT * FROM canales ORDER BY id DESC"
        else:
            query = "SELECT * FROM canales WHERE estado='ACTIVO' ORDER BY id DESC"
        rows = conn.execute(query).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_canal_by_id(self, canal_id):
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM canales WHERE id=?", (canal_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def buscar_o_crear_canal(self, siniiga_parcial):
        conn = self._get_conn()
        cursor = conn.cursor()
        siniiga_full = siniiga_parcial.strip()
        if "-" not in siniiga_full:
            if len(siniiga_full) <= 8 and not siniiga_full.startswith("08"):
                siniiga_full = "08" + siniiga_full.zfill(8)

        cursor.execute("SELECT * FROM canales WHERE siniiga = ? AND estado='ACTIVO'", (siniiga_full,))
        existe = cursor.fetchone()
        if existe:
            conn.close()
            return dict(existe)
        
        lote_hoy = datetime.now().strftime("%d%m%y")
        try:
            cursor.execute("INSERT INTO canales (siniiga, lote_dia) VALUES (?, ?)", (siniiga_full, lote_hoy))
            conn.commit()
            cursor.execute("SELECT * FROM canales WHERE id=?", (cursor.lastrowid,))
            nuevo = cursor.fetchone()
            conn.close()
            return dict(nuevo)
        except sqlite3.IntegrityError:
            conn.rollback()
            cursor.execute("SELECT * FROM canales WHERE siniiga=?", (siniiga_full,))
            recuperado = cursor.fetchone()
            conn.close()
            return dict(recuperado) if recuperado else None

    def cerrar_canal(self, canal_id):
        conn = self._get_conn()
        conn.execute("UPDATE canales SET estado='CERRADO' WHERE id=?", (canal_id,))
        conn.commit()
        conn.close()

    def reabrir_canal(self, canal_id):
        conn = self._get_conn()
        conn.execute("UPDATE canales SET estado='ACTIVO' WHERE id=?", (canal_id,))
        conn.commit()
        conn.close()

    def get_resumen_canal(self, canal_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT c.id) as total_cajas,
                COALESCE(SUM(p.peso), 0) as peso_total
            FROM cajas c
            LEFT JOIN piezas p ON p.caja_id = c.id
            WHERE c.canal_id = ?
        """, (canal_id,))
        row = cursor.fetchone()
        conn.close()
        return {'total_cajas': row[0] or 0, 'peso_total': row[1] or 0.0}

    # --- 3. CAJAS ---
    def get_max_numero_caja(self, canal_id):
        conn = self._get_conn()
        row = conn.execute("SELECT MAX(numero_caja) FROM cajas WHERE canal_id=?", (canal_id,)).fetchone()
        conn.close()
        return row[0] if row and row[0] else 0

    def get_cajas_abiertas(self, canal_id):
        conn = self._get_conn()
        query = """
        SELECT c.*, COALESCE(SUM(p.peso), 0) as peso_acumulado
        FROM cajas c
        LEFT JOIN piezas p ON p.caja_id = c.id
        WHERE c.canal_id = ? AND c.estado = 'ABIERTA'
        GROUP BY c.id ORDER BY c.numero_caja ASC
        """
        rows = conn.execute(query, (canal_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_all_cajas_canal(self, canal_id, incluir_cerradas=True):
        conn = self._get_conn()
        st_filter = "" if incluir_cerradas else "AND c.estado='ABIERTA'"
        query = f"""
        SELECT c.*, COUNT(p.id) as num_piezas, COALESCE(SUM(p.peso), 0) as peso_acumulado
        FROM cajas c
        LEFT JOIN piezas p ON p.caja_id = c.id
        WHERE c.canal_id = ? {st_filter}
        GROUP BY c.id ORDER BY c.numero_caja ASC
        """
        rows = conn.execute(query, (canal_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_caja_by_id(self, caja_id):
        conn = self._get_conn()
        query = """
        SELECT c.*, COALESCE(SUM(p.peso), 0) as peso_acumulado, COUNT(p.id) as num_piezas
        FROM cajas c
        LEFT JOIN piezas p ON p.caja_id = c.id
        WHERE c.id = ? GROUP BY c.id
        """
        row = conn.execute(query, (caja_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def crear_o_recuperar_caja(self, canal_id, numero_caja):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM cajas WHERE canal_id=? AND numero_caja=? AND estado='ABIERTA'", (canal_id, numero_caja))
        existe = cursor.fetchone()
        if existe:
            conn.close()
            return existe['id']
        cursor.execute("INSERT INTO cajas (canal_id, numero_caja) VALUES (?, ?)", (canal_id, numero_caja))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return new_id

    def cerrar_caja(self, caja_id):
        conn = self._get_conn()
        conn.execute("UPDATE cajas SET estado='CERRADA', fecha_cierre=CURRENT_TIMESTAMP WHERE id=?", (caja_id,))
        conn.commit()
        conn.close()

    def reabrir_caja(self, caja_id):
        conn = self._get_conn()
        conn.execute("UPDATE cajas SET estado='ABIERTA', fecha_cierre=NULL WHERE id=?", (caja_id,))
        conn.commit()
        conn.close()

    def eliminar_caja(self, caja_id):
        conn = self._get_conn()
        conn.execute("DELETE FROM piezas WHERE caja_id=?", (caja_id,))
        conn.execute("DELETE FROM cajas WHERE id=?", (caja_id,))
        conn.commit()
        conn.close()

    # --- 4. PIEZAS ---
    def registrar_pieza(self, caja_id, codigo, nombre, peso):
        conn = self._get_conn()
        try:
            conn.execute("BEGIN IMMEDIATE")
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(consecutivo) FROM piezas WHERE caja_id=?", (caja_id,))
            res = cursor.fetchone()[0]
            sig = (res + 1) if res else 1
            cursor.execute("""
                INSERT INTO piezas (caja_id, codigo_producto, nombre_producto, peso, consecutivo)
                VALUES (?, ?, ?, ?, ?)
            """, (caja_id, codigo, nombre, peso, sig))
            new_id = cursor.lastrowid
            conn.commit()
            return sig, new_id
        except:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_contenido_caja(self, caja_id):
        conn = self._get_conn()
        rows = conn.execute("SELECT *, time(fecha_registro, 'localtime') as hora FROM piezas WHERE caja_id=? ORDER BY id DESC", (caja_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_pieza_by_id(self, pieza_id):
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM piezas WHERE id=?", (pieza_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def editar_pieza(self, pieza_id, nuevo_peso):
        conn = self._get_conn()
        try:
            conn.execute("BEGIN IMMEDIATE")
            cursor = conn.cursor()

            cursor.execute("SELECT caja_id, peso FROM piezas WHERE id=?", (pieza_id,))
            pieza = cursor.fetchone()
            if not pieza:
                raise ValueError("Pieza no existe")

            caja_id = pieza['caja_id']
            cursor.execute("UPDATE piezas SET peso=? WHERE id=?", (nuevo_peso, pieza_id))

            cursor.execute(
                "SELECT COALESCE(SUM(peso), 0) as peso_total, COUNT(*) as total_piezas FROM piezas WHERE caja_id=?",
                (caja_id,)
            )
            resumen = cursor.fetchone()
            peso_total = float(resumen['peso_total']) if resumen else 0.0
            total_piezas = int(resumen['total_piezas']) if resumen else 0

            caja_cols = {r['name'] for r in conn.execute("PRAGMA table_info(cajas)").fetchall()}
            if 'peso_acumulado' in caja_cols and 'num_piezas' in caja_cols:
                cursor.execute(
                    "UPDATE cajas SET peso_acumulado=?, num_piezas=? WHERE id=?",
                    (peso_total, total_piezas, caja_id)
                )
            elif 'peso_acumulado' in caja_cols:
                cursor.execute("UPDATE cajas SET peso_acumulado=? WHERE id=?", (peso_total, caja_id))
            elif 'num_piezas' in caja_cols:
                cursor.execute("UPDATE cajas SET num_piezas=? WHERE id=?", (total_piezas, caja_id))

            conn.commit()
            return True
        except:
            conn.rollback()
            raise
        finally:
            conn.close()

    def borrar_pieza(self, pieza_id):
        conn = self._get_conn()
        try:
            conn.execute("BEGIN IMMEDIATE")
            cursor = conn.cursor()

            cursor.execute("SELECT caja_id FROM piezas WHERE id=?", (pieza_id,))
            pieza = cursor.fetchone()
            if not pieza:
                raise ValueError("Pieza no existe")

            caja_id = pieza['caja_id']
            cursor.execute("DELETE FROM piezas WHERE id=?", (pieza_id,))

            cursor.execute(
                "SELECT COALESCE(SUM(peso), 0) as peso_total, COUNT(*) as total_piezas FROM piezas WHERE caja_id=?",
                (caja_id,)
            )
            resumen = cursor.fetchone()
            peso_total = float(resumen['peso_total']) if resumen else 0.0
            total_piezas = int(resumen['total_piezas']) if resumen else 0

            caja_cols = {r['name'] for r in conn.execute("PRAGMA table_info(cajas)").fetchall()}
            if 'peso_acumulado' in caja_cols and 'num_piezas' in caja_cols:
                cursor.execute(
                    "UPDATE cajas SET peso_acumulado=?, num_piezas=? WHERE id=?",
                    (peso_total, total_piezas, caja_id)
                )
            elif 'peso_acumulado' in caja_cols:
                cursor.execute("UPDATE cajas SET peso_acumulado=? WHERE id=?", (peso_total, caja_id))
            elif 'num_piezas' in caja_cols:
                cursor.execute("UPDATE cajas SET num_piezas=? WHERE id=?", (total_piezas, caja_id))

            conn.commit()
            return True
        except:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_estadisticas_generales(self):
        conn = self._get_conn()
        row_hoy = conn.execute("""
            SELECT COUNT(*), COALESCE(SUM(p.peso), 0) 
            FROM piezas p WHERE date(p.fecha_registro) = date('now', 'localtime')
        """).fetchone()
        conn.close()
        return {'piezas_hoy': row_hoy[0], 'peso_hoy': row_hoy[1]}
