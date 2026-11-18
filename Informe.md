# Sistema de Gestión Logística y Distribución

Trabajo final del Grupo 5 de Programación III.

## Propósito y alcance implementado

La aplicación permite administrar productos y existencias por depósito, crear pedidos, reservar mercadería, asignar vehículos con conductor, despachar y registrar entregas. El circuito puede operarse desde una interfaz web local o desde un menú de consola. Los datos persisten en SQLite y se recuperan al reiniciar.

La versión concentra el desarrollo en un circuito logístico completo. La selección de depósito, productos y vehículo es manual. La prioridad ordena los pedidos en la consulta; no implementa un planificador de rutas ni garantiza ventanas horarias.

## Arquitectura

El frontend usa HTML, CSS y JavaScript sin framework. Las páginas Gestión, Cargas, Seguimiento e Inicio intercambian JSON con una API FastAPI. Uvicorn sirve la aplicación y los archivos estáticos desde el mismo origen. La consola usa directamente los mismos repositorios que la API.

El recorrido de una operación es interfaz → API → repositorio → SQLite. Las reglas de negocio permanecen en Python: modificar una pantalla no permite eludir las validaciones de stock o estado.

| Componente | Responsabilidad |
|---|---|
| Backend/modelos/ | Representar productos, depósitos, pedidos, entregas, vehículos y conductores |
| Backend/persistencia.py | Abrir SQLite, actualizar el esquema y administrar catálogo y existencias |
| Backend/pedidos.py | Coordinar estados, reservas, asignación, despacho y entrega |
| Backend/flota.py | Administrar vehículos, conductores y sus relaciones |
| Backend/api.py | Validar solicitudes HTTP, traducir errores y serializar resultados |
| Backend/main.py y consola.py | Arranque, datos iniciales y operación por terminal |
| Frontend/api.js | Comunicación HTTP y presentación de errores |
| Frontend/gestion.js, carga.js, seguimiento.js y app.js | Interacción y presentación de datos reales |

La API abre y cierra una conexión por solicitud. No comparte una conexión SQLite global entre hilos. La base predeterminada se ubica respecto de los archivos del programa y puede sustituirse por una ruta de demostración. El primer arranque de una base vacía carga los valores definidos en schema.sql: tres productos, depósitos, conductores, vehículos y pedidos en borrador con sus ítems y existencias. Un marcador persistente evita repetir la carga o reponer datos modificados. Una base con registros propios se conserva sin agregar ejemplos.

## Flujo y reglas de negocio

Un pedido inicia en Borrador. Sus ítems relacionan producto, depósito y cantidad entera positiva. Guardar una cantidad para la misma pareja reemplaza el total anterior. La prioridad admite 1 normal, 2 urgente y 3 crítica. Los horarios son opcionales; si se indican, deben formar una ventana HH:MM válida cuyo inicio preceda al fin.

Confirmar valida todo el pedido. Si falta mercadería, devuelve los faltantes y conserva el borrador sin reservar parcialmente. Si alcanza, cambia a Confirmado y sus ítems pasan a representar reservas activas. Un pedido vacío no se confirma.

Un Confirmado necesita un vehículo Disponible, con conductor asignado y capacidad suficiente para su volumen completo. Un vehículo admite un solo pedido activo. Despachar cambia el pedido a Despachado, descuenta el stock y deja el vehículo En Ruta en una misma transacción. Repetir el despacho se rechaza para evitar descuentos duplicados.

Entregar requiere un pedido Despachado y deja el vehículo Disponible. Cancelar solo está permitido antes del despacho: conserva el registro y libera reservas y ocupación del vehículo. Los pedidos confirmados no se editan; se cancelan y se crean nuevamente cuando corresponde.

## Stock y consistencia

El catálogo contiene volumen y peso unitarios. La cantidad física pertenece a la pareja producto/depósito y no al objeto de catálogo. Se distinguen stock físico, reservado y disponible. Disponible es físico menos reservado.

Las reservas se calculan desde los ítems de los pedidos Confirmados. No se mantiene una segunda tabla de reservas que pueda desincronizarse. Un retiro o traslado por consola no puede consumir unidades reservadas. Las reservas siguen ocupando espacio físico en el depósito.

Los ingresos HTTP admiten una clave de operación guardada junto con el movimiento en una sola transacción. La web conserva esa clave mientras la respuesta esté pendiente: reintentar la misma operación después de perder la respuesta no duplica las unidades. La consulta posterior de la tabla se distingue de la confirmación del ingreso.

