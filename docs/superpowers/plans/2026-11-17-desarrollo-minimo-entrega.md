# Plan de implementación para la entrega mínima

Implementación completada en el directorio de trabajo de `desarrollo_minimo`. Ver `docs/VERIFICACION.md` para los resultados. Los commits, la etiqueta y el push quedan a cargo del usuario. La validación desde cero se realizó exportando las fuentes finales a una carpeta limpia con un entorno nuevo, porque los cambios aún no están guardados en commits.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Este documento es un plan; no autoriza por sí solo a realizar commits, push ni publicar.

**Goal:** Entregar una aplicación local que permita administrar productos y stock, crear pedidos, reservar mercadería, asignar un vehículo, despachar, consultar el seguimiento y registrar la entrega, conservando los datos al reiniciar.

**Architecture:** Reutilizar InventarioSQLite, PedidosSQLite y FlotaSQLite para las reglas y transacciones. Agregar una API FastAPI pequeña y servir el HTML/CSS/JavaScript existente desde el mismo servidor. La consola seguirá disponible como alternativa funcional.

**Tech Stack:** Python, SQLite, FastAPI, Uvicorn, JavaScript sin frameworks, HTML/CSS; pytest y httpx para las pruebas HTTP.

**Spec:** `C:/Users/timai/OneDrive/Desktop/Universidad/Programacion 3/Plan de entrega en 24 horas.docx`, con los ajustes de alcance explicitados en este documento y las comprobaciones realizadas en esta conversación.

## Punto de partida verificado

- Rama actual: `desarrollo_minimo`. HEAD observado: `dcc6f33`.
- Los cambios de `../files/bloque1.zip` todavía no están incorporados al código de la rama.
- El main actual conserva imports incompatibles con la ejecución como paquete. En pedidos.py, las operaciones desde crear_borrador están fuera de la clase.
- El esquema contiene `obvservaciones`. La base local existente tampoco tiene las columnas hora_inicio, hora_fin y observaciones que necesita la propuesta.
- El paquete del compañero funcionó, aplicado a una copia temporal del repo, con base nueva y circuito completo por consola. Las comprobaciones puntuales de los cinco casos de negocio pasaron; no hay fuentes de tests en tests/.
- No hay API. Las páginas son estáticas y no cargan scripts; carga.js, gestion.js y seguimiento.js están vacíos.
- La base, las cachés, tests/ y docs/ aparecen como archivos sin seguimiento. Hay también archivos .pyc ya versionados. No hacer git add . sin revisar.

## Global Constraints

- Trabajar sobre `desarrollo_minimo`; no volver a hacer pull durante una etapa con cambios pendientes.
- Conservar Python, SQLite y las páginas existentes. No introducir un framework de frontend ni reescribir los repositorios.
- Los estados de pedido son Borrador, Confirmado, Despachado, Entregado y Cancelado. La prioridad es un entero entre 1 y 3.
- Confirmar reserva todo o nada. Despachar descuenta stock una única vez. Solo Borrador y Confirmado se cancelan.
- El stock pertenece a una pareja depósito/producto. Físico, reservado y disponible se muestran por separado.
- La restricción de capacidad es volumen en m³. El peso en kg se conserva como dato informativo. No mostrar precios: el sistema no los modela.
- Un vehículo admite un pedido activo y necesita conductor asignado. Se proveen depósitos, vehículos y conductores de demostración; sus altas web no son parte de esta entrega.
- Conservar una copia de la base actual antes de cambiarla. Para esta entrega se propone una base nueva; recuperar datos anteriores mediante migración queda fuera de este recorte.
- Las pruebas usan bases temporales, nunca Backend/logistica.db. La consola y la API usan por defecto la misma ruta absoluta, derivada de Backend/main.py.
- Conservar las transacciones y validaciones en los repositorios. La API traduce entradas y resultados; JavaScript no decide las reglas de stock.
- No incluir rutas, restricciones por peso, estadísticas avanzadas, autenticación, precios, edición/borrado de catálogos ni rediseño visual.
- Documentar funcionalidades comprobadas. Una línea de tiempo muestra etapas por estado, sin inventar horas de eventos que no se registran.
- Revisar y hacer un commit por etapa cuando corresponda; el usuario decide cuándo ejecutarlo. No realizar push ni publicar como parte automática del plan.

## Review Focus

