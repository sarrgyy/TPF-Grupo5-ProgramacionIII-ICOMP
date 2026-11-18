# Nuevo pedido integrado — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Completar datos, productos y confirmación en un único bloque de Cargas sin buscar el pedido recién creado.

**Architecture:** Mantener las rutas y el guardado de borradores existentes. Reorganizar HTML y renderizado JavaScript con indicadores de progreso; usar la respuesta del alta para abrir los productos inmediatamente. Retomar pedidos existentes queda en un bloque desplegable separado.

**Tech Stack:** HTML, CSS y JavaScript actuales; FastAPI/SQLite sin cambios; pytest y Chromium.

**Spec:** Propuesta de esta conversación aprobada por el usuario: «Datos → Productos → Confirmación», con búsqueda aparte para retomar pedidos existentes.

## Global Constraints

- Conservar reglas de stock, reservas, vehículo, cancelación y despacho.
- Guardar el borrador y su URL para permitir recarga y recuperación.
- Mantener documentación en español y no modificar la base de trabajo.
- Trabajar sobre los cambios existentes sin commits ni push.

## Review Focus

- Recarga después de agregar productos: conserva pedido e ítems.
- Alta exitosa seguida de fallo de una consulta: no obliga a volver a crear el pedido.
- Recuperación inexistente: no deja acciones sobre el pedido anterior.
- Confirmación sin productos: deshabilitada; error de stock mantiene borrador editable.
- Vista móvil y teclado: avance a productos visible y con foco accesible.

## Task 1: Integrar el recorrido y verificarlo

**Files:** `Frontend/cargas.html`, `Frontend/carga.js`, `Frontend/styles.css`, `tests/test_browser.py`, `README.md` y registro de verificación.

**Interfaces:** Consumir el objeto de pedido devuelto por POST /pedidos. Conservar IDs de formularios y rutas HTTP; cambiar rótulos de creación/recuperación junto con las pruebas consumidoras.

- [x] Añadir pruebas de recorrido continuo, recarga/recuperación y ausencia de consulta redundante tras el alta; verlas fallar antes de implementar.
- [x] Agrupar los tres pasos en un bloque; separar recuperación en un desplegable; enfocar productos al guardar datos y deshabilitar confirmación vacía.
- [x] Actualizar pruebas anteriores por los nuevos rótulos y revisar escritorio/móvil en Chromium.
- [x] Ejecutar suite completa, Ruff, sintaxis JS y diff; actualizar README y resultados.
- [x] Revisar el cambio final y resolver hallazgos materiales con pruebas.

**Resultado:** 290 pruebas aprobadas, incluidas 19 de Chromium. Los hallazgos de revisión sobre fallo de flota después de guardar y descripción accesible de confirmación se reprodujeron y corrigieron con pruebas. Base de trabajo intacta; sin commits ni push.
