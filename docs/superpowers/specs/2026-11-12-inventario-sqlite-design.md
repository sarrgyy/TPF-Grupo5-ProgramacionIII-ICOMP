# Persistencia de inventario con SQLite

## Objetivo y alcance acordado

Guardar productos y existencias de varios depósitos entre ejecuciones. Primera etapa de la persistencia: pedidos, vehículos, conductores y entregas siguen en memoria.

## Alternativas

- SQLite: base local en un archivo, sin servidor ni dependencias externas. Elegida por el usuario para esta etapa.
- PostgreSQL: servidor centralizado con configuración adicional. No elegido para esta etapa.

## Diseño

Una base con tres tablas: `productos` (id, nombre, volumen y peso unitarios), `depositos` (id, nombre, ubicación, capacidad máxima) y `existencias` (id de depósito, id de producto, cantidad entera no negativa). La pareja depósito/producto es única y las referencias se validan mediante claves foráneas.

`Producto` deja de tener stock global. El inventario obtiene stock por depósito y total por producto; calcula la ocupación del depósito sumando cantidad por volumen unitario. Los ingresos no pueden superar la capacidad y los retiros no pueden dejar stock negativo. Un traslado actualiza origen y destino en una sola transacción. Las escrituras toman el bloqueo antes de consultar existencias y capacidad.

Decisiones de implementación: identificadores existentes de texto; capacidades, volúmenes y pesos positivos y finitos; cantidades enteras; errores de negocio con `ValueError`; duplicados con `sqlite3.IntegrityError`. Las consultas de ids inexistentes fallan, mientras que un producto registrado sin existencias en un depósito registrado tiene stock cero. No se incluyen bajas ni edición de características físicas en esta etapa.

## Integración y límites

La demo carga ejemplos solamente si el inventario está vacío, en una transacción. Los arranques posteriores no reponen ni descuentan stock automáticamente. Se conserva la simulación logística como opción que opera sobre una copia en memoria del stock, porque aún no persistimos pedidos. La ruta por defecto se resuelve desde el código y se puede cambiar con `--db`. El archivo de datos local no se versiona.

Se mantiene la rama `persistencia_en_db`; el usuario realiza los commits. No se instala ningún paquete. Las unidades de volumen y capacidad deben ser consistentes; las comparaciones contemplan el pequeño error de representación de los números decimales en Python/SQLite.

## Verificación

Pruebas con archivos temporales y SQLite real: reapertura, stock independiente por depósito, capacidad, entradas inválidas, duplicados, referencias inexistentes, traslados completos y rollback. Integración: dos ejecuciones contra el mismo archivo no alteran el inventario; la simulación tampoco lo modifica.