1. Base antigua incompatible: el arranque debe funcionar sobre una base nueva sin destruir el archivo anterior; indicar cómo hacer el respaldo y elegir otra ruta.
2. Datos vacíos, cantidades fraccionarias o negativas y ventanas incompletas: rechazar sin escrituras parciales.
3. Doble clic o transición repetida: no duplicar pedidos, reservas ni descuentos de stock.
4. Estado Cancelado o pedido sin horario: no mostrarlo como entrega completada ni perder observaciones al consultar.
5. Reinicio, identificador inexistente y caída de red: conservar datos, mostrar un error y permitir corregir/reintentar sin afirmar éxito.

## Orden y presupuesto

Estimaciones de trabajo efectivo de una persona familiarizada con el proyecto, no garantías. Aproximadamente 11 a 15 horas con el inicio opcional; reservar además margen para integración y descanso.

| Etapa | Tiempo | Condición para avanzar |
|---|---|---|
| 1. Integrar backend | 45–60 min | Arranque y resumen con base nueva |
| 2. Modelos y datos de consulta | 45–60 min | Estados y observaciones coherentes |
| 3. Pruebas de negocio | 45–60 min | Pruebas repetibles y verdes |
| 4. API y contrato | 3–4 h | Circuito completo por HTTP |
| 5. Gestión web | 1–1,5 h | Alta e ingreso de stock reales |
| 6. Cargas y seguimiento | 2,5–3,5 h | Circuito completo por navegador |
| 7. Inicio opcional | 30–45 min | Solo datos reales |
| 8. Documentación y entrega | 1,5–2 h | Ejecución desde copia limpia |

**Cortes de tiempo:** si el backend no arranca a la hora y media, concentrarse en ese bloqueo. A las seis horas evaluar el circuito HTTP: si todavía no funciona y el margen restante no alcanza, priorizar consola, pruebas y documentación, declarando la web como maqueta. Empezar la documentación a más tardar cinco horas antes de entregar. En los últimos 90 minutos, congelar funcionalidades y ensayar.

## Tarea 1: Integrar el backend del compañero

**Archivos:** incorporar los archivos de `../files/bloque1.zip` según sus rutas internas: Backend/__init__.py, consola.py, main.py, pedidos.py, schema.sql, modelos/__init__.py, modelos/vehiculo.py y ejemplos/simulacion_en_memoria.py. Retirar Backend/modelos/main.py como punto de entrada duplicado. Crear .gitignore en la raíz y requirements.txt.

**Interfaces:** conservar `InventarioSQLite(ruta)`, `PedidosSQLite(inventario)` y `FlotaSQLite(inventario)`. Incorporar `cargar_datos_demo(inventario) -> bool` y `main(argv=None)` del paquete revisado.

- [ ] Respaldar Backend/logistica.db sin sobrescribirlo y revisar git status. No reemplazar Backend/ por la carpeta files: faltan dependencias que deben conservarse.
- [ ] Aplicar el ZIP conservando el resto del repositorio. El __init__.py de modelos debe quedar dentro de Backend/modelos/, no con el nombre largo del archivo suelto.
- [ ] Crear .gitignore para .venv/, __pycache__/, *.py[cod], *.db, *.db-journal, *.db-wal y *.db-shm. No copiar la regla que oculta docs/superpowers/: este plan debe poder compartirse. Retirar del índice las cachés ya versionadas.
- [ ] Crear requirements.txt con fastapi, uvicorn, pytest y httpx; usar un entorno virtual y registrar versiones compatibles después de comprobar instalación y pruebas.
- [ ] Ejecutar `python -m Backend.main --db :memory: --resumen`. Esperado: inventario y tres vehículos con tres conductores; salida sin traceback. Ejecutar el menú con una base nueva de desarrollo y salir con 0.
- [ ] Revisar el diff y dejar un commit de integración, sin base ni cachés, cuando el usuario lo decida.

## Tarea 2: Corregir modelos y reconstrucción de pedidos

**Archivos:** Backend/modelos/pedido.py, Backend/pedidos.py, Backend/consola.py; revisar Backend/modelos/entrega.py y los ejemplos afectados. Crear tests/test_modelos.py.

**Interfaces:** `Pedido(id_pedido, cliente, destino, prioridad=1)` conserva su firma. `obtener_pedido(id_pedido) -> Pedido` entrega también hora_inicio, hora_fin y observaciones como atributos de cabecera, aunque no haya objeto Entrega.

