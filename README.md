# Sistema de Gestión Logística y Distribución

Trabajo Práctico Final del **Grupo 5 — Programación III — ICOMP**.

El proyecto busca centralizar la gestión de productos, depósitos, pedidos, vehículos y conductores para facilitar la distribución. Actualmente ofrece un **programa de consola en Python con inventario y pedidos persistentes en SQLite**, además de una simulación separada de asignación de pedidos a vehículos.

## Funcionalidades actuales

- Registro y recuperación de productos y depósitos.
- Stock independiente de cada producto en cada depósito y consulta del total.
- Ingresos y retiros de mercadería con control de stock y capacidad.
- Traslados entre depósitos en una transacción: si falla el destino, también se revierte la salida.
- Recuperación del inventario al reiniciar el programa.
- Pedidos abastecidos desde varios depósitos, elegidos manualmente.
- Borradores editables, confirmación con reservas, cancelación, despacho completo y entrega.
- Consulta de stock físico, reservado y disponible; retiros y traslados respetan las reservas.
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

El programa crea automáticamente `Backend/logistica.db` y muestra el inventario. La ruta predeterminada es independiente de la carpeta desde la que se ejecute. Si la base está vacía, carga este escenario inicial:

| Depósito | Producto | Cantidad |
| --- | --- | ---: |
| D-001 — Base Bariloche | PRD-1 — Cajas de Leche | 500 |
| D-001 — Base Bariloche | PRD-2 — Bolsas de Harina | 800 |
| D-002 — Depósito Centro | PRD-1 — Cajas de Leche | 100 |

Los siguientes arranques recuperan los datos existentes, sin reponer ni descontar stock automáticamente, y muestran los pedidos guardados. No hay menú interactivo en esta etapa; las operaciones de inventario y pedidos se utilizan desde Python, como en los ejemplos de abajo.

Para utilizar otro archivo (su carpeta debe existir):

```bash
python Backend/main.py --db mi_inventario.db
```

Para ejecutar también la simulación de pedidos:

```bash
python Backend/main.py --simular-pedidos
```

La simulación toma una copia del stock disponible de `D-001`, respetando las reservas existentes. Con los datos iniciales, `P-100` tiene volumen 16.0 y se asigna a `AB123CD`; `P-101` tiene volumen 25.0 y no encuentra vehículo con capacidad suficiente. El stock simulado termina en 430 cajas de leche y 770 bolsas de harina, pero **la base conserva sus existencias originales**. Esta simulación no crea pedidos persistentes ni realiza movimientos reales de mercadería.

## Diseño de la base de datos

Se utiliza **una sola base** con cinco tablas, definidas en [Backend/schema.sql](Backend/schema.sql):

| Tabla | Columnas |
| --- | --- |
| `productos` | `id_producto` (PK), `nombre`, `volumen_unitario`, `peso_unitario` |
| `depositos` | `id_deposito` (PK), `nombre`, `ubicacion`, `capacidad_maxima` |
| `existencias` | `id_deposito` (FK), `id_producto` (FK), `cantidad` |
| `pedidos` | `id_pedido` (PK), `cliente`, `destino`, `prioridad`, `estado`, `creado_en` (UTC) |
| `pedido_items` | `id_pedido` (FK), `id_deposito` (FK), `id_producto` (FK), `cantidad` |

La clave primaria de `existencias` es la pareja `(id_deposito, id_producto)`. Un producto puede estar en varios depósitos y un depósito puede contener varios productos.

La clave primaria de `pedido_items` es `(id_pedido, id_deposito, id_producto)`. La cantidad solicitada de un producto es la suma de lo asignado manualmente a cada depósito. Las tablas nuevas se crean automáticamente al abrir una base anterior y se conservan sus datos de inventario.

- Las cantidades son enteras no negativas; peso, volumen y capacidad deben ser positivos y finitos.
- El volumen ocupado se calcula sumando `cantidad × volumen_unitario` de todos los productos del depósito; no se guarda un total duplicado.
- Capacidad y volumen unitario deben expresarse en la misma unidad de volumen.
- El stock global de un producto se calcula sumando sus existencias.
- Las escrituras validan las reglas y se confirman completas o se revierten.
- Un producto registrado sin existencias en un depósito registrado tiene stock cero. Consultar un identificador inexistente produce un error.

