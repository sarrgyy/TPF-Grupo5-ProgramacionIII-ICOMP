# Distribución SQLite — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Vincular pedidos confirmados y flota, con despacho y entrega atómicos.

**Architecture:** Referencia en pedidos y restricción UNIQUE parcial para un pedido activo por vehículo. Migración aditiva en InventarioSQLite. Flota consulta la ocupación desde pedidos.

**Tech Stack:** Python 3.12+, sqlite3, unittest; sin dependencias externas.

**Spec:** `docs/superpowers/specs/2026-11-12-distribucion-sqlite-design.md`.

## Global Constraints

- No reemplazar bases anteriores ni alterar datos para simular asignaciones antiguas.
- Un pedido completo por vehículo; sin viajes ni rutas.
- Mantener cambios anteriores de flota y dejar sin commit esta etapa.

## Review Focus

- Un vehículo reservado no puede perder su conductor ni pasar a mantenimiento.
- Un despacho fallido revierte inventario, pedido y vehículo.
- Dos conexiones no pueden ocupar el mismo vehículo.
- Abrir una base anterior agrega la columna una sola vez y conserva los pedidos.
- Entregar un pedido anterior sin vehículo mantiene compatibilidad.

### Task 1: Asignación y transacciones

**Files:** Modificar `Backend/schema.sql`, `persistencia.py`, `pedidos.py`, `flota.py`, `modelos/vehiculo.py`; crear `tests/test_distribucion.py`; adaptar fixtures de pedidos anteriores.

**Interfaces:** `PedidosSQLite.asignar_vehiculo(id_pedido, patente)`, `liberar_vehiculo(id_pedido)`; consultas agregan `Pedido.vehiculo_asignado` y `Vehiculo.pedido_asignado`.

- [x] Escribir pruebas y ejecutarlas antes de implementar.
- [x] Agregar migración y referencia, validaciones, bloqueos y transacciones de despacho/entrega.
- [x] Adaptar pruebas anteriores para asignar vehículo antes de nuevos despachos; verificar migración y concurrencia.

### Task 2: Integración y documentación

**Files:** Modificar `Backend/main.py`, `README.md`, `tests/test_main.py`.

- [x] Probar salida de consola con vínculo persistente en ambos sentidos.
- [x] Mostrar asignación y carga sin modificar la flota real en la simulación.
- [x] Actualizar ejemplos manuales, alcance y esquema.
- [x] Ejecutar suite completa, revisión independiente, ejemplo manual y git diff --check.


## Registro de ejecucion

- Task 1 completa: pruebas iniciales fallaron por asignacion/migracion ausentes; SQLite real verifica asignacion, capacidad, conflictos, rollback y concurrencia.
- Task 2 completa: prueba de consola fallo antes de integrar; ejemplos anteriores adaptados al requisito de vehiculo.
- Revision independiente sin hallazgos accionables. Suite completa: 51 pruebas aprobadas.
- Flujo manual con dos depositos, despacho, reapertura y entrega verificado en base temporal.
- Se preservan los cambios anteriores de flota. Sin commits ni push.