- [ ] Escribir pruebas que exijan estado inicial Borrador y rechazo de prioridad 0, 4 y 1.5; comprobar el conjunto de estados válido. Ejecutarlas antes del cambio y confirmar que detectan la diferencia.
- [ ] Alinear el modelo Pedido con el esquema. Mantener las transiciones y sus restricciones en PedidosSQLite.
- [ ] Escribir pruebas para Confirmado → Programada, Despachado → En Camino y Entregado → Completada cuando exista ventana horaria. Para Borrador, Cancelado o ausencia de horario, devolver entrega=None; conservar siempre horario y observaciones en la cabecera. Este tratamiento de estados sin entrega es una propuesta de este plan.
- [ ] Ajustar obtener_pedido y la consulta de consola para conservar y mostrar observaciones aunque falten horarios. Si un ejemplo antiguo usa Asignado/En Camino como estados de Pedido, adaptarlo o retirarlo como ejemplo ejecutable.
- [ ] Ejecutar `python -m pytest tests/test_modelos.py -q`. Esperado: todas las pruebas pasan. Revisar diff y preparar commit de modelos.

## Tarea 3: Dejar una red de pruebas de negocio

**Archivos:** crear tests/test_pedidos.py y tests/test_main.py. Modificar repositorios solo si una prueba reproduce un defecto real.

**Interfaces:** usar crear_borrador, establecer_producto, confirmar, cancelar, asignar_vehiculo, despachar y entregar de PedidosSQLite; consultar stock y flota desde sus repositorios.

- [ ] Implementar `test_faltantes_conservan_borrador`: pedir 201 con 200 disponibles; exigir faltan=1, estado Borrador, ítems intactos y reservas=0.
- [ ] Implementar `test_cancelar_libera_reservas`: confirmar 2 de 200; cancelar; exigir reservado=0 y físico=200.
- [ ] Implementar `test_vehiculo_no_admite_dos_pedidos`: asignar un vehículo a un Confirmado y rechazar su asignación a otro sin modificar el segundo.
- [ ] Implementar `test_despacho_descuenta_una_vez`: despachar 2 de 200; exigir físico=198, pedido Despachado y vehículo En Ruta; repetir debe fallar conservando físico=198.
- [ ] Implementar `test_entrega_libera_vehiculo`: exigir pedido Entregado, vehículo Disponible y ningún pedido activo en el vehículo.
- [ ] Implementar `test_persistencia_y_demo_idempotente` con archivo temporal: completar el ciclo, cerrar, reabrir, conservar stock/estados y no duplicar datos iniciales. Probar el arranque con --db apuntando a esa ruta.
- [ ] Ejecutar `python -m pytest tests/test_modelos.py tests/test_pedidos.py tests/test_main.py -q`. Corregir solo fallos reproducidos y repetir las pruebas afectadas. Preparar commit de tests.

## Tarea 4: API mínima con contrato estable

**Archivos:** crear Backend/api.py y tests/test_api.py; actualizar requirements.txt. Reutilizar main.py, persistencia.py, pedidos.py y flota.py.

**Interfaces:** `create_app(ruta_db: str | Path | None = None) -> FastAPI` permite una base temporal en pruebas. `app = create_app()` sirve para Uvicorn. La ruta se elige por argumento, variable LOGISTICA_DB o RUTA_DB_POR_DEFECTO, en ese orden. Abrir y cerrar una conexión dentro de cada endpoint síncrono; no conservar una conexión global ni compartirla entre hilos. Inicializar demo al arrancar con una sesión separada que se cierre.

Contrato propuesto para que backend y frontend usen los mismos campos:

| Método y ruta | Entrada o resultado |
|---|---|
| GET /productos | Lista de id_producto, nombre, volumen_unitario, peso_unitario |
| POST /productos | Esos cuatro campos; crear catálogo sin ingreso implícito de stock |
| GET /depositos | Lista de id_deposito, nombre, ubicacion, capacidad_maxima |
| GET /stock | Filas por depósito/producto: id_deposito, id_producto, fisico, reservado, disponible; incluir parejas con cero para productos nuevos |
| POST /stock/ingresos | id_deposito, id_producto, cantidad entera positiva |
| GET /pedidos | Lista de pedidos; prioridad descendente y empate por creado_en/id_pedido |
| POST /pedidos | id_pedido, cliente, destino, prioridad, hora_inicio opcional, hora_fin opcional, observaciones opcional |
| GET /pedidos/{id} | Cabecera, estado, creado_en, vehiculo_asignado, volumen_total, productos y entrega opcional |
| PUT /pedidos/{id}/items | id_deposito, id_producto, cantidad; establece el total de esa pareja, no lo incrementa |
| POST /pedidos/{id}/confirmar | Devuelve pedido actualizado o faltantes |
| POST /pedidos/{id}/cancelar | Devuelve pedido actualizado |
| PUT /pedidos/{id}/vehiculo | patente; devuelve pedido actualizado |
| POST /pedidos/{id}/despachar | Devuelve pedido actualizado |
| POST /pedidos/{id}/entregar | Devuelve pedido actualizado |
| GET /vehiculos | patente, capacidad_maxima, estado, conductor_asignado, pedido_asignado, volumen_ocupado |
| GET /reportes/kpis | Opcional: pedidos_pendientes, vehiculos_asignados, productos_con_stock, pedidos_entregados |

