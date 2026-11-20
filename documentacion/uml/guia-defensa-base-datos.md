# Guía para defender el diseño de la base de datos

[Índice de documentación](../README.md) · [Diagrama UML](diagrama-base-datos.md)

## Cómo empezar la explicación

> El sistema utiliza una sola base de datos SQLite. Dentro de esa base hay nueve tablas que separan productos, depósitos, pedidos, flota y datos de control. Las tablas se relacionan mediante claves foráneas para representar cómo funciona la logística y evitar repetir información.

Cada rectángulo del [diagrama UML](diagrama-base-datos.md) representa una **tabla**, no una base de datos distinta. Las tablas almacenan registros: un producto, un depósito, un pedido, etc.

Una **clave primaria (PK)** identifica un registro sin repetirlo. Una **clave foránea (FK)** guarda el identificador de un registro de otra tabla. Por ejemplo, `vehiculos.dni_conductor` referencia `conductores.dni`: permite saber quién conduce el vehículo sin copiar su nombre y estado dentro del vehículo.

## Por qué existe cada relación

| Tabla que guarda la FK | Campo | Tabla referenciada | Motivo |
|---|---|---|---|
| `existencias` | `id_producto` | `productos` | Saber de qué producto son las unidades almacenadas. |
| `existencias` | `id_deposito` | `depositos` | Saber dónde están esas unidades. |
| `pedido_items` | `id_pedido` | `pedidos` | Saber a qué pedido pertenece cada renglón. |
| `pedido_items` | `id_producto` | `productos` | Saber qué producto se solicita. |
| `pedido_items` | `id_deposito` | `depositos` | Saber desde dónde se retira el producto. |
| `ingresos_stock` | `id_producto` | `productos` | Identificar el producto de una operación de ingreso. |
| `ingresos_stock` | `id_deposito` | `depositos` | Identificar el depósito que recibe ese ingreso. |
| `vehiculos` | `dni_conductor` | `conductores` | Identificar al conductor actualmente asignado. |
| `pedidos` | `patente_vehiculo` | `vehiculos` | Identificar al vehículo asignado al pedido y conservar esa referencia histórica. |

### 1. Productos, depósitos y existencias

`productos` describe **qué es** un artículo: nombre, volumen y peso unitario. `depositos` describe **dónde se almacena**: ubicación y capacidad. `existencias` responde **cuántas unidades de ese producto hay en ese depósito**.

La cantidad no pertenece solamente al producto: una remera puede tener 20 unidades en el depósito Centro y 15 en Melipal. Tampoco pertenece solamente al depósito, porque un depósito almacena muchos productos.

Por eso, productos y depósitos tienen una relación **muchos a muchos**, resuelta mediante `existencias`. Cada fila de existencias apunta a exactamente un producto y un depósito; cada producto o depósito puede participar en cero o muchas filas.

Ejemplo ilustrativo:

| Depósito | Producto | Cantidad física |
|---|---|---:|
| Centro | Remera | 20 |
| Melipal | Remera | 15 |
| Centro | Campera | 8 |

La PK de `existencias` es la pareja `(id_deposito, id_producto)`. Eso impide tener dos filas distintas para la misma combinación. Cambiar su cantidad actualiza el stock de esa pareja.

**Para decir en voz alta:**

> Separamos el catálogo del stock porque un producto puede estar en varios depósitos. La tabla existencias vincula producto y depósito, y guarda la cantidad correspondiente a esa combinación.

### 2. Pedidos y pedido_items

`pedidos` guarda los datos comunes de la solicitud: cliente, destino, prioridad, horarios y estado. `pedido_items` guarda sus renglones: producto, depósito de origen y cantidad.

Un pedido puede contener varios productos. Un producto puede aparecer en muchos pedidos. Además, un mismo producto puede salir de diferentes depósitos dentro del mismo pedido.

Ejemplo: el pedido `P-100` solicita 12 remeras. Se pueden tomar 7 del depósito Centro y 5 de Melipal. Se guardan dos ítems con el mismo pedido y producto, pero distinto depósito.

La PK es `(id_pedido, id_deposito, id_producto)`. Así, una combinación exacta no se repite, pero el mismo producto puede tener distintos depósitos de origen.

Las tres FK de cada ítem responden tres preguntas: **¿a qué pedido pertenece?, ¿qué producto es?, ¿de qué depósito sale?** La cantidad responde cuántas unidades se solicitan.

