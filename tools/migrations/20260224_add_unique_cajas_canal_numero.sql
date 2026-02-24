PRAGMA foreign_keys=OFF;

CREATE TABLE cajas_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canal_id INTEGER NOT NULL,
    numero_caja INTEGER NOT NULL,
    peso_tara REAL DEFAULT 0.0,
    fecha_apertura DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_cierre DATETIME,
    estado TEXT DEFAULT 'ABIERTA',

    FOREIGN KEY (canal_id)
        REFERENCES canales(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    UNIQUE (canal_id, numero_caja)
);

INSERT INTO cajas_new
SELECT * FROM cajas;

DROP TABLE cajas;

ALTER TABLE cajas_new RENAME TO cajas;

PRAGMA foreign_keys=ON;
