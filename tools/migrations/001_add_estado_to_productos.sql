-- MIGRACION CONTROLADA: agregar columna estado a productos
-- Idempotencia: la verificación de existencia de columna se realiza en DatabaseManager
ALTER TABLE productos ADD COLUMN estado TEXT NOT NULL DEFAULT 'ACTIVO';
