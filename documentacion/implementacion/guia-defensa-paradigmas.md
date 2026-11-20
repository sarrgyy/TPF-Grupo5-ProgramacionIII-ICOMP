# Guía de defensa: paradigmas de programación

[Índice de documentación](../README.md) · [Tecnologías de la implementación](guia-defensa-tecnologias.md)

## Referencia que ya existe en el proyecto

El [Informe del proyecto](../../Informe.md), en la sección **Paradigmas de programación**, identifica cinco paradigmas o estilos: orientado a objetos, imperativo, funcional, declarativo y lógico. El [README principal](../../README.md) remite a ese informe. También aparecen mencionados en la guía de tecnologías.

Esta guía amplía esa explicación con evidencia del código y frases para la defensa. Se trata de una aplicación **multiparadigma**: combina distintos enfoques según la tarea. Estas categorías no son excluyentes: un método de una clase puede contener instrucciones imperativas y ejecutar una consulta declarativa.

Un paradigma es una forma de organizar y expresar una solución. Python y JavaScript son lenguajes; FastAPI es un framework; orientado a objetos o imperativo describen cómo está construido el código.

## Mapa de los ejemplos

| Paradigma o estilo | Idea central | Evidencia del proyecto |
|---|---|---|
| Orientado a objetos | Representar entidades con estado y comportamiento; distribuir responsabilidades entre objetos. | Clases de `Backend/modelos`, composición de `Entrega` dentro de `Pedido` y repositorios `InventarioSQLite`, `PedidosSQLite` y `FlotaSQLite`. |
| Imperativo | Indicar una secuencia explícita de pasos y cambios de estado. | `PedidosSQLite.despachar`: validación, cambio de estado, recorrido de ítems, descuento de stock y actualización del vehículo. |
| Funcional, aplicado parcialmente | Pasar funciones como argumentos y transformar colecciones. | `sorted` con `key=lambda` en la API; `filter` y `map` en el frontend. |
| Declarativo | Describir qué resultado o restricción se necesita. | Consultas SQL con `SELECT`, `JOIN` y `GROUP BY`; restricciones `CHECK`, claves foráneas e índices únicos. |
| Lógico | Expresar hechos y reglas, y dejar que un motor de inferencia encuentre las soluciones. | `Backend/razonamiento.pl`: hechos `vehiculo/5` y regla `candidato/4`, consultados desde `Backend/prolog.py`. |

## 1. Programación orientada a objetos

### Qué significa

Se representan conceptos del dominio mediante objetos. Cada objeto reúne **atributos**, que describen su estado, y **métodos**, que ofrecen operaciones relacionadas con ese estado.

### Cómo se implementa

En [Pedido](../../Backend/modelos/pedido.py), la clase contiene atributos como `id_pedido`, `cliente`, `prioridad`, `estado`, `productos` y `entrega`. También tiene métodos como `agregar_producto` y `actualizar_estado`, que actúan sobre el objeto en memoria.

Un ejemplo breve tomado de la inicialización del modelo:

```python
self.id_pedido = id_pedido
self.cliente = cliente
self.estado = "Borrador"
self.productos = []
self.entrega = None
```

Cada instancia representa un pedido concreto con su propio estado. Otras clases representan `Producto`, `Deposito`, `Vehiculo`, `Conductor` y `Entrega`.

Además, los repositorios son objetos con responsabilidades definidas:

- `InventarioSQLite`: conexión, catálogo, existencias y cálculos de stock.
- `PedidosSQLite`: reservas, asignación, despacho, entrega y reconstrucción de pedidos.
- `FlotaSQLite`: vehículos, conductores y asignaciones.

La web y la consola utilizan estos repositorios para realizar las operaciones persistentes.

### Composición: un objeto contiene otro

En `PedidosSQLite.obtener_pedido`, se reconstruye el pedido y, cuando tiene horarios y un estado operativo de entrega, se crea un objeto `Entrega` y se asigna a `pedido.entrega`:

```python
pedido.entrega = entrega
```

El pedido reúne así la información de su entrega. Es una relación de composición en el modelo del proyecto, no una relación de herencia: **un pedido tiene una entrega**, no “un pedido es una entrega”. La entrega es opcional y no tiene una tabla independiente.

### Abstracción y encapsulación de responsabilidades

La API puede llamar a `repo.confirmar(identificador)` sin reproducir allí todas las consultas y validaciones de confirmación. El repositorio ofrece una operación del dominio y concentra su implementación.

