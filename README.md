# Gestión logística y distribución

Trabajo final del Grupo 5 de Programación III. Aplicación local para gestionar productos y stock por depósito, preparar pedidos, reservar mercadería, asignar vehículos, despachar y registrar entregas. La web y la consola usan las mismas reglas de negocio y SQLite.

El circuito principal es **Borrador → Confirmado → Despachado → Entregado**. Un pedido puede cancelarse antes del despacho. Confirmar reserva stock; despachar lo descuenta; entregar libera el vehículo. La capacidad se controla por volumen en m³ y el peso se registra como dato informativo en kg.

## Arquitectura

El navegador ejecuta JavaScript y envía JSON a FastAPI. La API delega las reglas de negocio en `InventarioSQLite`, `PedidosSQLite` y `FlotaSQLite`, que comparten transacciones SQLite. La consola utiliza esos mismos repositorios directamente.

Los objetos de dominio devueltos por los repositorios son copias de consulta. Cambiar sus atributos o usar los métodos de simulación en memoria no guarda cambios automáticamente. Las operaciones persistentes se realizan mediante los repositorios, la consola o la API.

## Instalación en Windows

Estos pasos permiten ejecutar la **interfaz web** en tu computadora. Hacelos en orden; esperá a que termine cada comando antes de pegar el siguiente. La instalación de dependencias se hace una sola vez por computadora.

### 1. Instalar los requisitos

