# Sistema de Gestión Logística y Distribución

Trabajo Práctico Final del **Grupo 5 — Programación III — ICOMP**.

El proyecto busca centralizar la gestión de productos, depósitos, pedidos, vehículos y conductores para facilitar la distribución. Actualmente ofrece un **programa de consola en Python con inventario, pedidos y flota persistentes en SQLite**, además de una simulación separada de asignación de pedidos a vehículos.

## Estado actual

La versión actual permite completar una distribución desde el menú: registrar mercadería y flota, crear un pedido con productos de varios depósitos, reservar stock, asignar un vehículo, despachar y registrar la entrega. Los datos se conservan entre ejecuciones en una sola base SQLite local.

| Componente | Estado |
| --- | --- |
| Menú de consola | Operativo para inventario, pedidos y flota. |
| Inventario | Stock por depósito, capacidad, ingresos, retiros y traslados. |
| Pedidos | Borrador editable, confirmación completa, reservas y cancelación. |
| Distribución | Un pedido activo por vehículo, despacho atómico y liberación al entregar. |
| Persistencia | Siete tablas, claves foráneas y migración aditiva de bases anteriores. |
| Verificación | 56 pruebas automatizadas con SQLite real y archivos temporales. |
| Interfaz web y API REST | Pendientes; el acceso actual es por consola o desde Python. |

## Funcionalidades actuales

- Menú interactivo para operar inventario, pedidos y flota sin escribir código Python.
- Registro y recuperación de productos y depósitos.
- Stock independiente de cada producto en cada depósito y consulta del total.
- Ingresos y retiros de mercadería con control de stock y capacidad.
- Traslados entre depósitos en una transacción: si falla el destino, también se revierte la salida.
- Recuperación del inventario al reiniciar el programa.
- Pedidos abastecidos desde varios depósitos, elegidos manualmente.
- Borradores editables, confirmación con reservas, cancelación, despacho completo y entrega.
- Consulta de stock físico, reservado y disponible; retiros y traslados respetan las reservas.
- Registro de vehículos y conductores, estados operativos y asignación manual uno a uno.
- Asignación manual de un pedido confirmado por vehículo, con control de capacidad y conductor.
- Despacho integrado de stock y flota; al entregar, el vehículo vuelve a estar disponible.
- Simulación de pedidos, vehículos y conductores en memoria, sin modificar el inventario guardado.

## Tecnologías

**Python 3.12+**, SQLite y el módulo `sqlite3` de la biblioteca estándar. No se requieren paquetes externos ni un servidor de base de datos.

El modelado utiliza programación orientada a objetos, la coordinación de operaciones utiliza programación imperativa y la persistencia utiliza SQL. La interfaz web en JavaScript y la API REST en Python siguen previstas para etapas posteriores.

## Instalación y ejecución

```bash
git clone https://github.com/sarrgyy/TPF-Grupo5-ProgramacionIII-ICOMP.git
cd TPF-Grupo5-ProgramacionIII-ICOMP
python Backend/main.py
```

En Windows se puede reemplazar `python` por `py`; en otros sistemas, por `python3` si corresponde.

El programa crea automáticamente `Backend/logistica.db` y abre el menú principal. La ruta predeterminada es independiente de la carpeta desde la que se ejecute. Si la base está vacía, carga este escenario inicial:

| Depósito | Producto | Cantidad |
| --- | --- | ---: |
| D-001 — Base Bariloche | PRD-1 — Cajas de Leche | 500 |
| D-001 — Base Bariloche | PRD-2 — Bolsas de Harina | 800 |
| D-002 — Depósito Centro | PRD-1 — Cajas de Leche | 100 |

Los siguientes arranques recuperan los datos existentes, sin reponer ni descontar stock automáticamente. Las consultas de inventario, pedidos y flota están disponibles desde sus respectivos menús.

Para utilizar otro archivo (su carpeta debe existir):

```bash
python Backend/main.py --db mi_inventario.db
```

Para consultar todos los datos y terminar sin abrir el menú:

```bash
python Backend/main.py --resumen
```

Para ejecutar la simulación de pedidos y terminar sin abrir el menú:

```bash
python Backend/main.py --simular-pedidos
```

