# Menú de consola

## Alcance

Operar desde una terminal todas las funciones persistentes existentes sin escribir código Python. Primera versión sencilla: menú principal Inventario/Pedidos/Flota/Salir, submenús numerados, sin dependencias nuevas ni cambios en las reglas de negocio.

## Diseño y decisiones

Se elige menú de texto con input/print frente a librerías de terminal o web porque funciona con la biblioteca estándar y reutiliza SQLite existente. El inicio normal abre el menú. `--resumen` muestra las consultas anteriores y termina; `--simular-pedidos` conserva la simulación no interactiva. Ambas opciones son excluyentes. `--db` conserva su comportamiento y la carga de inventario inicial no se modifica.

Inventario: consultar existencias y características de productos; registrar producto/depósito; ingresar, retirar y trasladar cantidades positivas. Pedidos: listar, consultar detalle, crear/editar borrador, establecer/quitar productos por depósito, confirmar, cancelar, asignar/liberar vehículo, despachar y entregar. Flota: consultar, registrar vehículo/conductor, asignar/liberar conductor, actualizar estados operativos.

Cada carga pide todos sus valores antes de llamar a la operación persistente. Las cantidades son enteros positivos de 64 bits; prioridad 1 a 3 (por defecto 1); medidas positivas y finitas (admiten coma o punto decimal). Textos requeridos no vacíos. No se agregan edición de entidades ni bajas que el backend no soporte.

`0` vuelve desde un submenú o sale desde el principal. `/volver` cancela el formulario actual sin escribirlo. EOF o Ctrl+C termina limpiamente y cierra la conexión; las operaciones previas ya confirmadas se conservan. Los errores de negocio muestran el motivo, los duplicados un mensaje claro y los errores SQLite un mensaje de acceso, sin traceback. No se añaden confirmaciones adicionales a las acciones que el usuario selecciona.

Las consultas compartidas y el menú van en `Backend/consola.py`; `main.py` conserva arranque, argumentos y simulación. No se mezclan input/print con SQL. Los borradores se guardan primero y sus ítems se cargan por acciones independientes, por lo que un error posterior no borra lo ya registrado.

## Validación

Subprocess con SQLite real y entrada de texto: crear inventario/flota, pedido desde dos depósitos, reservar/asignar/despachar/entregar y reabrir; corregir borrador tras faltantes; operaciones inválidas sin cambios parciales; navegación, cancelación, EOF y modo resumen compatible. No usar la base habitual para las pruebas. Sin commits ni push para esta etapa.