Los ítems consultados conservan los campos del repositorio: id_deposito, id_producto, cantidad, producto y volumen_unitario. Cabecera incluye horario y observaciones incluso si entrega=None. Serializar explícitamente los campos públicos; no exponer conexiones ni objetos internos.

- [ ] Escribir tests HTTP antes de implementar cada grupo: alta/inventario, borrador/ítems, reserva/faltantes y flota/despacho/entrega. Usar `with TestClient(create_app(tmp_path / 'api.db')) as client` para activar arranque y cerrar recursos.
- [ ] Validar textos no vacíos, prioridad/cantidad enteras estrictas y medidas positivas finitas. Los horarios llegan juntos en HH:MM o ambos ausentes; reutilizar la validación del repositorio. Validación de entrada HTTP: 422; ValueError de negocio: 400; recurso pedido inexistente: 404 comprobado explícitamente; StockInsuficiente e IntegrityError: 409.
- [ ] Para errores de negocio usar detail con mensaje y, cuando corresponda, faltantes. Capturar StockInsuficiente antes que ValueError porque hereda de él. No transformar errores inesperados en una respuesta de éxito.
- [ ] Implementar las rutas sin duplicar SQL de transición. Usar sorted con una función de clave para ordenar la consulta de pedidos, como ejemplo real de transformación sin mutar la lista original.
- [ ] Montar Frontend con StaticFiles(html=True) al final de las rutas; /docs y los endpoints deben seguir accesibles. Resolver Frontend desde __file__, no desde el directorio de ejecución.
- [ ] Probar por HTTP el ciclo completo, un 409 con faltan=1, identificación duplicada, pedido inexistente, cantidad fraccionaria y despacho repetido sin doble descuento.
- [ ] Ejecutar `python -m pytest -q` y `python -m uvicorn Backend.api:app --host 127.0.0.1 --port 8000`. Verificar /docs, /index.html y recorrido completo por /docs antes de pasar a JavaScript. Preparar commit de API.

## Tarea 5: Gestión de productos y stock en la web

**Archivos:** crear Frontend/api.js; modificar Frontend/gestion.html y Frontend/gestion.js.

**Interfaces:** `apiFetch(path, options = {}) -> Promise<object | object[]>` usa las rutas anteriores y rechaza con Error que conserva faltantes cuando existan. Exponer el helper desde window para mantener scripts clásicos con defer y evitar agregar un sistema de módulos.

- [ ] Implementar apiFetch con JSON, comprobación de response.ok y mensajes legibles para errores de negocio, errores 422 y fallos de red. Agregar scripts defer, primero api.js y luego gestion.js.
- [ ] Mostrar catálogo y stock por depósito con físico, reservado y disponible. Alta con ID, nombre, volumen en m³ y peso en kg; ingreso de stock separado con depósito, producto y cantidad.
- [ ] Implementar búsqueda por ID/nombre usando filter sobre los datos reales. Quitar Categoría, Editar/Eliminar y pestañas sin operación; insertar datos con textContent.
- [ ] Desactivar el botón mientras se guarda y reactivarlo si falla. Preservar lo ingresado y mostrar error; actualizar tabla después de una respuesta exitosa.
- [ ] Verificar en navegador: crear producto nuevo, comprobar cero existencias, ingresar 5 unidades en D-001 y comprobar físico=5/reservado=0/disponible=5. Repetir ID y desconectar servidor: debe verse error sin anunciar guardado. Preparar commit de gestión.

## Tarea 6: Pedido y seguimiento completos en la web

**Archivos:** Frontend/cargas.html, Frontend/carga.js, Frontend/seguimiento.html, Frontend/seguimiento.js y ajustes mínimos en Frontend/styles.css.

**Interfaces:** reutilizar apiFetch y las respuestas de pedido de la tarea 4. Los selectores usan los IDs y patentes recibidos de la API, no los nombres de las opciones de muestra.