La simulación toma una copia del stock disponible de `D-001`, respetando las reservas existentes. Con los datos iniciales, `P-100` tiene volumen 16.0 y se asigna a `AB123CD`; `P-101` tiene volumen 25.0 y no encuentra vehículo con capacidad suficiente. El stock simulado termina en 430 cajas de leche y 770 bolsas de harina, pero **la base conserva sus existencias originales**. Esta simulación no crea pedidos persistentes ni realiza movimientos reales de mercadería.

`--resumen` y `--simular-pedidos` no se combinan entre sí. Ambas opciones admiten `--db`.

## Uso del menú

| Menú principal | Operaciones |
| --- | --- |
| `1. Inventario` | Consultar existencias y productos; registrar productos y depósitos; ingresar, retirar y trasladar mercadería. |
| `2. Pedidos` | Listar y consultar detalle; crear y editar borradores; establecer o quitar productos por depósito; confirmar, cancelar, asignar o liberar vehículo, despachar y entregar. |
| `3. Flota` | Consultar vehículos y conductores; registrarlos; asignar o liberar conductor; cambiar estados operativos. |
| `0. Salir` | Cerrar el programa. |

Dentro de un submenú, `0` vuelve al principal. Durante una carga, escribir `/volver` cancela esa operación. Los campos requeridos no pueden quedar vacíos; la prioridad acepta Enter para usar 1. Las cantidades son enteros positivos y las medidas admiten coma o punto decimal. Para retirar mercadería, ingresar la cantidad positiva: el menú realiza el descuento.

Cada operación exitosa se guarda inmediatamente. Si hay un error de stock, capacidad, identificador o estado, se informa y se vuelve al submenú. Las operaciones guardadas anteriormente se conservan. Al cerrar la entrada de consola o usar Ctrl+C se termina la sesión sin guardar un formulario incompleto.

### Primera prueba completa por menú

Para mantener la prueba separada del inventario habitual, usar un archivo nuevo:

```bash
python Backend/main.py --db prueba_menu.db
```

1. Entrar a **Flota**. Registrar el vehículo `V-1` con capacidad `40` y el conductor `C-1`, nombre `Carlos`. Asignar `C-1` a `V-1`. Volver al principal con `0`.
2. Entrar a **Pedidos**. Crear el borrador `PED-1`, cliente `Almacén Sur`, destino `Mitre 200`, prioridad `1`.
3. Elegir **Establecer producto y cantidad por depósito** dos veces: `PED-1`, `D-001`, `PRD-1`, `50`; luego `PED-1`, `D-002`, `PRD-1`, `30`.
4. Consultar el detalle y confirmar el pedido. Quedan reservadas las 80 cajas, sin descontarlas físicamente todavía.
5. Asignar el vehículo `V-1` al pedido `PED-1`. Despacharlo: pasa a Despachado y el vehículo a En Ruta.
6. Marcar el pedido Entregado. El vehículo vuelve a Disponible conservando al conductor.
7. Volver al principal y consultar Inventario: si el archivo era nuevo, quedan `450` cajas de leche en `D-001` y `70` en `D-002`.
8. Salir con `0` desde el principal y ejecutar de nuevo con el mismo `--db`: los cambios deben conservarse.

Para repetir la carga, usar identificadores nuevos o un archivo de prueba nuevo. La aplicación no repone automáticamente existencias ni sobrescribe registros repetidos.

## Diseño de la base de datos

Se utiliza **una sola base** con siete tablas, definidas en [Backend/schema.sql](Backend/schema.sql):

| Tabla | Columnas |
| --- | --- |
| `productos` | `id_producto` (PK), `nombre`, `volumen_unitario`, `peso_unitario` |
| `depositos` | `id_deposito` (PK), `nombre`, `ubicacion`, `capacidad_maxima` |
| `existencias` | `id_deposito` (FK), `id_producto` (FK), `cantidad` |
| `pedidos` | `id_pedido` (PK), `cliente`, `destino`, `prioridad`, `estado`, `patente_vehiculo` (FK, opcional), `creado_en` (UTC) |
| `pedido_items` | `id_pedido` (FK), `id_deposito` (FK), `id_producto` (FK), `cantidad` |
| `conductores` | `dni` (PK), `nombre`, `estado` |
| `vehiculos` | `patente` (PK), `capacidad_maxima`, `estado`, `dni_conductor` (FK, UNIQUE, opcional) |

La clave primaria de `existencias` es la pareja `(id_deposito, id_producto)`. Un producto puede estar en varios depósitos y un depósito puede contener varios productos.

