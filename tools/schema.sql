-- schema.sql
PRAGMA foreign_keys = ON;

-- 1. CATALOGO DE PRODUCTOS
CREATE TABLE IF NOT EXISTS productos (
    codigo TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    especie TEXT NOT NULL
);

-- 2. CANALES (SINIIGAS)
-- Representa al animal/propietario.
CREATE TABLE IF NOT EXISTS canales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    siniiga TEXT NOT NULL UNIQUE,  -- El numero de arete (08XXXXXXXX)
    lote_dia TEXT NOT NULL,        -- Fecha DDMMYY
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    estado TEXT DEFAULT 'ACTIVO'   -- 'ACTIVO' para mostrar en pantalla, 'CERRADO' para ocultar
);

-- 3. CAJAS
-- Contenedores fisicos. Se relacionan con un CANAL.
CREATE TABLE IF NOT EXISTS cajas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canal_id INTEGER NOT NULL,
    numero_caja INTEGER NOT NULL,
    peso_tara REAL DEFAULT 0.0,
    fecha_apertura DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_cierre DATETIME,
    estado TEXT NOT NULL DEFAULT 'ABIERTA',
    
    FOREIGN KEY (canal_id) REFERENCES canales(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
        
    CHECK (estado IN ('ABIERTA','CERRADA')),
    UNIQUE (canal_id, numero_caja)
);

-- 4. PIEZAS (Registros de pesaje)
-- El contenido real. Se relacionan con una CAJA.
CREATE TABLE IF NOT EXISTS piezas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caja_id INTEGER NOT NULL,
    codigo_producto TEXT NOT NULL,
    nombre_producto TEXT NOT NULL,
    peso REAL NOT NULL CHECK (peso > 0),
    consecutivo INTEGER NOT NULL,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (caja_id) REFERENCES cajas(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
        
    UNIQUE (caja_id, consecutivo)
);

-- Indices para busquedas rapidas
CREATE INDEX IF NOT EXISTS idx_canal_estado ON canales(estado);
