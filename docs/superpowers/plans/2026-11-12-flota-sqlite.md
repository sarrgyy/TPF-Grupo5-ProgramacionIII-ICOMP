# Flota SQLite — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Persistir vehículos, conductores y asignaciones manuales uno a uno.

**Architecture:** FlotaSQLite reutiliza InventarioSQLite; la única referencia a la asignación está en vehiculos.dni_conductor, con FK y UNIQUE. El estado Asignado del conductor se calcula al consultar.

**Tech Stack:** Python 3.12+, sqlite3, unittest, sin dependencias externas.

**Spec:** `docs/superpowers/specs/2026-11-12-flota-sqlite-design.md`.

## Global Constraints

- Conservar inventario, pedidos y simulación; no implementar viajes ni pedidos por vehículo.
- Sin asignaciones automáticas, sin cambios de identidad Git ni push.

## Review Focus

- Una asignación no puede duplicarse ni reemplazarse implícitamente.
- Dos conexiones no pueden asignar el mismo conductor a distintos vehículos.
- Inactivar o enviar a mantenimiento no debe dejar una asignación inválida.
- Las copias recuperadas no guardan cambios por sus métodos en memoria.
- Abrir una base anterior conserva inventario y pedidos.

### Task 1: Persistencia de flota

**Files:** Crear `Backend/flota.py`, `tests/test_flota.py`; ampliar `Backend/schema.sql`.

**Interfaces:** `FlotaSQLite(inventario)`, `registrar_vehiculo(vehiculo)`, `registrar_conductor(conductor)`, `obtener_vehiculo(patente)`, `obtener_conductor(dni)`, `listar_vehiculos()`, `listar_conductores()`, `asignar_conductor(patente, dni)`, `liberar_conductor(patente)`, `actualizar_estado_vehiculo(patente, estado)`, `actualizar_estado_conductor(dni, estado)`.

- [x] Crear pruebas y ejecutar antes de implementar; fallo por módulo ausente.
- [x] Implementar tablas, consultas y transacciones respetando las reglas del diseño.
- [x] Verificar reapertura, restricciones, estados, reasignación y concurrencia con SQLite real.

### Task 2: Consola y documentación

**Files:** Modificar `Backend/main.py`, `tests/test_main.py`, `README.md`.

- [x] Probar que un nuevo arranque muestra las asignaciones guardadas y no las reemplaza.
- [x] Mostrar flota persistente y conservar simulación independiente.
- [x] Documentar esquema, operaciones, límites y prueba manual.
- [x] Ejecutar suite completa, revisión independiente y git diff --check.

## Registro

- Alcance autorizado por el usuario para primera prueba sencilla.

- Task 1 completa: pruebas iniciales fallaron por modulo ausente; pruebas reales verifican reapertura, validaciones, estados y asignaciones concurrentes.
- Task 2 completa: prueba de consola fallo antes de integracion y paso despues. README actualizado con ejemplo manual verificado en base temporal.
- Revision independiente sin hallazgos accionables; suite completa de 42 pruebas aprobada.
- No se uso la base habitual para crear flota de prueba; no se hicieron commits ni push.