Es válido hablar de organización y encapsulación de responsabilidades. Los atributos de los modelos son públicos: no debe afirmarse que todos están protegidos por mecanismos de privacidad estricta. Los métodos con prefijo `_` indican uso interno por convención de Python.

### Qué beneficio aporta

Permite relacionar el código con las entidades del problema y reunir las operaciones bajo una responsabilidad. También ayuda a reutilizar el comportamiento desde distintas interfaces.

### Cómo decirlo

> Usamos orientación a objetos para representar entidades como pedidos, productos y vehículos, y para organizar las operaciones en repositorios. Un pedido reúne sus datos e ítems y puede contener un objeto Entrega. Las operaciones persistentes se realizan mediante los repositorios.

**Distinción para la defensa:** cambiar un atributo de un objeto consultado no actualiza automáticamente SQLite. Los modelos devueltos son copias; las escrituras deben pasar por las operaciones persistentes.

## 2. Programación imperativa y control estructurado

### Qué significa

Se expresa **cómo realizar una operación**, indicando el orden de las instrucciones, las decisiones y los cambios de estado. Aparecen asignaciones, llamadas, condicionales y bucles.

### Cómo se implementa

El método `PedidosSQLite.despachar` en [pedidos.py](../../Backend/pedidos.py) sigue una secuencia explícita:

1. Inicia una transacción.
2. Exige que el pedido esté `Confirmado`.
3. Recupera el pedido y verifica que tenga vehículo asignado.
4. Valida el vehículo, su conductor, disponibilidad y capacidad.
5. Cambia el pedido a `Despachado`.
6. Recorre los ítems con un `for` y descuenta sus cantidades del stock físico.
7. Actualiza el vehículo a `En Ruta`.

Fragmento del recorrido de ítems:

```python
for item in self._items(id_pedido):
    self.inventario._modificar_stock(
        item["id_deposito"], item["id_producto"], -item["cantidad"]
    )
```

Las instrucciones se ejecutan en un orden determinado y producen cambios. La transacción hace que, si falla una escritura, se reviertan los cambios de esa operación.

La [consola](../../Backend/consola.py) también utiliza funciones y métodos, condicionales y bucles para mostrar opciones, leer entradas y ejecutar acciones. Se puede describir este control como **estructurado**, dentro del enfoque imperativo.

### Qué beneficio aporta

Hace explícito el orden requerido por el negocio: primero se valida y después se modifica. Permite seguir y explicar cada paso del despacho.

### Cómo decirlo

> Usamos programación imperativa para expresar procesos como el despacho. Indicamos paso a paso qué condiciones verificar y qué datos actualizar, utilizando decisiones y bucles dentro de una transacción.

La orientación a objetos y el estilo imperativo conviven en este ejemplo: `despachar` es un método de un objeto y su cuerpo contiene una secuencia imperativa.

## 3. Estilo funcional en operaciones concretas

### Qué significa

En los ejemplos del proyecto, consiste en pasar funciones como argumentos y expresar selección, transformación u ordenamiento de colecciones mediante esas funciones.

No toda función pertenece por eso al paradigma funcional. Los ejemplos relevantes son las operaciones de orden superior y las transformaciones que no modifican la colección de entrada.

### Cómo se implementa en Python

En [api.py](../../Backend/api.py), el listado de pedidos utiliza:

```python
ordenados = sorted(PedidosSQLite(inv).listar_pedidos(), key=lambda p: (-p.prioridad, p.creado_en, p.id_pedido))
```

`sorted` recibe una función mediante `key`. La `lambda` obtiene de cada pedido los criterios de comparación:

- `-p.prioridad`: permite mostrar primero la prioridad más alta.
- `p.creado_en`: ordena por fecha cuando coincide la prioridad.
- `p.id_pedido`: resuelve empates restantes.

`sorted` devuelve una lista nueva. No reordena la lista original ni clona los objetos que contiene.

### Cómo se implementa en JavaScript

En [gestion.js](../../Frontend/gestion.js), se filtran productos según el texto buscado:

```javascript
const filtrados = productos.filter(p => `${p.id_producto} ${p.nombre}`.toLocaleLowerCase("es").includes(busqueda));
```

`filter` recibe una función que decide qué elementos conservar y devuelve un nuevo arreglo. El ejemplo permite mostrar los productos coincidentes sin eliminar los demás del catálogo cargado.

En ese archivo también se usa `map` para transformar depósitos en pares de identificador y nombre para los selectores:

```javascript
const opciones = depositos.map(d => [d.id_deposito, d.nombre]);
```

