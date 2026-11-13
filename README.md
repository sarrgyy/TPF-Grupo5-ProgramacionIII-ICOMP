# Sistema de Gestión Logística y Distribución

Trabajo Práctico Final del **Grupo 5 — Programación III — ICOMP**.

El proyecto busca centralizar la gestión de productos, depósitos, pedidos, vehículos y conductores para facilitar la planificación de operaciones de distribución. A futuro, se propone incorporar herramientas de asignación de recursos y optimización de rutas.

Actualmente cuenta con un **prototipo de consola en Python**, con modelos del dominio y una demostración de asignación de pedidos según la disponibilidad y el volumen libre de los vehículos.

## Funcionalidades implementadas

- **Productos:** registro de nombre, volumen, peso y stock; actualización de existencias con control para evitar stock negativo.
- **Depósitos:** consulta de espacio disponible, verificación de capacidad y actualización de la capacidad máxima.
- **Pedidos:** registro de cliente, destino y prioridad; incorporación de productos, cálculo del volumen total y actualización del estado.
- **Vehículos:** control de volumen ocupado, asignación y liberación de pedidos, actualización del estado y vinculación de un conductor.
- **Conductores:** asignación y liberación de un vehículo, actualización del estado y consulta de información.
- **Asignación básica:** recorrido de los pedidos y la flota para asignar cada pedido al primer vehículo disponible con capacidad suficiente.

## Tecnologías y paradigmas

La implementación actual utiliza **Python**, sin dependencias externas.

| Paradigma | Aplicación actual |
| --- | --- |
| Orientado a objetos | Clases que representan las entidades y sus operaciones. |
| Imperativo | Secuencia de la demostración, actualización de existencias y asignación mediante ciclos y condicionales. |

La propuesta contempla un frontend en **JavaScript** conectado al backend mediante una **API REST con JSON**, además del uso de enfoques funcionales y declarativos. Estos componentes todavía no están implementados.

## Requisitos

- Python 3. La demostración fue verificada con **Python 3.12.3**.
- Git, si se desea clonar el repositorio.

No es necesario instalar paquetes con `pip`, configurar una base de datos ni definir variables de entorno.

## Instalación y ejecución

1. Clonar el repositorio y entrar en su carpeta:

   ```bash
   git clone https://github.com/sarrgyy/TPF-Grupo5-ProgramacionIII-ICOMP.git
   cd TPF-Grupo5-ProgramacionIII-ICOMP
   ```

2. Ejecutar la demostración desde la raíz del proyecto:

   ```bash
   python Backend/main.py
   ```

   En Windows también se puede usar `py Backend/main.py`; en sistemas donde corresponda, `python3 Backend/main.py`.

El programa utiliza datos de ejemplo definidos en el código y muestra los resultados por consola, sin solicitar datos al usuario. Para modificar el escenario, editar `Backend/main.py`.

### Qué muestra la demostración

1. Crea un depósito y dos productos: cajas de leche y bolsas de harina.
2. Configura dos vehículos y sus conductores.
3. Crea los pedidos `P-100` y `P-101`, agrega productos y descuenta las unidades del stock.
4. Intenta asignar cada pedido a un vehículo según su estado y volumen disponible.
5. Muestra la información de los conductores y el inventario final.

Con los datos actuales, los resultados esperados son:

| Elemento | Resultado |
| --- | --- |
| Pedido `P-100` | Volumen de 16.0; asignado al vehículo `AB123CD`, con 4.0 de capacidad restante. |
| Pedido `P-101` | Volumen de 25.0; queda pendiente porque ningún vehículo tiene capacidad suficiente. |
| Cajas de leche | Stock final de 430 unidades. |
| Bolsas de harina | Stock final de 770 unidades. |

La alerta por falta de capacidad de `P-101` forma parte del escenario de ejemplo.

## Estructura del repositorio

```text
TPF-Grupo5-ProgramacionIII-ICOMP/
├── README.md               # Presentación e instrucciones de uso
├── Informe.md              # Propuesta, alcance y fundamentos del proyecto
└── Backend/
    ├── main.py             # Punto de entrada de la demostración
    └── modelos/
        ├── conductor.py    # Modelo Conductor
        ├── deposito.py     # Modelo Deposito
        ├── entrega.py      # Archivo reservado; sin implementación
        ├── main.py         # Copia previa de la demo con imports inconsistentes
        ├── pedido.py       # Modelo Pedido
        ├── productos.py    # Modelo Producto
        └── vehiculo.py     # Modelo Vehiculo
```

El punto de entrada es **`Backend/main.py`**. El archivo `Backend/modelos/main.py` conserva una versión previa con importaciones que no coinciden con los modelos actuales.

## Alcance y limitaciones actuales

- Los datos se mantienen en memoria y se reinician en cada ejecución.
- La capacidad de los vehículos se evalúa por volumen; el peso registrado en los productos todavía no interviene en la asignación.
- La prioridad se almacena en cada pedido, pero la asignación respeta el orden de la lista de pedidos, sin ordenarlos por prioridad.
- El stock se descuenta al agregar productos a los pedidos en la demo, incluso si después no se consigue un vehículo.
- El depósito dispone de operaciones de capacidad, pero la demo todavía no vincula el inventario con su volumen ocupado.
- No hay una suite de pruebas automatizadas incluida en el repositorio.

## Próximas etapas

- Desarrollar la interfaz web en JavaScript y la API REST en Python.
- Incorporar persistencia en una base de datos.
- Completar el modelo y el seguimiento de entregas.
- Integrar el inventario con la ocupación de los depósitos.
- Ampliar la asignación con criterios de prioridad, peso y disponibilidad de recursos.
- Incorporar planificación y optimización de rutas.
- Agregar estadísticas, reportes y pruebas automatizadas.

## Documentación del trabajo

En [Informe.md](Informe.md) se detallan la propuesta original, la elección de lenguajes, los paradigmas previstos y el alcance inicial del trabajo.
