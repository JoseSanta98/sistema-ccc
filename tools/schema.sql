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
    numero_caja INTEGER NOT NULL,  -- El numero fisico escrito con marcador
    peso_tara REAL DEFAULT 0.0,
    fecha_apertura DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_cierre DATETIME,
    estado TEXT DEFAULT 'ABIERTA', -- 'ABIERTA', 'CERRADA'
    
    -- Si se borra el canal, se borran las cajas
    FOREIGN KEY (canal_id) REFERENCES canales(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 4. PIEZAS (Registros de pesaje)
-- El contenido real. Se relacionan con una CAJA.
CREATE TABLE IF NOT EXISTS piezas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caja_id INTEGER NOT NULL,
    codigo_producto TEXT NOT NULL,
    nombre_producto TEXT,          -- Snapshot del nombre (por si cambia el catalogo despues)
    peso REAL NOT NULL,
    consecutivo INTEGER NOT NULL,  -- Pieza 1, 2, 3... de ESTA caja
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Si se borra la caja, se borran las piezas
    FOREIGN KEY (caja_id) REFERENCES cajas(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Indices para busquedas rapidas
CREATE INDEX IF NOT EXISTS idx_canal_estado ON canales(estado);
CREATE INDEX IF NOT EXISTS idx_caja_activa ON cajas(canal_id, estado);
CREATE INDEX IF NOT EXISTS idx_contenido_caja ON piezas(caja_id);