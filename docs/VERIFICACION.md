# Verificación de la entrega mínima

Verificación inicial del 17 de noviembre de 2026 y actualización final del 18 de noviembre sobre la rama `desarrollo_minimo`, con Python 3.12.3 en Windows. La comprobación final previa a los commits aprobó los 290 casos de la suite completa.

## Resultados

| Comprobación | Resultado |
|---|---|
| Suite completa con Chromium (18/11) | 290 pruebas aprobadas: 271 de backend/consola/API y 19 de navegador |
| Backend/consola/API tras incorporar Prolog (19/11) | 274 pruebas aprobadas, con SWI-Prolog instalado; sin él, la prueba del motor real se omite |
| Backend/API en copia limpia y entorno virtual nuevo | 267 aprobadas; 13 pruebas de navegador excluidas explícitamente |
| Dependencias, `python -m pip check` | Sin incompatibilidades en ambos entornos |
| Sintaxis de los cinco scripts JavaScript, `node --check` | Correcta |
| Espacios y conflictos, `git diff --check` | Sin errores |
| Arranque de consola con SQLite en memoria | Inventario y flota cargados correctamente |
| Revisión independiente de código | Hallazgos reproducidos y corregidos con pruebas |
| Diseño en Chromium a 390 y 1280 píxeles | Sin desborde horizontal de página; tablas con desplazamiento propio |

La copia limpia contiene únicamente código, frontend, requisitos, documentación y pruebas. Se creó un entorno nuevo y se instalaron los requisitos. Se usó una exportación de fuentes porque clonar la rama antes de guardar los cambios en commits omitiría la implementación nueva.

La ampliación de escenarios, los defectos corregidos y la medición de cobertura están documentados en [Pruebas exhaustivas](PRUEBAS_EXHAUSTIVAS.md): 130 funciones/métodos ejercitados, 99,89% de líneas Python y 99,14% de ramas. Se comprobó mediante SHA256 que la base de trabajo no cambió durante las pruebas.

## Documentación del código

Se completaron docstrings PEP 257 de estilo Google en 30 módulos Python, 17 clases y 265 funciones/métodos del backend, ejemplos y tests. Ruff comprueba las reglas de documentación con la configuración de ruff.toml; sus dependencias se instalan con requirements-test.txt. Los cinco scripts del frontend incluyen JSDoc para módulos y funciones reutilizables.

La comparación del AST Python antes y después, excluyendo docstrings, confirmó instrucciones y firmas idénticas. Las inserciones JSDoc conservaron el JavaScript original al retirar los comentarios añadidos. Se comprobaron sintaxis JavaScript, estilo de docstrings, ejemplos JSON del README y hash de la base. OpenAPI expone descripciones para las 16 operaciones y los cuatro esquemas de entrada utilizados por las rutas; README.md aclara las limitaciones de sus esquemas automáticos de salida y los errores reales del servidor.

## Comportamientos cubiertos

- Estado inicial, prioridades, ventanas horarias y estados derivados de Entrega.
- Confirmación con faltantes sin perder el borrador ni reservar parcialmente.
- Cancelación y liberación de reservas; protección de mercadería reservada.
- Exclusión de dos pedidos activos en un vehículo.
- Despacho único, stock descontado y vehículo En Ruta.
- Rollback si falla una escritura durante el despacho.
- Entrega y liberación del vehículo.
- Persistencia de pedidos, reservas e ingresos al reabrir; datos de demo sin duplicación.
- Dos confirmaciones concurrentes sin sobreventa.
- Ingresos reintentados con la misma clave sin duplicar stock, incluso al perder la respuesta y recargar o reiniciar.
- Alta, consulta, cantidades inválidas, conflictos e identificadores inexistentes por HTTP.
- Compatibilidad de referencias con espacios registradas por consola.
- Migración aditiva con conservación de las observaciones históricas.
- Carga inicial desde schema.sql con tres productos, depósitos, conductores, vehículos, pedidos y sus ítems/existencias.
- Inicialización única: sin duplicación ni reposición de stock o productos borrados; bases con registros propios intactas.
- Carga inicial atómica, con rollback ante fallos y rechazo de llamadas dentro de una transacción ajena.
- Rechazo de volumen no finito antes de confirmar la transacción; conteos sin desborde de enteros.
- Circuito completo en Chromium desde alta de producto hasta entrega.
- Recuperación después de recargar, cancelación, pedido inexistente y ocultación del pedido anterior.
- Fallo de red con formulario recuperable y distinción entre ingreso confirmado y fallo de refresco.
- Texto con etiquetas HTML mostrado como texto; validación del formato de IDs nuevos.