La clave primaria de `pedido_items` es `(id_pedido, id_deposito, id_producto)`. La cantidad solicitada de un producto es la suma de lo asignado manualmente a cada depósito. Las tablas nuevas se crean automáticamente al abrir una base anterior y se conservan sus datos de inventario.

Al abrir una base anterior, `InventarioSQLite` agrega la columna `pedidos.patente_vehiculo` si falta y crea el índice único parcial `pedido_vehiculo_activo`. Este índice permite un solo pedido Confirmado o Despachado por vehículo; los pedidos cancelados o entregados conservan la patente como referencia histórica sin ocuparlo. La migración no reemplaza tablas ni borra datos.

- Las cantidades son enteras no negativas; peso, volumen y capacidad deben ser positivos y finitos.
- El volumen ocupado se calcula sumando `cantidad × volumen_unitario` de todos los productos del depósito; no se guarda un total duplicado.
- Capacidad y volumen unitario deben expresarse en la misma unidad de volumen.
- El stock global de un producto se calcula sumando sus existencias.
- Las escrituras validan las reglas y se confirman completas o se revierten.
- Un producto registrado sin existencias en un depósito registrado tiene stock cero. Consultar un identificador inexistente produce un error.

`Producto` contiene únicamente las características del producto. El antiguo `Producto.actualizar_stock()` se reemplazó por `InventarioSQLite.actualizar_stock()`, que exige indicar el depósito.

### Identificadores y unidades

Los campos de identificación reciben solo el identificador, no el nombre que aparece junto a él. Por ejemplo, ante `D-001 — Base Bariloche`, ingresar `D-001`; ante `PRD-1 — Cajas de Leche`, ingresar `PRD-1`.

La cantidad indica **unidades del producto**; no es su volumen ni su peso. El espacio necesario se calcula como `cantidad × volumen_unitario`. Productos, depósitos y vehículos deben usar la misma unidad de volumen. La aplicación guarda los números y no convierte unidades automáticamente.

Por ejemplo, si se utiliza m³, un producto de 500 cm³ debe registrarse con volumen `0.0005`, no `500`. Si un producto ocupa `500` por unidad y un depósito tiene `590` de espacio libre, solo entra una unidad. El peso se registra, pero todavía no limita los movimientos ni la asignación a vehículos.

## Uso del inventario desde Python (opcional)

Después de ejecutar el programa una vez, este ejemplo puede ejecutarse desde una consola Python ubicada en la raíz del repositorio:

```python
from Backend.main import RUTA_DB
from Backend.persistencia import InventarioSQLite
from Backend.modelos.deposito import Deposito
from Backend.modelos.productos import Producto

with InventarioSQLite(RUTA_DB) as inventario:
    # Cantidad positiva: ingreso. Cantidad negativa: retiro.
    inventario.actualizar_stock("D-001", "PRD-1", 20)
    inventario.actualizar_stock("D-001", "PRD-1", -5)
    inventario.transferir("D-001", "D-002", "PRD-1", 10)

    print(inventario.stock("D-001", "PRD-1"))
    print(inventario.stock_total("PRD-1"))
    print(inventario.obtener_deposito("D-001").espacio_disponible())

    # Usar identificadores nuevos; repetirlos produce un error de duplicado.
    inventario.registrar_producto(Producto("PRD-3", "Arroz", 0.1, 1.0))
    inventario.registrar_deposito(Deposito("D-003", "Depósito Norte", "Ruta 237", 300.0))
    inventario.actualizar_stock("D-003", "PRD-3", 50)
```

Los cambios se guardan en cada operación y pueden consultarse al ejecutar nuevamente `python Backend/main.py`. Las reglas de negocio inválidas generan `ValueError`; los identificadores duplicados generan `sqlite3.IntegrityError`. Cada ingreso/retiro es una operación independiente; un traslado agrupa sus dos movimientos.

El archivo `.db` y sus archivos auxiliares quedan excluidos de Git. Se versiona el esquema y el código que carga los ejemplos, no el inventario local.

## Pedidos y reservas

El flujo persistente es `Borrador → Confirmado → Despachado → Entregado`.

