# Vinculación de pedidos y vehículos

## Alcance acordado

Asignación manual de un pedido Confirmado a un vehículo Disponible, con conductor y capacidad para todo el volumen. Un solo pedido activo por vehículo. Despachar descuenta las reservas y deja el vehículo En Ruta en una transacción; entregar lo devuelve a Disponible. No se calculan recorridos ni se modelan viajes, paradas o entregas parciales.

## Diseño y alternativas

Se elige una referencia nullable `pedidos.patente_vehiculo` a `vehiculos` frente a una tabla independiente de viajes, porque no necesitamos una entidad de viaje todavía. Un índice UNIQUE parcial sobre esa referencia para pedidos Confirmados/Despachados evita la doble ocupación incluso con conexiones concurrentes. Al cancelar o entregar, la referencia se conserva como dato histórico, pero ya no ocupa el vehículo.

La apertura agrega la columna a bases anteriores con ALTER TABLE dentro de BEGIN IMMEDIATE y crea el índice sin reemplazar tablas ni datos. Pedidos Despachados por versiones anteriores sin vehículo pueden marcarse Entregados sin afectar flota; los despachos nuevos exigen vehículo.

`PedidosSQLite.asignar_vehiculo(id_pedido, patente)` valida confirmación, conductor, disponibilidad y volumen. Para cambiar vehículo antes del despacho se llama `liberar_vehiculo(id_pedido)` y se asigna otro; no se editan los productos confirmados. Cancelar libera reservas y ocupación lógica. Despachar revalida todo y actualiza stock, pedido y vehículo de forma atómica. Entregar libera el vehículo conservando su conductor.

FlotaSQLite impide liberar conductor o cambiar estado mientras el vehículo tiene un pedido activo. Las consultas agregan `pedido_asignado` al vehículo y `vehiculo_asignado` al pedido. El volumen ocupado del vehículo es cero antes del despacho y se calcula a partir del pedido Despachado. La simulación en memoria sigue independiente. La capacidad se compara con la misma tolerancia decimal usada en inventario.

No se agrega menú ni se persisten datos de la simulación. No se hacen commits ni push sin una solicitud para esta etapa.

## Pruebas

Asignación y reapertura, falta de conductor/capacidad, borradores y ocupación, liberación/cancelación, bloqueos de flota, despacho/entrega completos, rollback por falla en flota, asignaciones concurrentes, migración repetida preservando pedidos anteriores. Actualizar los ejemplos de pedidos para que asignen un vehículo antes del despacho.
