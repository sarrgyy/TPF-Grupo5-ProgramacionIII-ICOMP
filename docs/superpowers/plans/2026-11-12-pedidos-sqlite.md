# Pedidos y reservas — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Persistir pedidos de varios depósitos con reservas y transiciones atómicas.

**Architecture:** PedidosSQLite comparte InventarioSQLite; las reservas se derivan de ítems Confirmados. La base existente se amplía con CREATE TABLE IF NOT EXISTS.

**Tech Stack:** Python 3.12+, sqlite3, unittest, sin paquetes externos.

**Spec:** `docs/superpowers/specs/2026-11-12-pedidos-sqlite-design.md`.

## Global Constraints

- Estados: Borrador, Confirmado, Despachado, Entregado, Cancelado.
- Confirmar y despachar son operaciones completas; cancelar solo antes de despachar.
- Preservar inventario local, simulación y cambios no commiteados; no hacer commits ni push.

## Review Focus

- Dos pedidos no pueden reservar las mismas unidades, incluso con dos conexiones.
- Una confirmación rechazada debe mantener borrador e informar todos los faltantes.
- Un traslado/retiro no puede consumir reservas.
- Un despacho repetido o fallido no puede perder mercadería.
- Una base anterior debe abrirse sin perder existencias.

### Task 1: Pedidos y reservas

**Files:** Crear `Backend/pedidos.py`, `tests/test_pedidos.py`; modificar `Backend/schema.sql` y `Backend/persistencia.py`.

**Interfaces:** `PedidosSQLite(inventario)`; `crear_borrador(id_pedido, cliente, destino, prioridad=1)`, `editar_borrador(id_pedido, cliente, destino, prioridad=1)`, `establecer_producto(id_pedido, id_deposito, id_producto, cantidad)`, `quitar_producto(id_pedido, id_deposito, id_producto)`, `obtener_pedido(id_pedido)` devuelve Pedido, `listar_pedidos()` devuelve lista de Pedido; `confirmar`, `cancelar`, `despachar`, `entregar` reciben id_pedido. Inventario expone `stock_reservado(deposito, producto)` y `stock_disponible(deposito, producto)`.

- [x] Escribir y ejecutar pruebas antes de implementar; deben fallar por funcionalidad ausente.
- [x] Añadir tablas y operaciones, validación de estados, detalle de faltantes y protección del stock.
- [x] Verificar reapertura, edición, reservas, estados, rollback y concurrencia con SQLite real.

### Task 2: Integración y documentación

**Files:** Modificar `Backend/main.py`, `README.md`, `tests/test_main.py`.

- [x] Probar que la salida de consola diferencia stock físico, reservado y disponible, y muestra pedidos guardados.
- [x] Integrar esas consultas sin confirmar ni despachar pedidos automáticamente.
- [x] Documentar el flujo y un ejemplo manual contra un archivo separado.
- [x] Ejecutar toda la suite, revisar de forma independiente y ejecutar git diff --check.

## Registro

- El usuario autorizó implementar las reglas definidas en la conversación.
- Decisión: reservas derivadas del estado Confirmado, sin tabla duplicada; cantidad solicitada definida por la suma de asignaciones manuales.

- Task 1 completa: pruebas iniciales fallaron por funcionalidad ausente; SQLite real verifica reservas, estados, rollback, concurrencia y compatibilidad con base anterior.
- Task 2 completa: prueba de salida falló antes de integrar y pasó después; README actualizado con ejemplo manual verificado y recuperación al reabrir.
- Revisión independiente sin hallazgos accionables; suite completa de 30 pruebas aprobada.
- Se conserva la rama y los cambios sin commit. La base habitual no se utilizó para crear pedidos de prueba.
