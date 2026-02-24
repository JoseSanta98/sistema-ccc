PRAGMA foreign_keys=OFF;

CREATE TABLE piezas_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caja_id INTEGER NOT NULL,
    codigo_producto TEXT NOT NULL,
    nombre_producto TEXT,
    peso REAL NOT NULL,
    consecutivo INTEGER NOT NULL,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (caja_id)
        REFERENCES cajas(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    FOREIGN KEY (codigo_producto)
        REFERENCES productos(codigo)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    UNIQUE (caja_id, consecutivo)
);

INSERT INTO piezas_new
SELECT * FROM piezas;

DROP TABLE piezas;

ALTER TABLE piezas_new RENAME TO piezas;

PRAGMA foreign_keys=ON;