`map` transforma cada elemento y devuelve otro arreglo. Estos usos de `filter` y `map` no modifican los objetos de entrada; utilizar esos métodos con otros callbacks no garantiza por sí solo ausencia de efectos secundarios.

### Qué beneficio aporta

Permite expresar de forma breve la intención de seleccionar, transformar u ordenar datos y conservar las colecciones originales.

### Cómo decirlo

> Aplicamos estilo funcional en operaciones concretas: ordenamos pedidos con sorted y una lambda, filtramos productos con filter y transformamos datos de selectores con map. Son transformaciones dentro de una aplicación que también modifica estado y guarda datos.

La aplicación no es funcional pura: utiliza estado mutable, interacción con el DOM, archivos, base de datos y entrada/salida. La `lambda` sola tampoco convierte a todo el programa en funcional.

## 4. Programación declarativa

### Qué significa

Se describe **qué resultado se necesita** o **qué condición debe cumplirse**, dejando al motor o al entorno resolver los detalles de ejecución.

### Cómo se implementa

La evidencia más directa es SQL. En `InventarioSQLite.stock_reservado`, en [persistencia.py](../../Backend/persistencia.py), se utiliza esta consulta:

```sql
SELECT i.cantidad FROM pedido_items i
JOIN pedidos p USING (id_pedido)
WHERE i.id_deposito = ? AND i.id_producto = ? AND p.estado = 'Confirmado'
```

La consulta declara qué cantidades interesan: las del producto y depósito indicados, correspondientes a pedidos confirmados. SQLite determina cómo resolver la consulta. Después, Python suma los resultados.

La consulta del endpoint `/stock` utiliza además `GROUP BY` para agrupar las reservas por producto y depósito.

En [schema.sql](../../Backend/schema.sql), las restricciones declaran condiciones que deben respetar los datos:

```sql
cantidad INTEGER NOT NULL CHECK (typeof(cantidad) = 'integer' AND cantidad >= 0)
```

Esto exige una cantidad entera no negativa en `existencias`. Las claves foráneas declaran referencias válidas y las claves primarias y restricciones de unicidad impiden duplicados según sus reglas. El índice único parcial de vehículo activo se declara desde la migración en `persistencia.py`.

HTML y CSS también expresan estructura y presentación de forma declarativa. Para defender el paradigma con una operación del sistema, SQL y sus restricciones son los ejemplos más directos y ya están citados en el informe.

### Qué beneficio aporta

Permite describir consultas y restricciones de manera cercana a los datos, delegando su ejecución y aplicación al motor SQLite.

### Cómo decirlo

> Usamos programación declarativa en SQL: indicamos qué registros necesitamos y qué restricciones deben cumplir, mientras SQLite resuelve la consulta y aplica esas restricciones.

## 5. Programación lógica

### Qué significa

Se declaran **hechos** (lo que se sabe) y **reglas** (cuándo algo se cumple), y se hace una consulta. El motor de inferencia busca todas las combinaciones que satisfacen las reglas; no se escribe el recorrido paso a paso.

### Cómo se implementa

En [razonamiento.pl](../../Backend/razonamiento.pl), cada vehículo se carga como un hecho `vehiculo(Patente, Capacidad, Estado, TieneConductor, TienePedidoActivo)`. La regla que define qué vehículo sirve para un pedido es:

```prolog
candidato(VolumenPedido, Patente, Capacidad, Restante) :-
    vehiculo(Patente, Capacidad, "Disponible", true, false),
    Capacidad >= VolumenPedido,
    Restante is Capacidad - VolumenPedido.
```

Un vehículo es candidato si está Disponible, tiene conductor, no tiene pedido activo y su capacidad alcanza. `findall` reúne todos los candidatos y `predsort` los ordena por menor espacio sobrante.

Python participa a través de [prolog.py](../../Backend/prolog.py): arma un JSON con el volumen y la flota, ejecuta `swipl` como subproceso, y recibe la lista de recomendaciones también en JSON. El endpoint `GET /pedidos/{id}/vehiculos-recomendados` de la API lo usa para pedidos Confirmados. Recomendar no asigna: la asignación sigue siendo explícita.

### Qué beneficio aporta

Las condiciones de compatibilidad quedan escritas como una regla legible y separada del resto del código. Agregar una condición es agregar un objetivo a la regla.

### Límites

Depende de tener SWI-Prolog instalado; sin él, el endpoint responde 503. La interfaz web no consume todavía este endpoint. Se invoca un proceso por consulta, algo aceptable para una demostración local.