- **Python 3.12**. El proyecto se verificó con Python 3.12.3. Si no lo tenés, podés descargar el [instalador de Python 3.12.10](https://www.python.org/downloads/release/python-31210/), eligiendo **Windows installer (64-bit)** para una PC Windows x64. En el instalador, marcá **Add python.exe to PATH** y conservá el lanzador `py`.
- **Git**, si vas a clonar el repositorio. Se descarga desde [Git para Windows](https://git-scm.com/install/windows). También podés descargar el proyecto como ZIP, como se explica en el paso siguiente.
- **Conexión a Internet** para descargar el proyecto y sus dependencias.

Después de instalar Python y Git, cerrá y volvé a abrir PowerShell. Comprobá Python:

```powershell
py -3.12 --version
```

Debe mostrar `Python 3.12.x`. Si vas a usar Git, comprobá también:

```powershell
git --version
```

### 2. Descargar el proyecto desde main

**Si todavía no tenés el proyecto:** abrí PowerShell en la carpeta donde quieras guardarlo y ejecutá:

```powershell
git clone --branch main --single-branch https://github.com/sarrgyy/TPF-Grupo5-ProgramacionIII-ICOMP.git
Set-Location TPF-Grupo5-ProgramacionIII-ICOMP
```

El primer comando descarga el proyecto; el segundo entra en su carpeta.

**Si ya lo habías clonado:** con tus cambios propios guardados, abrí PowerShell dentro del repositorio y actualizá `main`:

```powershell
git switch main
git pull --ff-only origin main
```

Si Git avisa que hay cambios locales pendientes, guardalos antes de actualizar; no hace falta borrar tu carpeta ni tu base de datos.

**Alternativa sin Git:** abrí el [repositorio en GitHub](https://github.com/sarrgyy/TPF-Grupo5-ProgramacionIII-ICOMP), seleccioná la rama **main** y elegí **Code → Download ZIP**. Extraé el ZIP completo antes de continuar.

### 3. Abrir PowerShell en la carpeta correcta

Todos los comandos siguientes se ejecutan en la **raíz del proyecto**, donde están `README.md`, `requirements.txt`, `ejecutar.py` y las carpetas `Backend` y `Frontend`.

Si usaste los comandos de clonado del paso 2, ya estás en esa carpeta. Si descargaste un ZIP o cerraste la terminal, abrí la carpeta del proyecto en el Explorador de archivos; en su barra de direcciones escribí `powershell` y presioná Enter.

Para comprobar la ubicación:

```powershell
Test-Path .\requirements.txt
```

Debe responder `True`. Si responde `False`, entrá en la carpeta que contiene ese archivo antes de continuar.

### 4. Crear el entorno e instalar las dependencias

Ejecutá estas dos líneas, una por vez:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

La primera crea `.venv`, una carpeta con el entorno Python del proyecto. La segunda instala las dependencias; puede tardar unos minutos. Cuando vuelva a aparecer el indicador de PowerShell, podés continuar.

Usamos directamente el ejecutable de `.venv`: **no hace falta activar el entorno, ejecutar Activate.ps1 ni cambiar la política de PowerShell**. Si ya creaste ese entorno en esta computadora, podés reutilizarlo e instalar las dependencias con la segunda línea.

### 5. Iniciar el servidor web

Desde la misma carpeta, ejecutá:

```powershell
.\.venv\Scripts\python.exe -m uvicorn Backend.api:app --host 127.0.0.1 --port 8000
```

Dejá esa terminal abierta. Cuando aparezcan `Application startup complete` y `Uvicorn running on http://127.0.0.1:8000`, el servidor está listo. Que la terminal quede ocupada en este punto es normal: está atendiendo la aplicación.

### 6. Abrir y usar la aplicación

Abrí Chrome, Edge o Firefox y entrá a **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**. Desde ahí podés recorrer Inicio, Gestión, Cargas y Seguimiento. La documentación interactiva de la API está en [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

Usá esa dirección del navegador; abrir los HTML con doble clic no inicia el servidor. `127.0.0.1` indica tu propia computadora: cada compañero debe iniciar su servidor para usar su copia del proyecto.

La base SQLite y los datos de ejemplo se crean automáticamente en el primer arranque. Los cambios que hagas se conservan al cerrar y volver a abrir el programa.

### 7. Detenerlo y volver a usarlo otro día

Para detener el servidor, volvé a su terminal y presioná **Ctrl+C**.

Para abrirlo nuevamente, entrá en la carpeta del proyecto, abrí PowerShell y repetí **solo el comando del paso 5**; después abrí la dirección del paso 6. La creación de `.venv` se hace una sola vez. Si descargás una actualización que cambie los requisitos, volvé a ejecutar la instalación de dependencias del paso 4.

### Problemas frecuentes

| Problema | Qué hacer |
|---|---|
| `py` no se reconoce o no encuentra Python 3.12 | Revisá la instalación de Python 3.12 y volvé a abrir PowerShell. Si `python --version` muestra `Python 3.12.x`, podés usar `python -m venv .venv` en el paso 4. |
| No encuentra `requirements.txt` o `Backend.api` | Revisá la carpeta de la terminal con el paso 3: tiene que ser la raíz del proyecto. |
| No encuentra `.venv\Scripts\python.exe` | Completá la creación del entorno del paso 4 y comprobá que estás en la carpeta correcta. Cada compañero debe crear su propio entorno. |
| Aparece `No module named uvicorn` | Ejecutá `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` y esperá a que termine sin errores. |
| El puerto 8000 está ocupado o aparece `WinError 10048` | Si ya tenés otro servidor del proyecto abierto, detenelo con Ctrl+C. Como alternativa, cambiá `--port 8000` por `--port 8001` y entrá a `http://127.0.0.1:8001/`. |
| El navegador no puede conectarse | Confirmá que el servidor del paso 5 siga abierto, que no haya terminado con un error y que estés usando el mismo puerto en la dirección del navegador. |
| La pantalla muestra una versión anterior | Recargá con **Ctrl+F5** después de actualizar el proyecto. |

En Linux/macOS el ejecutable equivalente del entorno es `.venv/bin/python`; los pasos anteriores están escritos para PowerShell en Windows.

## Datos iniciales de la aplicación

El primer arranque inicializa una base vacía con tres productos, depósitos, conductores, vehículos y pedidos en borrador. Los vehículos ya tienen conductor y los pedidos tienen un ítem cada uno. Los valores se definen al final de `Backend/schema.sql`. Los siguientes arranques conservan tus cambios: no duplican registros ni reponen stock.

| Producto | Depósito | Stock inicial |
|---|---|---|
| PRD-1 · Pantalón | D-001 · Centro | 200 |
| PRD-2 · Campera | D-002 · Melipal | 100 |
| PRD-3 · Remera | D-003 · Dina Huapi | 300 |

Los pedidos P-001, P-002 y P-003 están listos para practicar confirmación, asignación, despacho y entrega. Todavía no reservan mercadería porque comienzan en Borrador. Los vehículos AB123CD, EF456GH e IJ789KL están disponibles con conductores asignados.

En **Gestión**, la sección **Espacio de los depósitos** muestra una fila por depósito con su capacidad total, volumen ocupado y espacio disponible, en m³. Es independiente de los filtros de productos. El volumen ocupado suma `stock físico × volumen unitario` de todos los productos del depósito; las reservas siguen ocupando lugar hasta el despacho. El resumen se actualiza al ingresar mercadería y al cargar o recargar la página. Los ingresos que superan la capacidad se rechazan sin modificar el stock.

## Consola y ejemplo

El atajo `ejecutar.py` inicia el mismo menú que `python -m Backend.main` y acepta los mismos argumentos, como `--db` y `--resumen`:

```powershell
.\.venv\Scripts\python.exe ejecutar.py
```

```powershell
.\.venv\Scripts\python.exe -m Backend.main
.\.venv\Scripts\python.exe -m Backend.main --resumen
.\.venv\Scripts\python.exe -m ejemplos.simulacion_en_memoria
```

En el menú, `0` vuelve o sale y `/volver` cancela un formulario. El ejemplo utiliza SQLite en memoria y no modifica los datos habituales.

## Datos y respaldos

La base predeterminada de ambos modos es `Backend/logistica.db`, ubicada respecto del código. Se crea automáticamente; no se incluye en Git. El arranque agrega las columnas de horario/observaciones que faltan en versiones anteriores y corrige el nombre histórico `obvservaciones`, conservando registros. La carga inicial se registra en la tabla `inicializaciones` y es transaccional. Si ya hay datos propios, no agrega los ejemplos ni los reemplaza. Las conexiones directas a los repositorios preparan el esquema; los arranques de API y consola ejecutan además la inicialización. Ejecutar el schema completo sobre una base nueva también carga los valores.

Antes de probar cambios sobre datos importantes, detener el servidor y la consola y copiar la base a una carpeta de respaldo. No borrar la base para actualizar el código. Los respaldos locales pueden guardarse en `.backups/`, que está excluido de Git.

Para una demo independiente, seleccionar otra base sin tocar la habitual:

```powershell
$env:LOGISTICA_DB = Join-Path (Get-Location) 'demo.db'
.\.venv\Scripts\python.exe -m uvicorn Backend.api:app --host 127.0.0.1 --port 8000
```

La base independiente recibe los mismos valores iniciales la primera vez. La consola selecciona esa misma base con `--db demo.db`. Para volver al archivo predeterminado en la API, detener el servidor y ejecutar `Remove-Item Env:LOGISTICA_DB -ErrorAction SilentlyContinue`. La carpeta de una ruta personalizada debe existir. La API necesita una base de archivo; `:memory:` se usa en repositorios, consola y ejemplo, no como LOGISTICA_DB.

## Guion de demostración

Para este guion, usar la base de demostración separada del apartado anterior, que incluye los tres depósitos y la flota inicial.

En **Cargas**, el bloque **Nuevo pedido** reúne los pasos **Datos → Productos → Confirmación**. Completá los datos y elegí **Guardar datos y continuar**: el borrador se guarda y la pantalla abre directamente los productos, sin volver a escribir su código. Agregá las cantidades y confirmá desde el mismo bloque. La confirmación se habilita al tener al menos un producto. La URL conserva el pedido para retomar el avance al recargar; **Crear otro pedido** abre un formulario nuevo sin borrar el anterior. Para abrir un pedido ya existente, usá el desplegable separado **Retomar un pedido existente** y su botón **Abrir pedido**.

1. En **Gestión**, registrar `DEMO-PROD`, con volumen 0.1 m³ y peso 1 kg.
2. Ingresar 5 unidades en Depósito Centro.
3. En **Cargas**, crear `DEMO-PED` indicando cliente y destino. Los horarios son opcionales, pero deben completarse ambos y el inicio debe ser anterior al fin.
4. Agregar 6 unidades de DEMO-PROD desde Centro. Confirmar: debe informar que falta 1 y conservar el borrador.
5. Guardar cantidad total 4 para la misma pareja producto/depósito. Confirmar: físico 5, reservado 4 y disponible 1.
6. Asignar un vehículo con conductor y volumen suficiente. Despachar: físico 1 y reservado 0.
7. Abrir **Ver seguimiento** y **Marcar como entregado**. El vehículo queda disponible.
8. Recargar o reiniciar y buscar DEMO-PED: sigue Entregado. Inicio refleja el pedido y los indicadores reales.

Los IDs nuevos de productos y pedidos creados desde la web/API admiten letras sin acentos, números, guion y guion bajo. Las referencias a registros existentes también admiten espacios, incluidos los registros cargados por consola. Si se repite la demo, usar IDs nuevos o una base de demostración diferente. La cantidad guardada reemplaza el total del producto en ese depósito; no se suma a la anterior. Un pedido confirmado ya no admite modificación de ítems: puede cancelarse antes del despacho y crearse otro.

### Estados y acciones del pedido

| Estado | Acción siguiente | Efecto sobre stock y vehículo |
|---|---|---|
| Borrador | Agregar productos y confirmar | Los ítems aún no reservan stock |
| Confirmado | Asignar vehículo y despachar; también puede cancelarse | El stock está reservado; el vehículo asignado queda ocupado por ese pedido |
| Despachado | Abrir Seguimiento y marcar como entregado | El stock físico ya se descontó y el vehículo está En Ruta |
| Entregado | Consultar el pedido y su seguimiento | El vehículo queda disponible |
| Cancelado | Crear otro pedido si se necesita una nueva carga | Se liberan reservas y asignaciones anteriores |

Las acciones de Cargas se ocultan cuando no corresponden al estado actual. El paso Confirmación y despacho puede quedar sin botones en pedidos Despachados, Entregados o Cancelados. La entrega de un pedido Despachado se registra en Seguimiento.

### Capacidad del transporte

El volumen del pedido suma `cantidad × volumen unitario` de todos sus ítems, incluso si provienen de distintos depósitos. Se compara con la capacidad máxima del vehículo al asignarlo y se vuelve a validar antes de despachar. Si el pedido no entra, se rechaza la operación con el mensaje «El vehículo no tiene capacidad para todo el pedido». También se exige vehículo disponible, conductor habilitado y ausencia de otro pedido activo. Cada vehículo atiende un pedido activo; el peso es informativo y no limita la carga.

La pantalla utiliza el pedido devuelto por las operaciones de guardado. Si una consulta posterior de flota falla, muestra una advertencia y conserva el pedido guardado y su URL para retomarlo al recargar.

### Ingresos de mercadería y reintentos

Los ingresos web envían una clave de operación persistida en SQLite. La pestaña conserva una sola operación pendiente. Si se pierde la respuesta del servidor, reintentar los mismos datos en esa pestaña, incluso después de recargar, antes de enviar otro ingreso distinto: así se conserva la clave y no vuelve a sumar el ingreso. Si el ingreso fue confirmado pero falla la actualización de la tabla, se muestra esa diferencia y se vacía la cantidad. Para clientes externos de la API, el encabezado opcional `Idempotency-Key` habilita la misma protección; reutilizar una clave con otros datos devuelve 409. Un reintento válido devuelve el stock físico actual, no una copia del contador de la respuesta original.

## API HTTP

Las rutas usan el mismo servidor que las páginas. Los campos y tipos de entrada, encabezados y descripciones de cada operación se consultan en `/docs`; la especificación JSON está en `/openapi.json`. El contrato de salida y errores se detalla a continuación.

| Método | Ruta | Operación |
|---|---|---|
| GET / POST | `/productos` | Consultar catálogo / registrar producto sin stock implícito |
| GET | `/depositos` | Consultar depósitos, capacidad total, volumen ocupado y espacio disponible en m³ |
| GET | `/stock` | Consultar físico, reservado y disponible por depósito/producto |
| POST | `/stock/ingresos` | Ingresar unidades; admite `Idempotency-Key` |
| GET / POST | `/pedidos` | Listar por prioridad / crear borrador |
| GET | `/pedidos/{identificador}` | Consultar cabecera, ítems y entrega derivada |
| PUT | `/pedidos/{identificador}/items` | Establecer el total de una pareja producto/depósito |
| POST | `/pedidos/{identificador}/confirmar` | Reservar todos los ítems o informar faltantes |
| PUT | `/pedidos/{identificador}/vehiculo` | Asignar vehículo con conductor y capacidad |
| POST | `/pedidos/{identificador}/despachar` | Descontar stock y dejar el vehículo En Ruta |
| POST | `/pedidos/{identificador}/entregar` | Finalizar el pedido y liberar vehículo |
| POST | `/pedidos/{identificador}/cancelar` | Cancelar antes del despacho y liberar reservas |
| GET | `/vehiculos` | Consultar estado, conductor y pedido activo |
| GET | `/reportes/kpis` | Consultar los cuatro indicadores de Inicio |

Crear producto o pedido responde con 201. Las consultas y operaciones restantes responden con 200. Los errores de negocio usan `detail.mensaje`; un faltante incluye además `detail.faltantes` con producto, depósito y cantidades.

OpenAPI genera los esquemas de entrada a partir de Pydantic. Las respuestas exitosas se devuelven como diccionarios o listas sin modelos de salida, por lo que su esquema automático puede aparecer como `{}`. Swagger también conserva la descripción 422 predeterminada del framework; la aplicación la reemplaza por el objeto `detail.mensaje` mostrado aquí. Los errores de negocio 400/404/409 de la tabla corresponden al comportamiento del servidor y no aparecen necesariamente enumerados en cada operación de Swagger.

| Código | Significado |
|---|---|
| 400 | La operación incumple una regla de negocio |
| 404 | El pedido solicitado no existe |
| 409 | Stock insuficiente, identificador repetido o conflicto de datos |
| 422 | El cuerpo, tipo o límite de un campo es inválido |

Ejemplo de respuesta al crear un borrador, antes de agregar ítems:

```json
{
  "id_pedido": "DEMO-PED",
  "cliente": "Cliente de ejemplo",
  "destino": "Centro, Bariloche",
  "prioridad": 1,
  "estado": "Borrador",
  "creado_en": "2026-11-17 12:00:00",
  "vehiculo_asignado": null,
  "volumen_total": 0.0,
  "hora_inicio": null,
  "hora_fin": null,
  "observaciones": null,
  "productos": [],
  "entrega": null
}
```

`creado_en` representa la fecha y hora UTC de SQLite. El ejemplo ilustra el formato; el servidor completa su valor al crear el pedido. Cuando hay ítems, cada uno incluye `id_deposito`, `id_producto`, `cantidad`, `producto` y `volumen_unitario`.

Un error 404 de pedido tiene esta forma:

```json
{"detail": {"mensaje": "No existe el pedido solicitado."}}
```

Un error 409 por stock insuficiente agrega los faltantes:

```json
{
  "detail": {
    "mensaje": "No se confirmó el pedido. PRD-1 en D-001: faltan 1 unidades (solicitadas 2, disponibles 1)",
    "faltantes": [{
      "id_deposito": "D-001",
      "id_producto": "PRD-1",
      "solicitadas": 2,
      "disponibles": 1,
      "faltan": 1
    }]
  }
}
```

## Pruebas

Backend, modelos, persistencia, consola, migraciones y API:

```powershell
.\.venv\Scripts\python.exe -m pytest -m 'not browser' -q
.\.venv\Scripts\python.exe -m pip check
```

Las pruebas crean bases temporales y no usan la base de trabajo. Incluyen faltantes sin reservas parciales, cancelación, reservas protegidas, vehículo ocupado, rollback, despacho repetido, concurrencia y reapertura.

La última verificación funcional aprobó **290 casos: 271 de backend/consola/API y 19 de navegador**. La cobertura Python fue **99,89% de líneas y 99,14% de ramas**, con las 130 funciones y métodos identificados ejercitados. Los resultados y los límites de la medición están en [Pruebas exhaustivas](docs/PRUEBAS_EXHAUSTIVAS.md).

Para verificar también la web en Chromium sin interfaz visible:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-browser.txt
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path (Get-Location) '.venv\browsers'
.\.venv\Scripts\python.exe -m playwright install chromium
$env:RUN_BROWSER_TESTS = '1'
.\.venv\Scripts\python.exe -m pytest -q
```

Las pruebas de navegador arrancan y detienen su propio servidor, usan una base temporal y comprueban el circuito completo, recarga, cancelación, errores de red, texto seguro y ancho móvil. Sin RUN_BROWSER_TESTS=1 esas pruebas se omiten explícitamente. Si otro entorno restringe sockets locales o el lanzamiento de Chromium, hay que habilitar esas capacidades para ejecutar las pruebas HTTP/navegador.

## Pruebas ampliadas y cobertura

La verificación ampliada y las correcciones detectadas están en [Pruebas exhaustivas](docs/PRUEBAS_EXHAUSTIVAS.md). Para medir cobertura, instalar `requirements-test.txt`, habilitar RUN_BROWSER_TESTS como en el apartado anterior y ejecutar:

```powershell
.\.venv\Scripts\python.exe -m coverage erase
.\.venv\Scripts\python.exe -m coverage run -m pytest -q
.\.venv\Scripts\python.exe -m coverage combine
.\.venv\Scripts\python.exe -m coverage report
.\.venv\Scripts\python.exe -m coverage html
```

El detalle queda en `test-results/coverage-html/index.html`. La cobertura mide Python; las pruebas de navegador verifican los comportamientos de las pantallas.

## Documentación del código Python

Las docstrings siguen [PEP 257](https://peps.python.org/pep-0257/) con secciones del [estilo Google](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings). Están escritas en español y usan comillas triples dobles, un resumen inicial y, cuando corresponde, `Args`, `Returns`, `Yields`, `Raises` y `Attributes`.

Los módulos explican su responsabilidad; las clases describen sus datos y el alcance de sus operaciones; las funciones y métodos documentan parámetros, retornos, unidades y errores relevantes. Los tests describen el comportamiento comprobado; sus helpers y fixtures explican los recursos temporales que preparan. El SQL mantiene comentarios sobre restricciones, migraciones y carga inicial.

Los cinco scripts de JavaScript usan comentarios JSDoc para sus módulos y funciones reutilizables, con parámetros y promesas de retorno cuando corresponde. Las convenciones de Python se aplican a los archivos `.py`.

Para comprobar el estilo después de instalar `requirements-test.txt`:

```powershell
.\.venv\Scripts\ruff.exe check Backend ejemplos tests
```

`ruff.toml` configura las reglas de docstrings con convención Google. En los casos de prueba no se exige repetir en `Args` cada fixture inyectada por pytest. Ruff se utiliza aquí para documentación; esta configuración no representa una auditoría completa de todas las reglas de PEP 8.

Las docstrings de los endpoints se publican también en `/docs`. Para consultar la documentación de una clase desde Python:

```powershell
.\.venv\Scripts\python.exe -c "from Backend.pedidos import PedidosSQLite; help(PedidosSQLite)"
```

## Estructura y alcance

- `Backend/modelos/`: entidades de dominio.
- `Backend/persistencia.py`, `pedidos.py`, `flota.py`: reglas persistentes, reservas y transacciones.
- `Backend/main.py`, `consola.py`: carga inicial y menú.
- `Backend/api.py`: API y publicación local del frontend.
- `Frontend/`: páginas y scripts, sin herramientas de compilación.
- `tests/`: pruebas automatizadas.
- [Informe](Informe.md): arquitectura, decisiones y paradigmas con referencias al código.
- [Registro de verificación](docs/VERIFICACION.md): resultados y alcance de las comprobaciones de entrega.

La capacidad se controla por volumen, no por peso. Cada vehículo atiende un pedido activo. Depósitos, vehículos y conductores tienen altas por consola y datos de demo; sus altas web quedan pendientes. La web permite establecer cantidades de ítems, pero no quitarlos ni editar la cabecera después de crear el borrador. No se implementan precios, rutas óptimas, entregas parciales, devoluciones, estadísticas avanzadas ni historial de horas de transición. La aplicación se entrega para uso local; no incluye autenticación ni despliegue público.