- **Borrador:** permite editar cliente, destino, prioridad y productos por depósito. No reserva stock; no puede confirmarse vacío.
- **Confirmado:** valida todas las cantidades contra el stock disponible. Si falta mercadería, informa todos los faltantes, conserva el borrador y no reserva nada. Si alcanza, activa todas las reservas; ya no permite editar el pedido.
- **Despachado:** requiere un vehículo asignado, Disponible, con conductor y capacidad para el pedido completo. Descuenta las cantidades físicas de todos los depósitos, consume reservas y marca el vehículo En Ruta en una sola transacción. Una falla revierte todos los cambios. No permite un segundo despacho.
- **Entregado:** registra la finalización de un pedido Despachado y devuelve el vehículo a Disponible, sin descontar stock nuevamente. Conserva su conductor.
- **Cancelado:** solo se alcanza desde Borrador o Confirmado. Libera las reservas sin descontar mercadería y conserva el detalle. Para reemplazar un pedido confirmado, cancelarlo y crear otro con un identificador nuevo.

`stock()` indica la cantidad física, `stock_reservado()` lo comprometido en pedidos Confirmados y `stock_disponible()` la diferencia. Las reservas se calculan desde el estado del pedido y sus ítems; no se duplican en otra tabla. La mercadería reservada sigue ocupando espacio en el depósito y no se puede retirar ni trasladar para otro uso.

### Prueba manual de un pedido

Para probar en un archivo separado, ejecutar desde la raíz:

```bash
python Backend/main.py --db prueba_pedidos.db --resumen
python
```

Luego, en la consola Python, ejecutar cada bloque en orden:

```python
from Backend.persistencia import InventarioSQLite
from Backend.pedidos import PedidosSQLite, StockInsuficiente
from Backend.flota import FlotaSQLite
from Backend.modelos.vehiculo import Vehiculo
from Backend.modelos.conductor import Conductor

inv = InventarioSQLite("prueba_pedidos.db")
pedidos = PedidosSQLite(inv)
pedidos.crear_borrador("MANUAL-1", "Almacén Sur", "Mitre 200", prioridad=2)
pedidos.establecer_producto("MANUAL-1", "D-001", "PRD-1", 50)
pedidos.establecer_producto("MANUAL-1", "D-002", "PRD-1", 30)
pedidos.confirmar("MANUAL-1")

# En una base de prueba recién creada: físico 500, reservado 50, disponible 450.
print(inv.stock("D-001", "PRD-1"))
print(inv.stock_reservado("D-001", "PRD-1"))
print(inv.stock_disponible("D-001", "PRD-1"))

# El pedido completo ocupa 40 unidades de volumen.
flota = FlotaSQLite(inv)
flota.registrar_vehiculo(Vehiculo("REP-1", 40.0))
flota.registrar_conductor(Conductor("30111222", "Carlos Gómez"))
flota.asignar_conductor("REP-1", "30111222")
pedidos.asignar_vehiculo("MANUAL-1", "REP-1")
pedidos.despachar("MANUAL-1")
# Quedan 450 unidades físicas en D-001 y 70 en D-002.
print(inv.stock("D-001", "PRD-1"), inv.stock("D-002", "PRD-1"))
pedidos.entregar("MANUAL-1")
print(pedidos.obtener_pedido("MANUAL-1").estado)  # Entregado
print(flota.obtener_vehiculo("REP-1").estado)     # Disponible
inv.close()
exit()
```

Al ejecutar de nuevo `python Backend/main.py --db prueba_pedidos.db --resumen`, deben aparecer las cantidades modificadas y el pedido Entregado. Para repetir este ejemplo completo, usar un archivo de prueba nuevo o identificadores nuevos para el pedido, el vehículo y el conductor. Los ejemplos no reponen existencias existentes.

Para editar un borrador, usar `editar_borrador(id_pedido, cliente, destino, prioridad)` y `establecer_producto(...)`, que reemplaza la cantidad de esa pareja depósito/producto. `quitar_producto(id_pedido, id_deposito, id_producto)` elimina una asignación. `cancelar(id_pedido)` cancela un borrador o confirmado. `StockInsuficiente` es un `ValueError` cuyo atributo `faltantes` contiene producto, depósito, unidades solicitadas, disponibles y faltantes.

### Asignación del pedido a un vehículo

`pedidos.asignar_vehiculo(id_pedido, patente)` se usa después de confirmar. El pedido completo debe caber en un solo vehículo, aunque la mercadería provenga de varios depósitos. La asignación no despacha ni descuenta stock, pero ocupa el vehículo para ese pedido.

