# Verificación ampliada de funciones

Pruebas realizadas en Windows, Python 3.12.3 y Chromium. La ampliación del 18 de noviembre de 2026 aprobó **290 casos: 271 de backend/consola/API y 19 de navegador**. El 19 de noviembre se sumaron tres pruebas de la recomendación con Prolog (una exige SWI-Prolog instalado) y la suite de backend/consola/API quedó en 274 casos; las de navegador no se volvieron a ejecutar, sin fallos, errores ni pruebas omitidas. La verificación anterior, del 17 de noviembre, había aprobado 280 casos; una copia independiente con su entorno virtual ejecutó entonces 267 pruebas de backend/consola/API, con las 13 de navegador excluidas explícitamente.

## Cobertura medida

- Líneas Python ejecutables: 910/911 (**99,89%**).
- Ramas: 230/232 (**99,14%**).
- Medición combinada de Coverage: **99,74%**, frente al 74% inicial.
- Se ejercitó la entrada de **130 funciones y métodos** identificados en el backend mediante AST y líneas ejecutadas. Esto registra ejecución de cada función, no todas las combinaciones posibles de sus entradas.

La cobertura corresponde al código Python de Backend, con instrumentación de subprocesos de consola. Los escenarios JavaScript se verificaron mediante Chromium y sus aserciones, sin asignarles un porcentaje de cobertura de código.

| Archivo | Cobertura combinada de líneas y ramas |
|---|---|
| Backend/api.py | 100,00% |
| Backend/consola.py | 100,00% |
| Backend/flota.py | 100,00% |
| Backend/main.py | 100,00% |
| Backend/modelos/conductor.py | 100,00% |
| Backend/modelos/deposito.py | 100,00% |
| Backend/modelos/entrega.py | 100,00% |
| Backend/modelos/pedido.py | 100,00% |
| Backend/modelos/productos.py | 100,00% |
| Backend/modelos/validaciones.py | 100,00% |
| Backend/modelos/vehiculo.py | 98,53% |
| Backend/pedidos.py | 99,05% |
| Backend/persistencia.py | 100,00% |

Quedan dos ramas defensivas sin ejercitar: liberar un vehículo que tuviera varios pedidos en su lista de simulación y detectar un conductor no habilitado después de obtener el estado Asignado derivado del vínculo. Las operaciones válidas limitan el vehículo a un pedido y derivan ese estado al consultar al conductor. Esas comprobaciones permanecen en el código.

## Casos por archivo

Cada parametrización cuenta como un caso porque comprueba una entrada o una combinación de estado y operación distinta.

| Archivo | Casos aprobados |
|---|---|
| test_api.py | 29 |
| test_api_limites.py | 40 |
| test_browser.py | 19 |
| test_concurrencia.py | 2 |
| test_consola.py | 18 |
| test_datos_base.py | 8 |
| test_flota.py | 12 |
| test_inventario.py | 46 |
| test_main.py | 6 |
| test_modelos.py | 15 |
| test_modelos_completos.py | 32 |
| test_pedidos.py | 12 |
| test_transiciones.py | 51 |

## Áreas verificadas

