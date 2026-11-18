# Persistencia de inventario — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Persistir productos, depósitos y stock por depósito con SQLite.

**Architecture:** `InventarioSQLite` concentra SQL y transacciones. Los modelos conservan los datos del dominio; las consultas reconstruyen productos y depósitos y calculan la ocupación. La demo utiliza este inventario sin descontar stock por pedidos no persistidos.

**Tech Stack:** Python 3.12, sqlite3, unittest, pathlib; sin dependencias externas.

**Spec:** `docs/superpowers/specs/2026-11-12-inventario-sqlite-design.md`.

## Global Constraints

- Una base, tres tablas; cantidades enteras no negativas, medidas positivas y finitas.
- No implementar persistencia de pedidos, conductores, vehículos ni entregas.
- Mantener `persistencia_en_db`; no hacer commits ni push.

## Review Focus

- Una reapertura y una segunda ejecución deben conservar el stock modificado.
- Un traslado sin capacidad en destino no debe descontar origen.
- Una referencia inexistente no debe interpretarse como stock cero.
- Números no finitos, cantidades fraccionarias y claves duplicadas deben rechazarse.
- La carga inicial y la simulación no deben reponer ni consumir existencias existentes.

### Task 1: Inventario persistente

**Files:** Crear `Backend/persistencia.py`, `Backend/schema.sql`, `tests/test_inventario.py`; modificar `Backend/modelos/productos.py`.

**Interfaces:** `InventarioSQLite(ruta)` como context manager; `registrar_producto(producto)`, `registrar_deposito(deposito)`, `obtener_producto(id_producto)`, `obtener_deposito(id_deposito)`, `listar_productos()`, `listar_depositos()`, `stock(id_deposito, id_producto)`, `stock_total(id_producto)`, `actualizar_stock(id_deposito, id_producto, cantidad)`, `transferir(origen, destino, id_producto, cantidad)`, `cargar_iniciales(productos, depositos, existencias)` (devuelve si se cargaron).

- [x] Escribir pruebas con archivos temporales para reapertura, dos depósitos, capacidad exacta y excedida, stock insuficiente, ids inexistentes, duplicados, datos inválidos, traslado y rollback.
- [x] Ejecutar `python -B -m unittest discover -s tests -v` y confirmar fallo por implementación ausente.
- [x] Crear esquema con claves y restricciones; implementar operaciones SQL parametrizadas y transacciones `BEGIN IMMEDIATE`; separar stock de `Producto`.
- [x] Ejecutar la suite y comprobar los casos de Review Focus de esta tarea.

### Task 2: Integración y documentación

**Files:** Modificar `Backend/main.py`, `Backend/modelos/main.py`, `README.md`; crear `.gitignore` y `tests/test_main.py`.

**Interfaces:** `python Backend/main.py --db RUTA [--simular-pedidos]`; el arranque muestra inventario y carga ejemplos solo si está vacío.

- [x] Probar mediante subprocess dos arranques con una modificación de stock intermedia y una simulación que no consume existencias.
- [x] Ejecutar las pruebas y observar el fallo antes de adaptar la demo.
- [x] Integrar SQLite, conservar la simulación opcional y sustituir la copia obsoleta de main por un acceso al punto de entrada actual.
- [x] Documentar esquema, ruta, operaciones de ejemplo, límites y comando de pruebas; ignorar bases locales y cachés nuevas.
- [x] Ejecutar suite completa, demo normal, simulación y `git diff --check`; revisar el cambio completo y dejarlo sin commit.

## Registro de ejecución

- Autorización: el usuario eligió SQLite e indicó avanzar con la implementación de esta primera etapa.
- Decisión: no ejecutar automáticamente pedidos contra stock real hasta persistirlos; evita consumos repetidos sin registro.

- Task 1: completa. Pruebas iniciales fallaron por módulo ausente y luego pasaron contra SQLite real.
- Task 2: completa. Las tres pruebas de integración fallaron antes de adaptar main y después pasaron.
- Revisión independiente: detectó overflow de SUM al agregar cantidades válidas de varios depósitos; reproducido con prueba y corregido usando enteros Python.
- Verificación final: 17 pruebas pasan; demo con base predeterminada y simulación ejecutadas correctamente; git diff --check sin errores.
- Sin commits ni push. Archivo local de base excluido por .gitignore.