Para cambiar de vehículo antes del despacho, usar `pedidos.liberar_vehiculo(id_pedido)` y asignar otro. Esto mantiene las reservas de mercadería. Cancelar el pedido libera tanto sus reservas como la ocupación del vehículo. Mientras haya un pedido activo no se puede cambiar el conductor ni alterar manualmente el estado del vehículo: sus estados se coordinan con `despachar()` y `entregar()`.

Las consultas exponen `pedido.vehiculo_asignado` (también para pedidos terminados), `vehiculo.pedido_asignado` (solo el pedido activo) y `vehiculo.volumen_ocupado` (carga de un pedido Despachado; cero antes del despacho o después de entregar). No se planifican todavía el recorrido ni la recolección en cada depósito. Los pedidos que ya estaban Despachados sin vehículo en versiones anteriores pueden marcarse Entregados; todo despacho nuevo exige asignación.

Los objetos devueltos por `obtener_pedido()` y `listar_pedidos()` son copias para consulta. Las transiciones persistentes se realizan con `PedidosSQLite`; los estados de la antigua simulación de flota siguen siendo independientes.

## Vehículos y conductores

`FlotaSQLite` guarda vehículos, conductores y la asignación actual. Se utiliza una sola referencia: `vehiculos.dni_conductor`. La restricción `UNIQUE` impide asignar un mismo conductor a dos vehículos. Al consultar un conductor se obtiene su vehículo y se calcula su estado `Asignado`; no se guarda esa relación dos veces.

- Un vehículo Disponible sin conductor se puede vincular a un conductor Disponible sin vehículo.
- Para cambiar de conductor o vehículo, primero se debe liberar la asignación anterior. Repetir una asignación se rechaza.
- Un conductor asignado no puede pasar a Inactivo: primero se libera la asignación. `Asignado` se obtiene automáticamente al asignar, no se establece manualmente.
- Un vehículo asignado no puede pasar a Mantenimiento hasta liberar al conductor.
- Se conserva el estado En Ruta: requiere conductor y debe volver a Disponible antes de liberar la asignación. Todavía no representa una entidad de viaje.
- El registro recibe vehículos sin carga ni conductor y conductores sin vehículo. La asignación se realiza mediante el método persistente.
- La capacidad usa la misma unidad de volumen que los productos. Los identificadores y nombres no pueden estar vacíos; la capacidad debe ser positiva y finita.

La consola muestra la flota guardada, su pedido activo y su carga, pero no carga vehículos ni conductores de ejemplo automáticamente. La opción `--simular-pedidos` conserva su flota ficticia en memoria y no altera las asignaciones reales.

### Prueba manual de flota

Desde la raíz del proyecto, crear una base separada y abrir Python:

```bash
python Backend/main.py --db prueba_flota.db --resumen
python
```

En la consola Python:

```python
from Backend.persistencia import InventarioSQLite
from Backend.flota import FlotaSQLite
from Backend.modelos.vehiculo import Vehiculo
from Backend.modelos.conductor import Conductor

inv = InventarioSQLite("prueba_flota.db")
flota = FlotaSQLite(inv)
flota.registrar_vehiculo(Vehiculo("AB123CD", 20.0))
flota.registrar_conductor(Conductor("30111222", "Carlos Gómez"))
flota.asignar_conductor("AB123CD", "30111222")

print(flota.obtener_vehiculo("AB123CD").conductor_asignado)  # 30111222 (DNI)
print(flota.obtener_conductor("30111222").obtener_info())   # Asignado, AB123CD
inv.close()
exit()
```

Volver a ejecutar `python Backend/main.py --db prueba_flota.db --resumen`: debe aparecer la asignación guardada. Los identificadores registrados no se pueden repetir; para repetir el ejemplo usar una base nueva o identificadores nuevos.

Con una conexión abierta, `flota.liberar_conductor("AB123CD")` libera ambos lados de la asignación. Después se puede usar `flota.actualizar_estado_vehiculo("AB123CD", "Mantenimiento")` o `flota.actualizar_estado_conductor("30111222", "Inactivo")`. Para reasignar, ambos recursos deben volver a Disponible.