`Producto` contiene únicamente las características del producto. El antiguo `Producto.actualizar_stock()` se reemplazó por `InventarioSQLite.actualizar_stock()`, que exige indicar el depósito.

## Uso del inventario desde Python

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
- **Despachado:** descuenta las cantidades físicas de todos los depósitos y consume las reservas en una sola transacción. Una falla revierte todos los movimientos y deja el pedido Confirmado. No permite un segundo despacho.
- **Entregado:** registra la finalización de un pedido Despachado, sin descontar stock nuevamente.
- **Cancelado:** solo se alcanza desde Borrador o Confirmado. Libera las reservas sin descontar mercadería y conserva el detalle. Para reemplazar un pedido confirmado, cancelarlo y crear otro con un identificador nuevo.

`stock()` indica la cantidad física, `stock_reservado()` lo comprometido en pedidos Confirmados y `stock_disponible()` la diferencia. Las reservas se calculan desde el estado del pedido y sus ítems; no se duplican en otra tabla. La mercadería reservada sigue ocupando espacio en el depósito y no se puede retirar ni trasladar para otro uso.

### Prueba manual de un pedido

Para probar en un archivo separado, ejecutar desde la raíz:

```bash
python Backend/main.py --db prueba_pedidos.db
python
```

Luego, en la consola Python, ejecutar cada bloque en orden:

```python
from Backend.persistencia import InventarioSQLite
from Backend.pedidos import PedidosSQLite, StockInsuficiente

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

pedidos.despachar("MANUAL-1")
# Quedan 450 unidades físicas en D-001 y 70 en D-002.
print(inv.stock("D-001", "PRD-1"), inv.stock("D-002", "PRD-1"))
pedidos.entregar("MANUAL-1")
print(pedidos.obtener_pedido("MANUAL-1").estado)  # Entregado
inv.close()
exit()
```

Al ejecutar de nuevo `python Backend/main.py --db prueba_pedidos.db`, deben aparecer las cantidades modificadas y el pedido Entregado. Para repetir la carga, usar un identificador de pedido nuevo; los ejemplos no reponen existencias existentes.

Para editar un borrador, usar `editar_borrador(id_pedido, cliente, destino, prioridad)` y `establecer_producto(...)`, que reemplaza la cantidad de esa pareja depósito/producto. `quitar_producto(id_pedido, id_deposito, id_producto)` elimina una asignación. `cancelar(id_pedido)` cancela un borrador o confirmado. `StockInsuficiente` es un `ValueError` cuyo atributo `faltantes` contiene producto, depósito, unidades solicitadas, disponibles y faltantes.

Los objetos devueltos por `obtener_pedido()` y `listar_pedidos()` son copias para consulta. Las transiciones persistentes se realizan con `PedidosSQLite`; los estados de la antigua simulación de flota siguen siendo independientes.

## Estructura

```text
├── README.md
├── Informe.md
├── Backend/
│   ├── main.py              # Inventario y simulación opcional
│   ├── persistencia.py      # Acceso a SQLite y reglas de inventario
│   ├── pedidos.py           # Borradores, reservas y transiciones de pedidos
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
└── docs/superpowers/        # Diseño y plan de esta etapa
```

## Pruebas

Desde la raíz del repositorio:

```bash
python -B -m unittest discover -s tests -v
```

Cubren recuperación de datos, existencias por depósito, capacidad, validaciones, traslados, rollback, reservas, estados de pedidos, confirmaciones concurrentes y compatibilidad con la base anterior. Utilizan archivos temporales y no modifican la base de uso habitual.

## Alcance y próximas etapas

Esta etapa persiste **productos, depósitos, existencias y pedidos**. No incluye edición de características de productos/depósitos ni bajas desde la capa de persistencia; los objetos recuperados son copias de los datos y modificarlos directamente no actualiza la base. Los métodos del modelo `Deposito` operan sobre esa copia en memoria.

Queda pendiente discutir e implementar, por separado:

- Persistencia de vehículos, conductores y sus asignaciones.
- Entidades de entrega, despachos parciales, devoluciones e historial detallado de movimientos.
- Interfaz web y API REST.
- Priorización, restricciones por peso, optimización de rutas y reportes.

La propuesta original y los fundamentos académicos se encuentran en [Informe.md](Informe.md).