### Cómo decirlo

> Usamos programación lógica para recomendar vehículos: declaramos en Prolog qué condiciones debe cumplir un vehículo y el motor encuentra cuáles las cumplen. Python le pasa los datos y recibe el resultado, pero la decisión de asignar sigue siendo explícita.

## Estilos complementarios: eventos y asincronía

Además de los enfoques del informe, el frontend está dirigido por eventos. En [gestion.js](../../Frontend/gestion.js):

```javascript
byId("buscar-producto").addEventListener("input", mostrarInventario);
```

Se registra una función para que el navegador la invoque cuando el usuario cambia la búsqueda. Hay otros manejadores para cambios de selección y envío de formularios.

También se utilizan promesas y `async/await` para esperar respuestas HTTP. En [api.js](../../Frontend/api.js), `apiFetch` espera el resultado de `fetch`. Esto permite que el navegador continúe atendiendo otras tareas mientras la operación de red está pendiente.

Los eventos describen cómo se disparan acciones; la asincronía describe cómo se gestionan esperas y continuaciones. Son características presentes en la solución, pero no hace falta reemplazar con ellas la clasificación principal del informe. `async/await` por sí solo no demuestra paralelismo ni programación reactiva.

## Preguntas posibles sobre orientación a objetos

**¿Dónde hay herencia?**

Hay ejemplos concretos en la infraestructura: en `api.py`, `Entrada` hereda de `BaseModel` de Pydantic y modelos como `PedidoEntrada` heredan de `Entrada`, reutilizando su configuración. También se definen excepciones mediante herencia. Las entidades logísticas como `Pedido` y `Vehiculo` no forman una jerarquía de herencia propia entre sí.

**¿Todos los objetos que tienen actualizar_estado demuestran polimorfismo?**

Compartir el nombre de un método no basta para demostrar un diseño polimórfico. Para defenderlo habría que mostrar un consumidor común que utilice objetos intercambiables bajo un mismo contrato. La evidencia más clara del proyecto está en las entidades, composición y repositorios; no se presenta el polimorfismo de dominio como un eje de la implementación.

**¿La composición es lo mismo que una FK?**

No. La composición describe cómo se relacionan objetos en el programa; una FK relaciona registros en la base de datos. Por ejemplo, `pedido.entrega` contiene un objeto `Entrega`, aunque no haya una tabla de entregas.

## Un mismo proceso puede combinar enfoques

Al operar sobre un pedido:

1. Un evento del navegador inicia la acción.
2. JavaScript espera la respuesta HTTP de forma asíncrona.
3. La API utiliza un objeto repositorio.
4. El repositorio valida y actualiza siguiendo pasos imperativos.
5. Las consultas y restricciones SQL expresan condiciones declarativas.
6. Las listas que se consultan pueden ordenarse o filtrarse mediante operaciones de estilo funcional.

No es necesario que cada operación use todos los paradigmas ni que cada archivo tenga un único estilo.

## Guion oral

> El proyecto es multiparadigma. Usamos orientación a objetos para representar productos, pedidos y vehículos, y para agrupar operaciones en repositorios. El estilo imperativo aparece en procesos como el despacho, donde validamos condiciones y actualizamos stock y estados en un orden explícito. Aplicamos estilo funcional al ordenar pedidos con sorted y lambda y al filtrar o transformar datos con filter y map en JavaScript. El enfoque declarativo aparece en las consultas y restricciones SQL, y el lógico en las reglas Prolog que recomiendan vehículos. Además, la interfaz responde a eventos y utiliza asincronía para comunicarse con la API.

## Fuentes y alcance de la revisión

- [Informe: clasificación original](../../Informe.md).
- [Modelo Pedido](../../Backend/modelos/pedido.py) y [modelo Entrega](../../Backend/modelos/entrega.py).
- [Pedidos: composición y despacho](../../Backend/pedidos.py).
- [Persistencia: consultas y reservas](../../Backend/persistencia.py).
- [API: ordenamiento y modelos de entrada](../../Backend/api.py).
- [SQL: relaciones y restricciones](../../Backend/schema.sql).
- [Reglas Prolog](../../Backend/razonamiento.pl) y [puente Python-Prolog](../../Backend/prolog.py).
- [JavaScript: filtros, transformaciones y eventos](../../Frontend/gestion.js) y [comunicación asíncrona](../../Frontend/api.js).

La clasificación se contrastó mediante lectura del código y de la documentación. No se modificó el comportamiento del sistema ni se ejecutaron pruebas funcionales para generar esta guía.