Los métodos de `FlotaSQLite` guardan los cambios. Los objetos devueltos por `obtener_vehiculo()`, `obtener_conductor()` y sus listados son copias: los métodos de los modelos operan en memoria. El pedido persistente activo se consulta con `pedido_asignado`; la lista `pedidos` del antiguo modelo se conserva para la simulación en memoria.

## Estructura

```text
├── README.md
├── Informe.md
├── Backend/
│   ├── main.py              # Arranque, argumentos y simulación opcional
│   ├── consola.py           # Menú interactivo y consultas compartidas
│   ├── persistencia.py      # Acceso a SQLite y reglas de inventario
│   ├── pedidos.py           # Borradores, reservas y transiciones de pedidos
│   ├── flota.py             # Vehículos, conductores y asignaciones persistentes
│   ├── schema.sql          # Tablas, claves y restricciones
│   └── modelos/
│       ├── conductor.py
│       ├── deposito.py
│       ├── entrega.py      # Pendiente de implementación
│       ├── main.py         # Delega al punto de entrada actual
│       ├── pedido.py
│       ├── productos.py
│       └── vehiculo.py
├── tests/                  # Pruebas con SQLite real y archivos temporales
└── docs/superpowers/        # Decisiones de diseño y planes de implementación
```

## Organización del código y documentación

`main.py` abre la base y elige entre menú, resumen y simulación. `consola.py` recoge los datos y muestra resultados. `persistencia.py`, `pedidos.py` y `flota.py` aplican las operaciones persistentes usando una conexión compartida; `schema.sql` define las tablas y sus restricciones.

Los archivos de `modelos/` representan entidades y operaciones en memoria. Los objetos recuperados de SQLite son copias: para guardar cambios hay que utilizar los repositorios persistentes, no modificar directamente esas copias. La simulación mantiene su propio flujo local y no escribe sus pedidos en la base.

Los módulos, clases y funciones Python, incluidos los tests, tienen docstrings en español siguiendo las convenciones de [PEP 257](https://peps.python.org/pep-0257/). Para describir contratos se utilizan las secciones `Args`, `Returns`, `Raises`, `Yields` y `Attributes` cuando corresponden. Los comentarios explican decisiones como el bloqueo de escrituras, el cálculo de reservas y las diferencias entre simulación y persistencia.

La documentación puede consultarse desde el editor o con `help()`. Por ejemplo, desde una consola Python iniciada en la raíz del proyecto:

```python
from Backend.persistencia import InventarioSQLite
help(InventarioSQLite.actualizar_stock)
```

## Pruebas

Desde la raíz del repositorio:

```bash
python -B -m unittest discover -s tests -v
```

Cubren recuperación de datos, existencias por depósito, capacidad, validaciones, traslados, rollback, reservas, estados de pedidos, confirmaciones concurrentes, flota, conflictos de asignación, despacho integrado, migración de bases anteriores y operaciones completas desde el menú con entrada real por consola. Utilizan archivos temporales y no modifican la base de uso habitual.

| Archivo | Qué verifica |
| --- | --- |
| `tests/test_inventario.py` | Existencias, capacidad, traslados y recuperación de datos. |
| `tests/test_pedidos.py` | Borradores, reservas, estados y rechazo sin cambios parciales. |
| `tests/test_flota.py` | Asignaciones únicas, disponibilidad y recuperación de flota. |
| `tests/test_distribucion.py` | Vinculación con vehículos, despacho integrado y migraciones. |
| `tests/test_main.py` | Arranque, consultas, acceso anterior y simulación. |
| `tests/test_consola.py` | Navegación, validaciones y flujo completo desde el menú. |

## Alcance y próximas etapas

Esta etapa persiste **productos, depósitos, existencias, pedidos, vehículos, conductores y sus asignaciones**. No incluye edición de características de productos/depósitos ni bajas desde la capa de persistencia; los objetos recuperados son copias de los datos y modificarlos directamente no actualiza la base. Los métodos del modelo `Deposito` operan sobre esa copia en memoria.

Queda pendiente discutir e implementar, por separado:

- Planificación de viajes, recorridos y recolección en varios depósitos.
- Entidades de entrega, despachos parciales, devoluciones e historial detallado de movimientos.
- Interfaz web y API REST.
- Priorización, restricciones por peso, optimización de rutas y reportes.
- Edición persistente de las características de las entidades y reglas de baja.

La propuesta original y los fundamentos académicos se encuentran en [Informe.md](Informe.md).