- [ ] Corregir la X suelta y los div de cargas.html. Agregar ID, cliente, destino, prioridad, horarios type=time y observaciones. Cargar depósitos, productos y vehículos desde la API.
- [ ] Implementar crear borrador y establecer cantidad por depósito/producto. Mostrar ID del pedido guardado, sus ítems y volumen total. Un borrador recuperable evita perder la operación si se recarga la página.
- [ ] Separar acciones: confirmar, asignar vehículo y despachar. Mostrar faltantes del 409 y permitir corregir cantidades mientras siga Borrador. Quitar el botón combinado Confirmar y Despachar.
- [ ] Mostrar capacidad en m³; peso solo informativo. Quitar precios, subtotales y chofer de texto libre: el conductor se consulta desde el vehículo de demo. Ofrecer cancelar solo en Borrador/Confirmado.
- [ ] En seguimiento, buscar por ID real y mostrar estado, destino, vehículo y etapas. Borrador/Cancelado tienen tratamiento propio; no marcar Cancelado como completado. Mostrar error si no existe.
- [ ] Agregar Marcar como entregado solo para Despachado y refrescar estado después del éxito. Proteger acciones contra doble clic; el servidor debe seguir rechazando repeticiones aunque se fuerce la llamada.
- [ ] Ensayar en navegador: crear producto, ingresar 5, pedir 6, recibir faltan=1, establecer 4, confirmar, comprobar físico=5/reservado=4/disponible=1, asignar vehículo, despachar, comprobar físico=1/reservado=0, buscar y entregar. Recargar y reiniciar servidor: el pedido debe seguir Entregado y el vehículo Disponible.
- [ ] Ejecutar `python -m pytest -q` después de cualquier cambio de backend. Preparar commit del circuito web.

## Tarea 7: Inicio opcional

**Archivos:** Frontend/index.html, Frontend/app.js y, si se incluye, GET /reportes/kpis en Backend/api.py con tests/test_api.py.

- [ ] Reemplazar app.js de ejemplo por indicadores y tabla de pedidos reales. Pendientes significa Borrador o Confirmado; asignados cuenta vehículos con pedido activo; productos con stock cuenta productos con stock físico total positivo; entregados cuenta pedidos Entregados.
- [ ] Mostrar nombres de estados reales y quitar alertas/destinos ficticios. Si se recorta esta tarea, dejar una portada con navegación y alcance real, sin métricas inventadas.
- [ ] Verificar que un pedido nuevo y uno entregado actualizan sus conteos. Preparar commit solo si queda margen después de asegurar tareas 1 a 6 y documentación.

## Tarea 8: Documentación, instalación y ensayo

**Archivos:** README.md, Informe.md, requirements.txt y .gitignore. Resolver la duplicación Backend/Informe.md dejando una única versión de referencia.

- [ ] Empezar el informe aunque el frontend siga en curso. Describir arquitectura real, flujo, reservas, transacciones y alcance. Evidencia de paradigmas: objetos/composición, secuencia de transiciones, sorted/filter funcionando y SQL con restricciones.
- [ ] Documentar límites: una entrega por pedido, un pedido activo por vehículo, depósitos/flota precargados en web, capacidad por volumen, sin rutas ni históricos con horas de eventos.
- [ ] Escribir README con versión de Python efectivamente probada, entorno virtual, `python -m pip install -r requirements.txt`, ejecución de consola/API, URL de inicio, pruebas y respaldo/selección de la base. Las versiones de requisitos deben ser las que pasaron instalación y pruebas, no versiones inventadas.
- [ ] Revisar `git diff --check`, `git status --short` y `python -m pytest -q`. Comprobar que los archivos necesarios estén incluidos y que ninguna base/caché se entregue por accidente.
- [ ] Con el código final guardado en commits, clonar la rama en otra carpeta y seguir solo el README usando una base vacía y un entorno nuevo. Debe arrancar, servir las páginas, completar el circuito y conservarlo al reiniciar.
- [ ] Ensayar dos veces el guion de la tarea 6 y preparar qué integrante explica cada paradigma. En los últimos 90 minutos, corregir solo bloqueos de entrega.
- [ ] Revisar el commit final. Crear etiqueta v1.0 y subir rama/etiqueta cuando el usuario decida hacer la entrega.

## Criterio de entrega

La versión web mínima está lista cuando otra persona puede instalarla desde cero, completar el circuito por navegador, ver errores de stock útiles, consultar el estado después de reiniciar y entender en el informe qué está implementado. El inicio con KPIs no es condición de cierre.

Si se activa la alternativa por consola, esos mismos requisitos operativos deben cumplirse por terminal, y README/informe/presentación deben declarar expresamente que la API o la conexión web quedaron pendientes. No presentar una maqueta como si estuviera conectada.