| Área | Escenarios |
|---|---|
| Inventario | Altas, duplicados, medidas finitas, enteros fuera de rango, stock cero, ingresos/retiros, faltantes, traslados, capacidad y rollback, copias de consulta y totales grandes |
| Flota | Altas y listados, conductores inactivos/ocupados, asignación única, mantenimiento, estados, recursos inexistentes, liberación y protección de pedidos activos |
| Pedidos | Matriz de 40 combinaciones entre cinco estados y ocho operaciones, edición de borrador, reemplazo/eliminación de ítems, prioridad y cabecera, capacidad con conductor válido, liberación de vehículo y entrega histórica sin vehículo |
| Varios depósitos | Faltante en el segundo ítem sin reserva parcial; corrección; reserva de ambos ítems; descuento en ambos depósitos y entrega |
| Transacciones | Fallo de despacho con reversión de todos los cambios, carga SQL fallida y reintento, migración incompatible conservando registros |
| Inicio de base | SQL directo y arranque de consola/API, tres registros por entidad, inicialización única, eliminación sin reposición y conservación de bases propias |
| Concurrencia | Ocho inicializaciones simultáneas, dos confirmaciones sobre el mismo stock, dos pedidos compitiendo por un vehículo y reintentos con la misma clave de ingreso |
| Modelos | Métodos de productos, depósitos, conductores, entregas, pedidos y vehículos; entradas inválidas, cambios de estado, notas e información de consulta |
| Consola | Menús de inventario/flota/pedidos, consultas vacías, detalle, opcionales, coma decimal, entradas inválidas, /volver, EOF, Ctrl+C y errores de SQLite |
| HTTP | Todas las rutas, 400/404/409/422, JSON inválido, campos extra, límites de texto, tipos estrictos, referencias, stock por depósito y orden por prioridad |
| Texto y archivos | Datos con sintaxis SQL tratados como texto, HTML mostrado sin ejecutarse, backend/DB/Git fuera del directorio publicado |
| Navegador | Circuito completo, filtros, navegación por pedido, recarga, cancelación, inexistente, doble envío, botones según estado, duplicados, fallos de red y respuesta inválida, escritorio y móvil |
| Espacio de depósitos | Suma física de todos los productos, depósitos vacíos y llenos, redondeo decimal, ingreso, reserva/cancelación sin liberar espacio, despacho; tabla separada de filtros, actualización y lectura en móvil |
| Nuevo pedido integrado | Datos, productos y confirmación sin buscar el código; foco en productos, confirmación vacía bloqueada, recarga, pedido nuevo, recuperación separada, respuesta del alta sin consulta adicional, conservación de URL ante fallo de flota y descripción accesible de confirmación |

## Defectos reproducidos y corregidos

1. El modelo Producto aceptaba deltas fraccionarios/booleanos y stock inicial inválido. Ahora exige unidades enteras y un stock inicial no negativo.
2. El modelo Pedido admitía ítems inválidos, volumen no finito y modificaciones después de confirmar. Se valida antes de modificar su colección o volumen.
3. El modelo Deposito aceptaba medidas negativas, booleanas o no finitas en sus operaciones de espacio y capacidad. Comparte la validación de medidas con Pedido y el repositorio.
4. La simulación de Vehiculo asignaba sin conductor, marcaba una liberación previa al despacho como entrega y podía conservar En Ruta al liberar. Se verifican conductor y etapa correspondiente, y se recupera la disponibilidad.
5. Las medidas enteras grandes generaban OverflowError al enviarse a SQLite aunque cabían como REAL. Se convierten a float después de comprobar su finitud; los valores que exceden el rango numérico se rechazan con ValueError.

Cada corrección quedó precedida por una prueba que fallaba con el comportamiento anterior y luego pasó. Una revisión independiente también detectó pruebas que mezclaban motivos de rechazo o no incluían múltiples ítems; se separaron los escenarios.

## Conservación de datos

Se comparó el SHA256 de Backend/logistica.db antes y después de las pruebas: coincidió. Los valores iniciales de trabajo quedaron intactos. Todos los escenarios de escritura usan SQLite en memoria o archivos temporales, y los servidores de pruebas se detienen al finalizar.

## Reproducción

Desde la raíz del proyecto, seguir README.md para instalar Python y el entorno. Para incluir navegador y cobertura:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-test.txt
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path (Get-Location) '.venv\browsers'
.\.venv\Scripts\python.exe -m playwright install chromium
$env:RUN_BROWSER_TESTS = '1'
.\.venv\Scripts\python.exe -m coverage erase
.\.venv\Scripts\python.exe -m coverage run -m pytest -q --junitxml=test-results/junit.xml
.\.venv\Scripts\python.exe -m coverage combine
.\.venv\Scripts\python.exe -m coverage report
.\.venv\Scripts\python.exe -m coverage html
```

El reporte HTML queda en test-results/coverage-html/index.html. Los resultados JUnit, capturas y datos de cobertura quedan en test-results/, excluido de Git. Para backend sin navegador: `python -m pytest -m 'not browser' -q`, usando el Python del entorno.

## Alcance de la conclusión

Los casos descritos pasaron en Windows/Python 3.12.3 y Chromium. Las pruebas no constituyen una verificación de otros navegadores, otros sistemas operativos, despliegue público ni carga sostenida de producción. No se realizaron commits ni push.
