# Menú de consola — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Operar inventario, pedidos y flota con un menú de texto.

**Architecture:** Menú y consultas en consola.py; main selecciona modo interactivo, resumen o simulación. Todas las escrituras reutilizan las APIs persistentes actuales.

**Tech Stack:** Python 3.12+, input/print, argparse, unittest, sqlite3; sin paquetes nuevos.

**Spec:** `docs/superpowers/specs/2026-11-12-menu-consola-design.md`.

## Global Constraints

- Conservar las reglas de inventario, reservas, estados y ocupación de flota.
- Mantener --db y --simular-pedidos; agregar --resumen y menú por defecto.
- Sin commits ni push para esta etapa.

## Review Focus

- Cancelar o interrumpir una carga no debe escribir datos incompletos.
- Errores de números, stock, duplicados o estados no deben cerrar el menú.
- Un pedido rechazado debe seguir como borrador y poder corregirse.
- El flujo completo debe persistir sin modificar datos por solo consultarlos.
- Las opciones no interactivas deben terminar sin solicitar entrada.

### Task 1: Menú y navegación

**Files:** Crear `Backend/consola.py`, `tests/test_consola.py`; modificar `Backend/main.py`, `tests/test_main.py`.

**Interfaces:** `ejecutar_menu(inventario)`, `mostrar_inventario(inventario)`, `mostrar_pedidos(inventario)`, `mostrar_flota(inventario)` en consola.py. Main usa por defecto ejecutar_menu, o consultas con --resumen/--simular-pedidos.

- [x] Escribir y ejecutar pruebas de entrada real, esperando fallo antes de implementar.
- [x] Mover las consultas compartidas, implementar submenús y validar entradas antes de invocar APIs existentes.
- [x] Probar flujo completo, correcciones, errores, salida y compatibilidad no interactiva.

### Task 2: Documentación y revisión

**Files:** Modificar `README.md`.

- [x] Documentar inicio interactivo, opciones y una prueba manual completa por menú.
- [x] Ejecutar toda la suite, revisar de forma independiente y verificar git diff --check.


## Registro de ejecucion

- Task 1 completa: pruebas iniciales fallaron por operaciones ausentes; el menu reutiliza APIs sin modificar reglas de negocio.
- Task 2 completa: README actualizado y recorrido manual por menu verificado contra base temporal con reapertura.
- Suite completa: 56 pruebas aprobadas, incluyendo formularios incompletos, errores y flujo de entrega real.
- Revision independiente sin hallazgos accionables. Ctrl+C esta manejado pero no tiene prueba especifica; EOF si se verifica automaticamente.
- Sin commits ni push. No se uso la base habitual para las pruebas.
