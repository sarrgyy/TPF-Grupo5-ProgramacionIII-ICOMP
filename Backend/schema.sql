PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS productos (
    id_producto TEXT PRIMARY KEY NOT NULL CHECK (length(trim(id_producto)) > 0),
    nombre TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
    volumen_unitario REAL NOT NULL CHECK (volumen_unitario > 0),
    peso_unitario REAL NOT NULL CHECK (peso_unitario > 0)
);

CREATE TABLE IF NOT EXISTS depositos (
    id_deposito TEXT PRIMARY KEY NOT NULL CHECK (length(trim(id_deposito)) > 0),
    nombre TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
    ubicacion TEXT NOT NULL CHECK (length(trim(ubicacion)) > 0),
    capacidad_maxima REAL NOT NULL CHECK (capacidad_maxima > 0)
);

CREATE TABLE IF NOT EXISTS existencias (
    id_deposito TEXT NOT NULL REFERENCES depositos(id_deposito),
    id_producto TEXT NOT NULL REFERENCES productos(id_producto),
    cantidad INTEGER NOT NULL CHECK (typeof(cantidad) = 'integer' AND cantidad >= 0),
    PRIMARY KEY (id_deposito, id_producto)
);

CREATE INDEX IF NOT EXISTS existencias_producto ON existencias(id_producto);

-- Pedidos: las reservas activas se derivan de los ítems de pedidos Confirmados.
CREATE TABLE IF NOT EXISTS pedidos (
    id_pedido TEXT PRIMARY KEY NOT NULL CHECK (length(trim(id_pedido)) > 0),
    cliente TEXT NOT NULL CHECK (length(trim(cliente)) > 0),
    destino TEXT NOT NULL CHECK (length(trim(destino)) > 0),
    prioridad INTEGER NOT NULL CHECK (typeof(prioridad) = 'integer' AND prioridad BETWEEN 1 AND 3),
    estado TEXT NOT NULL DEFAULT 'Borrador'
        CHECK (estado IN ('Borrador', 'Confirmado', 'Despachado', 'Entregado', 'Cancelado')),
    patente_vehiculo TEXT REFERENCES vehiculos(patente),
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pedido_items (
    id_pedido TEXT NOT NULL REFERENCES pedidos(id_pedido),
    id_deposito TEXT NOT NULL REFERENCES depositos(id_deposito),
    id_producto TEXT NOT NULL REFERENCES productos(id_producto),
    cantidad INTEGER NOT NULL CHECK (typeof(cantidad) = 'integer' AND cantidad > 0),
    PRIMARY KEY (id_pedido, id_deposito, id_producto)
);

CREATE INDEX IF NOT EXISTS pedido_items_stock ON pedido_items(id_deposito, id_producto);

-- Flota: una sola referencia representa la asignación en ambos sentidos.
CREATE TABLE IF NOT EXISTS conductores (
    dni TEXT PRIMARY KEY NOT NULL CHECK (length(trim(dni)) > 0),
    nombre TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
    estado TEXT NOT NULL DEFAULT 'Disponible' CHECK (estado IN ('Disponible', 'Inactivo'))
);

CREATE TABLE IF NOT EXISTS vehiculos (
    patente TEXT PRIMARY KEY NOT NULL CHECK (length(trim(patente)) > 0),
    capacidad_maxima REAL NOT NULL CHECK (capacidad_maxima > 0),
    estado TEXT NOT NULL DEFAULT 'Disponible'
        CHECK (estado IN ('Disponible', 'En Ruta', 'Mantenimiento')),
    dni_conductor TEXT UNIQUE REFERENCES conductores(dni),
    CHECK (estado != 'Mantenimiento' OR dni_conductor IS NULL),
    CHECK (estado != 'En Ruta' OR dni_conductor IS NOT NULL)
);
