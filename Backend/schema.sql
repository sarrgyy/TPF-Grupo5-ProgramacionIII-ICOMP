-- El esquema se aplica al abrir InventarioSQLite, sin reemplazar las tablas.
-- La columna histórica y el índice de vehículo activo se migran en Python.
PRAGMA foreign_keys = ON;

-- El catálogo describe una unidad; el stock pertenece a existencias.
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

-- Una fila por producto y depósito evita duplicar las existencias físicas.
CREATE TABLE IF NOT EXISTS existencias (
    id_deposito TEXT NOT NULL REFERENCES depositos(id_deposito),
    id_producto TEXT NOT NULL REFERENCES productos(id_producto),
    cantidad INTEGER NOT NULL CHECK (typeof(cantidad) = 'integer' AND cantidad >= 0),
    PRIMARY KEY (id_deposito, id_producto)
);

CREATE INDEX IF NOT EXISTS existencias_producto ON existencias(id_producto);

-- Una clave de operación permite reintentar un ingreso HTTP sin duplicarlo.
CREATE TABLE IF NOT EXISTS ingresos_stock (
    clave TEXT PRIMARY KEY NOT NULL,
    id_deposito TEXT NOT NULL REFERENCES depositos(id_deposito),
    id_producto TEXT NOT NULL REFERENCES productos(id_producto),
    cantidad INTEGER NOT NULL CHECK (typeof(cantidad) = 'integer' AND cantidad > 0)
);

-- Pedidos: las reservas activas se derivan de los ítems de pedidos Confirmados.
CREATE TABLE IF NOT EXISTS pedidos (
    id_pedido TEXT PRIMARY KEY NOT NULL CHECK (length(trim(id_pedido)) > 0),
    cliente TEXT NOT NULL CHECK (length(trim(cliente)) > 0),
    destino TEXT NOT NULL CHECK (length(trim(destino)) > 0),
    prioridad INTEGER NOT NULL CHECK (typeof(prioridad) = 'integer' AND prioridad BETWEEN 1 AND 3),
    hora_inicio TEXT,
    hora_fin TEXT,
    observaciones TEXT,
    estado TEXT NOT NULL DEFAULT 'Borrador'
        CHECK (estado IN ('Borrador', 'Confirmado', 'Despachado', 'Entregado', 'Cancelado')),
    patente_vehiculo TEXT REFERENCES vehiculos(patente),
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Las cantidades por depósito componen el total solicitado del pedido.
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

-- UNIQUE permite varios vehículos sin conductor, pero no repetir un DNI.
CREATE TABLE IF NOT EXISTS vehiculos (
    patente TEXT PRIMARY KEY NOT NULL CHECK (length(trim(patente)) > 0),
    capacidad_maxima REAL NOT NULL CHECK (capacidad_maxima > 0),
    estado TEXT NOT NULL DEFAULT 'Disponible'
        CHECK (estado IN ('Disponible', 'En Ruta', 'Mantenimiento')),
    dni_conductor TEXT UNIQUE REFERENCES conductores(dni),
    CHECK (estado != 'Mantenimiento' OR dni_conductor IS NULL),
    CHECK (estado != 'En Ruta' OR dni_conductor IS NOT NULL)
);

-- DATOS BASE
-- La aplicación ejecuta esta sección después de migrar las bases antiguas.
-- El marcador evita duplicar registros, reponer stock o recrear datos borrados.
BEGIN IMMEDIATE;

CREATE TABLE IF NOT EXISTS inicializaciones (
    nombre TEXT PRIMARY KEY NOT NULL,
    aplicado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TEMP TRIGGER cargar_base_inicial
AFTER INSERT ON main.inicializaciones
WHEN NEW.nombre = 'datos_base_v1'
    AND NOT EXISTS (SELECT 1 FROM productos)
    AND NOT EXISTS (SELECT 1 FROM depositos)
    AND NOT EXISTS (SELECT 1 FROM conductores)
    AND NOT EXISTS (SELECT 1 FROM vehiculos)
    AND NOT EXISTS (SELECT 1 FROM pedidos)
    AND NOT EXISTS (SELECT 1 FROM existencias)
    AND NOT EXISTS (SELECT 1 FROM pedido_items)
    AND NOT EXISTS (SELECT 1 FROM ingresos_stock)
BEGIN
    INSERT INTO productos (id_producto, nombre, volumen_unitario, peso_unitario) VALUES
        ('PRD-1', 'Pantalón', 0.004, 0.5),
        ('PRD-2', 'Campera', 0.008, 0.9),
        ('PRD-3', 'Remera', 0.002, 0.2);

    INSERT INTO depositos (id_deposito, nombre, ubicacion, capacidad_maxima) VALUES
        ('D-001', 'Depósito Centro', 'Centro, Bariloche', 50.0),
        ('D-002', 'Depósito Melipal', 'Melipal, Bariloche', 30.0),
        ('D-003', 'Depósito Dina Huapi', 'Dina Huapi', 20.0);

    INSERT INTO existencias (id_deposito, id_producto, cantidad) VALUES
        ('D-001', 'PRD-1', 200),
        ('D-002', 'PRD-2', 100),
        ('D-003', 'PRD-3', 300);

    INSERT INTO conductores (dni, nombre) VALUES
        ('28555111', 'Juan Pérez'),
        ('30111222', 'Carlos Gómez'),
        ('31333444', 'Ana Silva');

    INSERT INTO vehiculos (patente, capacidad_maxima, dni_conductor) VALUES
        ('AB123CD', 3.0, '28555111'),
        ('EF456GH', 2.5, '30111222'),
        ('IJ789KL', 20.0, '31333444');

    INSERT INTO pedidos (id_pedido, cliente, destino, prioridad, hora_inicio, hora_fin, observaciones) VALUES
        ('P-001', 'Supermercado Sur', 'Av. Pioneros 4500', 3, '08:00', '12:00', 'Pedido inicial para practicar confirmación y despacho.'),
        ('P-002', 'Despensa Centro', 'Mitre 200', 2, '10:00', '14:00', 'Pedido inicial con retiro desde Melipal.'),
        ('P-003', 'Kiosco Melipal', 'Av. Bustillo 4000', 1, '14:00', '18:00', 'Pedido inicial con retiro desde Dina Huapi.');

    INSERT INTO pedido_items (id_pedido, id_deposito, id_producto, cantidad) VALUES
        ('P-001', 'D-001', 'PRD-1', 5),
        ('P-002', 'D-002', 'PRD-2', 3),
        ('P-003', 'D-003', 'PRD-3', 10);
END;

INSERT INTO inicializaciones (nombre)
SELECT 'datos_base_v1'
WHERE NOT EXISTS (SELECT 1 FROM inicializaciones WHERE nombre = 'datos_base_v1');
DROP TRIGGER temp.cargar_base_inicial;
COMMIT;
