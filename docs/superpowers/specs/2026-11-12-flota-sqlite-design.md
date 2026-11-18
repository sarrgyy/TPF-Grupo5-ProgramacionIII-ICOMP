# Flota persistente para la primera prueba

## Alcance

Registro y recuperación de vehículos y conductores, asignación manual uno a uno, liberación y cambios de estado. Sin viajes, turnos, historial de asignaciones ni relación con pedidos todavía.

## Diseño

Se amplía la misma base SQLite con `conductores` (dni, nombre, estado Disponible/Inactivo) y `vehiculos` (patente, capacidad máxima positiva y finita, estado Disponible/En Ruta/Mantenimiento, dni_conductor nullable, FK y UNIQUE). La alternativa de guardar la referencia en ambas tablas se descarta porque duplica el dato. El estado Asignado del conductor y su vehículo se derivan de la referencia única en vehículos.

FlotaSQLite comparte conexión y transacciones BEGIN IMMEDIATE con InventarioSQLite, siguiendo el patrón de PedidosSQLite. Devuelve copias de los modelos existentes; los métodos de esas copias no escriben en SQLite.

Reglas: al registrar no se aceptan asignaciones ni pedidos en memoria preexistentes; se asigna con el método persistente. Se asigna solo vehículo Disponible y conductor Disponible sin otro vehículo. Repetir o reemplazar una asignación se rechaza; primero hay que liberarla. Un conductor asignado no puede inactivarse y un vehículo asignado no puede pasar a mantenimiento. Se conserva el estado En Ruta existente: requiere conductor y no permite liberar la asignación hasta volver a Disponible. Asignado no se establece manualmente en el conductor.

Los identificadores y nombres son textos no vacíos; no se normalizan DNI ni patentes para no imponer reglas locales fuera de alcance. Duplicados producen sqlite3.IntegrityError; reglas inválidas y referencias inexistentes producen ValueError. Las nuevas tablas se crean sin borrar inventario ni pedidos anteriores. No se carga flota de ejemplo automáticamente, para no modificar asignaciones guardadas al arrancar. La simulación anterior mantiene sus objetos en memoria.

## Verificación

SQLite real y archivos temporales: reapertura de asignaciones, conflictos en ambos sentidos, estados y validaciones, liberación y reasignación, dos conexiones concurrentes y compatibilidad con la base anterior. La consola muestra la flota guardada. El README incluye un ejemplo manual contra una base separada.