## Espacio de los depósitos

La ampliación del 18 de noviembre de 2026 agrega en Gestión un resumen separado del inventario por producto. GET /depositos devuelve capacidad_maxima, volumen_ocupado y espacio_disponible en m³, calculados por el repositorio a partir del stock físico. El espacio libre se limita a cero ante diferencias de redondeo. Las reservas no liberan volumen; los despachos sí. La pantalla actualiza el resumen después de un ingreso y al cargar la página, y mantiene todos los depósitos visibles independientemente de los filtros de productos. Se verificó la vista en escritorio y móvil.

La suite ampliada aprueba 285 casos (271 de backend/consola/API y 14 de navegador). Los cinco casos nuevos cubren cálculo de volumen y capacidad, reserva/cancelación/despacho, depósito lleno, redondeo y actualización visual. La base de trabajo no se usa en estas pruebas.

## Ampliación: Nuevo pedido integrado

Cargas reúne Datos → Productos → Confirmación dentro de Nuevo pedido. Guardar datos y continuar muestra directamente los productos del borrador; Retomar un pedido existente queda en un desplegable separado. La URL conserva el pedido para recargar y el foco pasa al título de Productos después del alta. Confirmar permanece deshabilitado mientras no hay ítems. Las operaciones utilizan el pedido devuelto por la API; si falla la consulta posterior de flota, se muestra una advertencia conservando pedido y URL.

La suite actual aprueba 290 casos (271 de backend/consola/API y 19 de navegador). Los cinco casos agregados comprueban el recorrido integrado, persistencia al recargar, recuperación separada, continuidad sin consulta redundante, fallo de actualización de flota y descripción accesible correcta. Se revisaron capturas del flujo con productos en escritorio y móvil. El backend y la base de trabajo no se modificaron por este cambio de interfaz.

## Reproducir

Seguir README.md para crear el entorno e instalar los requisitos. Para la suite completa:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-browser.txt
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path (Get-Location) '.venv\browsers'
.\.venv\Scripts\python.exe -m playwright install chromium
$env:RUN_BROWSER_TESTS = '1'
.\.venv\Scripts\python.exe -m pytest -q
```

Sin Chromium, ejecutar `python -m pytest -m 'not browser' -q` usando el Python del entorno. Las pruebas usan bases temporales y detienen los servidores que crean.

## Límites de la comprobación

Después de la limpieza se incorporaron, a pedido del usuario, valores base automáticos en schema.sql. Backend/logistica.db contiene tres registros de cada entidad principal, tres filas de existencias y tres ítems de pedido. Los pedidos comienzan en Borrador y los vehículos están disponibles con conductor. La marca de inicialización impide repetir la carga al reabrir. Se verificaron integridad SQLite y claves foráneas, y se guardó un respaldo previo en .backups/. Las nuevas bases reciben los mismos valores automáticamente desde la API o consola. El SQL completo se ejecuta directamente solo sobre bases nuevas; las antiguas deben abrirse mediante la aplicación para migrar primero sus columnas.

Se probó en Windows/Python 3.12.3 y Chromium. No se probaron otros navegadores ni sistemas operativos. Las capturas y entornos de prueba son locales y están excluidos de Git. La base original quedó respaldada; no se utiliza como base de tests.

No incluye despliegue público, autenticación, cálculo de rutas, restricciones por peso ni funcionalidades excluidas del alcance que detalla el informe. La entrega se prepara en la rama desarrollo_minimo con código, pruebas, dependencias y documentación. La base SQLite, el entorno virtual, los respaldos y los resultados locales de pruebas quedan excluidos de Git; una instalación nueva crea su propia base con los valores iniciales.