El esquema permite un pedido con cero ítems porque primero se crea un borrador. La aplicación exige que tenga al menos un ítem antes de confirmarlo.

**Para decir en voz alta:**

> Dividimos el pedido en cabecera y detalle. La cabecera guarda los datos generales una sola vez y cada ítem indica qué producto se pide, cuántas unidades y desde qué depósito se retiran.

### 3. Ingresos de stock, productos y depósitos

`ingresos_stock` identifica una operación de ingreso mediante una `clave` única y guarda producto, depósito y cantidad.

Su función principal es permitir reintentos sin duplicar un ingreso. Por ejemplo: se solicitan 10 remeras para Centro; la operación se aplica, pero la respuesta no llega por un problema de conexión. Si el cliente repite la misma operación con la misma clave y datos, el backend reconoce que ya fue aplicada y no vuelve a sumar 10.

Las dos FK identifican **qué ingresó y dónde ingresó**. Son necesarias aunque `existencias` también tenga esos identificadores: `existencias` guarda la cantidad actual; `ingresos_stock` permite reconocer operaciones de ingreso ya procesadas.

No debe presentarse como un historial completo de movimientos: no registra todos los retiros y despachos. El mecanismo se utiliza en los ingresos que se realizan con clave de operación.

**Para decir en voz alta:**

> Esta tabla evita que un reintento de una carga sume stock dos veces. Se vincula con productos y depósitos para identificar exactamente qué operación se aplicó.

### 4. Vehículos y conductores

La FK está en `vehiculos.dni_conductor`. El nombre y el estado del conductor permanecen en `conductores`; el vehículo solo guarda su DNI como referencia.

La relación actual es **cero o uno en ambos extremos**: puede haber un vehículo sin conductor y un conductor sin vehículo. Cuando se asignan, cada vehículo tiene como máximo un conductor y cada conductor puede estar asignado como máximo a un vehículo.

Esto se representa con dos condiciones: `dni_conductor` admite `NULL`, para expresar que no hay asignación, y es `UNIQUE`, para impedir repetir un DNI no nulo en distintos vehículos.

No hace falta guardar además una patente en la tabla conductores. El backend consulta la referencia existente para saber qué vehículo tiene cada conductor. Esto evita mantener dos asignaciones que podrían contradecirse.

La tabla representa la asignación actual; no es un historial de todos los vehículos que condujo una persona.

**Para decir en voz alta:**

> Guardamos una sola referencia para la asignación. Un vehículo puede estar sin conductor, pero un conductor no puede quedar asignado simultáneamente a dos vehículos.

### 5. Pedidos y vehículos

La FK está en `pedidos.patente_vehiculo`. Permite conocer qué vehículo se asignó al pedido sin copiar sus datos de capacidad, estado o conductor.

Un pedido puede no tener vehículo, por ejemplo cuando está en borrador o confirmado a la espera de asignación. Cuando lo tiene, el esquema permite como máximo uno.

Un vehículo puede aparecer en **muchos pedidos históricos**, porque se reutiliza para distintas entregas. Sin embargo, solo puede estar asignado a **un pedido activo a la vez**. El sistema considera activos para esta restricción los pedidos `Confirmado` y `Despachado`.

El índice único parcial `pedido_vehiculo_activo`, creado en `Backend/persistencia.py`, aplica esa exclusividad a las patentes no nulas de esos estados. No impide que la misma patente figure en pedidos anteriores entregados o cancelados.

**Para decir en voz alta:**

> Un vehículo puede realizar muchos pedidos a lo largo del tiempo, pero no atender dos pedidos activos simultáneamente. Conservamos su patente en el pedido para mantener la referencia histórica.

## Por qué inicializaciones no tiene vínculos

`inicializaciones` guarda una marca, como `datos_base_v1`, y la fecha en que se aplicó la carga inicial. No representa una entidad logística. La rutina de carga consulta esa marca para no repetir la inicialización ni volver a crear los datos base en cada arranque.

Por eso no necesita claves foráneas hacia productos, depósitos o pedidos. Es una tabla de control interno.

## Un recorrido que conecta todas las tablas

Ejemplo ilustrativo, sin otros pedidos que reserven ese producto:

1. Se registra la Remera en `productos` y el depósito Centro en `depositos`.
2. Se ingresan 20 unidades. `existencias` refleja esas 20; si el ingreso tiene clave, `ingresos_stock` registra la operación para reconocer reintentos.
3. Se crea `P-100` en `pedidos` y un ítem que solicita 5 remeras de Centro en `pedido_items`.
4. Al confirmar, quedan 20 unidades físicas, 5 reservadas y 15 disponibles. La reserva se calcula desde los ítems de pedidos confirmados; no existe una tabla de reservas.
5. Se asigna un conductor a un vehículo y ese vehículo al pedido. La aplicación comprueba disponibilidad y capacidad.
6. Al despachar, el stock físico baja a 15, el pedido pasa a `Despachado` y el vehículo a `En Ruta`. Esas escrituras se realizan dentro de una transacción.
7. Al entregar, el pedido pasa a `Entregado` y el vehículo vuelve a estar disponible. La patente queda guardada como referencia histórica.

**Por qué importa la transacción:** si falla una escritura durante el despacho, se revierten las demás. Así se evita, por ejemplo, descontar stock y dejar el pedido todavía confirmado.

## Preguntas que podrían hacerte

**¿Por qué guardar identificadores y no repetir nombres?**

Los identificadores relacionan registros sin copiar todos sus datos. Los nombres pueden repetirse o cambiar. Si el nombre del producto está en un solo lugar, no hay que corregirlo en cada fila de existencias e ítems. Esto reduce redundancia y problemas de actualización.

**¿Qué evita una clave foránea?**

Impide referencias a registros inexistentes: un ítem no puede apuntar a un producto, depósito o pedido que no existe. La conexión habilita `PRAGMA foreign_keys = ON`. Las claves foráneas no verifican por sí solas stock suficiente, capacidad o transiciones de estado: esas reglas también se controlan en el backend.

**¿Por qué no se conecta pedido_items directamente con existencias?**

El esquema implementado referencia producto y depósito por separado. No tiene una FK compuesta a `existencias`. La disponibilidad se consulta y valida en el backend. La combinación puede tener stock cero sin que exista una fila en `existencias`, y aun así el producto y el depósito son registros válidos.

**¿Existencias y pedido_items no guardan lo mismo?**

No. `existencias` guarda cuánto hay físicamente; `pedido_items` guarda cuánto solicita un pedido a cada origen. Pedir o confirmar no equivale a retirar: el stock físico se descuenta al despachar.

**¿Dónde se guarda Entrega? ¿Y los clientes?**

No hay tablas independientes para esas entidades. El cliente es un campo de texto de `pedidos`. El objeto Python `Entrega` se reconstruye con los horarios y el estado del pedido. Que exista una clase Python no implica que tenga una tabla propia.

**¿Por qué no guardar stock reservado y volumen total como columnas?**

Se calculan a partir de datos ya guardados: las reservas desde los ítems confirmados y los volúmenes desde cantidades y volumen unitario. Así no hace falta actualizar dos representaciones de un mismo resultado y se reduce el riesgo de que queden distintas.

**¿Se pueden borrar registros relacionados automáticamente?**

Las FK no declaran borrado en cascada. No debe afirmarse que borrar un producto elimina automáticamente sus ítems o existencias.

## Guion breve para cerrar la explicación

> El diseño separa el catálogo, las cantidades físicas, los pedidos y la flota. Existencias une productos con depósitos para indicar dónde está cada cantidad. Pedido_items une cada pedido con sus productos y depósitos de origen. El pedido referencia al vehículo que lo atiende y el vehículo al conductor asignado. Las claves foráneas mantienen referencias válidas, las claves compuestas evitan combinaciones duplicadas y las restricciones de unicidad evitan asignaciones simultáneas incompatibles. Además, usamos transacciones para que un despacho se complete entero o se revierta.

## Fuentes del proyecto

- [Diagrama y detalle del esquema](diagrama-base-datos.md).
- [SQL: tablas y restricciones](../../Backend/schema.sql).
- [Persistencia: stock, ingresos e índice de vehículo activo](../../Backend/persistencia.py).
- [Pedidos: reservas y transacciones](../../Backend/pedidos.py).
- [Flota: asignación de conductores](../../Backend/flota.py).

Esta guía explica el código existente. Los ejemplos son ilustrativos; no corresponden a cambios en la base de trabajo. No se ejecutaron pruebas funcionales para generar esta documentación.
