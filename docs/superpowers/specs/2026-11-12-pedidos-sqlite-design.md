# Pedidos con reservas en SQLite

## Alcance acordado

Un pedido reúne productos de varios depósitos seleccionados manualmente. Se guarda como Borrador editable. Confirmar valida todas sus cantidades y reserva todo o nada; si falta stock, informa los faltantes y conserva el borrador. Un pedido Confirmado no se edita: se cancela y se crea otro. Despachar consume todas las reservas y descuenta todo el stock en una transacción. Entregado solo sucede a Despachado. Solo Borrador y Confirmado se pueden cancelar.

## Diseño

Se amplía la misma base SQLite, sin reemplazar existencias. `pedidos` guarda id, cliente, destino, prioridad (1 a 3), estado y fecha de creación. `pedido_items` guarda pedido, depósito, producto y cantidad positiva; la clave es esa triple combinación. La cantidad de un producto pedida es la suma de sus asignaciones manuales a depósitos.

Alternativas: mantener una tabla adicional de reservas o calcular las reservas desde los ítems de pedidos Confirmados. Se elige calcularlas: los ítems confirmados son inmutables y el estado determina si la reserva está activa, evitando dos fuentes del mismo dato. Es una decisión técnica del implementador.

`PedidosSQLite(inventario)` reutiliza la conexión y las transacciones del inventario. Los retiros y traslados solo pueden consumir stock no reservado. La capacidad física sigue considerando toda la mercadería, incluida la reservada. Las escrituras usan BEGIN IMMEDIATE para serializar confirmaciones y movimientos.

La confirmación vacía se rechaza. Las cantidades son enteras positivas de 64 bits; cliente, destino e identificadores no pueden estar vacíos. Las transiciones repetidas se rechazan para evitar doble despacho. Una excepción StockInsuficiente, compatible con ValueError, incluye los faltantes por producto y depósito. Cancelar preserva los ítems como registro pero desactiva sus reservas. No hay cancelación posterior al despacho, devolución, entrega parcial ni asignación automática.

El objeto Pedido recuperado es una copia para consulta: cambiarlo no persiste. Se conservan los estados de la simulación logística anterior, que no alteran los pedidos persistidos. No se agregan menú, interfaz web ni persistencia de flota. El usuario hace los commits.

## Validación

SQLite real en bases temporales: reapertura, edición exclusiva de borradores, faltantes completos sin reserva parcial, stock disponible, protección de retiros y traslados, cancelación, despacho único y completo, rollback ante falla, entrega y confirmaciones concurrentes. La apertura de una base con las tres tablas anteriores debe preservar sus datos y agregar las nuevas tablas.