SQLite aplica claves foráneas, unicidad y restricciones CHECK. Un índice único parcial impide que un vehículo figure en dos pedidos Confirmados o Despachados. Las escrituras usan BEGIN IMMEDIATE, y un error provoca rollback. Así se coordinan lecturas de disponibilidad y escrituras, incluso cuando dos solicitudes intentan confirmar al mismo tiempo.

Las bases anteriores reciben columnas de horario y observaciones mediante una migración aditiva. También se corrige el nombre histórico obvservaciones. Se conserva un respaldo antes de intervenir sobre la base local.

## Objetos y estado derivado

Pedido reúne sus ítems y, cuando hay ventana horaria y una etapa operativa de entrega, compone un objeto Entrega. Su estado se deriva del pedido: Confirmado corresponde a Programada, Despachado a En Camino y Entregado a Completada. Borrador y Cancelado no se presentan como entregas en curso. Las observaciones y horarios se conservan en la cabecera aunque no exista un objeto Entrega.

Los objetos devueltos por los repositorios son copias para consulta: modificar sus atributos no guarda cambios automáticamente. Las operaciones persistentes deben pasar por el repositorio correspondiente. Esto mantiene una única ruta para validar y actualizar los datos.

## Paradigmas de programación

| Paradigma o estilo | Evidencia concreta |
|---|---|
| Orientado a objetos | Clases Pedido, Producto, Vehiculo y Entrega; composición de Entrega en PedidosSQLite.obtener_pedido; repositorios que agrupan estado y operaciones |
| Imperativo | Secuencia de validación y actualizaciones de PedidosSQLite.despachar y entregar; coordinación explícita de operaciones en la consola |
| Funcional | sorted con una función lambda en el listado de pedidos de Backend/api.py crea una lista ordenada sin mutar la original; filter y map en Frontend/gestion.js y carga.js seleccionan y transforman colecciones |
| Declarativo | SELECT, JOIN y GROUP BY describen consultas; CHECK, claves foráneas e índice único parcial expresan restricciones del dominio en schema.sql y la migración |

Python concentra el modelado y las transacciones; JavaScript aporta eventos, asincronía e interacción con el DOM. El uso de filter o sorted constituye una aplicación de estilo funcional dentro de una aplicación multiparadigma, no una afirmación de que toda la solución sea funcional pura.

## Interfaz y manejo de errores

Las pantallas muestran datos de la API, incluidos los indicadores de pedidos pendientes, vehículos asignados, productos con stock y pedidos entregados. Los botones disponibles dependen del estado y se bloquean durante su operación para reducir envíos repetidos. El servidor vuelve a validar cada transición.

La API rechaza datos de entrada inválidos con 422, reglas de negocio incumplidas con 400, pedidos inexistentes con 404 y faltantes o conflictos con 409. Los faltantes incluyen producto, depósito y cantidades. La web presenta mensajes legibles y conserva el formulario ante errores de red. Los datos ingresados se insertan mediante textContent para mostrarlos como texto.

## Verificación

La carpeta tests contiene pruebas de modelos, inventario y reservas, transacciones, migración, consola, API y navegador. Se usan SQLite real en memoria o archivos temporales. Se verifican faltantes sin reservas parciales, cancelación, vehículo ocupado, despacho único, rollback, conservación al reiniciar y confirmaciones concurrentes sin sobreventa.

Las pruebas en Chromium recorren alta de producto, ingreso de stock, pedido con faltante, corrección, confirmación, asignación, despacho y entrega. También comprueban recarga, búsqueda inexistente, cancelación, fallos de red, texto con etiquetas HTML y ancho móvil. README.md documenta los comandos reproducibles y la instalación del navegador opcional.

## Limitaciones y trabajo futuro

La capacidad se valida por volumen en metros cúbicos. El peso en kilogramos es informativo. Cada vehículo transporta un pedido activo; no se consolidan recorridos. La ventana horaria se valida y muestra, pero no se calcula un horario de llegada.

Depósitos, vehículos y conductores pueden registrarse desde la consola; la web utiliza los registros existentes, ingresados manualmente o provistos por la inicialización de schema.sql. Quedan pendientes las altas web de esas entidades, la edición de cabeceras y eliminación de ítems desde la web, bajas de catálogo, restricciones por peso, optimización de rutas, entregas parciales, devoluciones, estadísticas avanzadas y registro histórico de horas de transición.

La aplicación está orientada a una demostración y operación local. No incorpora cuentas de usuario, autenticación ni despliegue público. Las instrucciones de instalación, operación y demostración se encuentran en README.md.
