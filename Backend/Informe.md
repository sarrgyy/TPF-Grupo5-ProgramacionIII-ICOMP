# TPF-Grupo5-ProgramacionIII-ICOMP" 
# Sistema Inteligente de Gestión Logística y Distribución

## 1. Descripción del proyecto

Se propone desarrollar una aplicación destinada a gestionar y optimizar procesos de logística y distribución de productos.

El sistema permitirá administrar depósitos, productos, pedidos, vehículos, conductores y destinos de entrega, centralizando la información y facilitando la planificación de las operaciones logísticas.

Además de las funcionalidades tradicionales de gestión, se buscará incorporar herramientas de asistencia para la toma de decisiones, como la asignación de vehículos a pedidos, la optimización de rutas de distribución y la priorización de entregas según diferentes criterios.

El objetivo principal es desarrollar una solución que no solamente permita registrar y consultar operaciones, sino que también contribuya a mejorar la eficiencia de los procesos de distribución.

## 2. Funcionalidades principales

- **Gestión de productos y depósitos:** registro de productos, control de existencias y administración de ubicaciones de almacenamiento.
- **Gestión de pedidos:** creación, modificación y seguimiento de pedidos, incluyendo sus destinos y estados.
- **Gestión de vehículos y conductores:** administración de vehículos, capacidades de carga, disponibilidad y conductores asignados.
- **Planificación de entregas:** organización de pedidos según destinos, prioridades y disponibilidad de recursos.
- **Optimización de rutas:** cálculo y comparación de alternativas para determinar recorridos eficientes.
- **Asignación de recursos:** selección de vehículos y conductores según las características de los pedidos y las restricciones operativas.
- **Estadísticas y reportes:** análisis de entregas realizadas, tiempos, utilización de vehículos y rendimiento general del sistema.

## 3. Selección de lenguajes de programación

Se propone utilizar **Python y JavaScript**, dos lenguajes multiparadigma que permiten combinar programación imperativa, orientada a objetos y funcional.

La elección se fundamenta en las características particulares de cada lenguaje y en su adecuación a las distintas responsabilidades del sistema.

### Python – Backend y procesamiento de información

Python será utilizado principalmente para implementar la lógica del sistema, gestionar las operaciones logísticas y desarrollar los algoritmos de asignación y optimización.

Se elige por su sintaxis expresiva, flexibilidad y facilidad para trabajar con estructuras de datos, cálculos y procesamiento de información.

Sus principales responsabilidades serán:

- Implementar las reglas de negocio y validaciones.
- Administrar pedidos, depósitos y recursos logísticos.
- Procesar información relacionada con las entregas.
- Desarrollar algoritmos de asignación de vehículos.
- Calcular y comparar alternativas de distribución.
- Gestionar la comunicación con la base de datos.

### JavaScript – Frontend e interacción con el usuario

JavaScript será utilizado principalmente para desarrollar la interfaz de usuario y gestionar la interacción con el sistema.

Se elige por su capacidad para desarrollar aplicaciones web interactivas y por permitir combinar diferentes paradigmas de programación.

Sus principales responsabilidades serán:

- Desarrollar la interfaz de gestión logística.
- Permitir la creación y administración de pedidos.
- Visualizar vehículos, destinos y entregas.
- Presentar rutas y alternativas de distribución.
- Mostrar estadísticas y reportes.
- Gestionar eventos e interacciones del usuario.

### Comunicación entre ambos lenguajes

Se propone utilizar una arquitectura cliente-servidor, donde JavaScript se encargará de la interfaz y Python de la lógica del backend.

La comunicación entre ambos componentes se realizará mediante una API REST, intercambiando información en formato JSON.

## 4. Aplicación de los paradigmas de programación

El desarrollo permitirá integrar diferentes paradigmas, aprovechando las características de ambos lenguajes.

| Paradigma | Aplicación en el sistema |
|---|---|
| Orientado a objetos | Modelado de pedidos, productos, vehículos, conductores y depósitos. |
| Imperativo | Registro de operaciones, actualización de estados y coordinación de procesos. |
| Funcional | Filtrado, transformación, agrupación y análisis de colecciones de datos. |
| Declarativo | Consultas y expresiones que permitan especificar condiciones y resultados esperados. |

Se buscará utilizar cada paradigma en aquellos componentes donde aporte mayor claridad, expresividad y facilidad de mantenimiento.

## 5. Criterios de elección

La selección de Python y JavaScript responde a los siguientes criterios:

- **Naturaleza del problema:** el sistema requiere tanto procesamiento de información y algoritmos como una interfaz interactiva para administrar las operaciones.
- **Características de los lenguajes:** ambos ofrecen mecanismos para combinar programación imperativa, orientada a objetos y funcional.
- **Separación de responsabilidades:** permite diferenciar la lógica de negocio y el procesamiento de datos de la presentación e interacción con el usuario.
- **Flexibilidad y expresividad:** facilitan implementar algoritmos, manipular colecciones y representar las entidades del dominio.
- **Integración:** permiten establecer una comunicación entre frontend y backend mediante tecnologías web.
- **Mantenibilidad:** la separación en componentes independientes facilita las pruebas, modificaciones y futuras ampliaciones.

## 6. Alcance inicial

Se buscará desarrollar una primera versión funcional que contemple la administración de pedidos, productos, depósitos y vehículos, junto con mecanismos básicos de asignación de recursos y planificación de entregas.

Posteriormente, se podrán incorporar algoritmos más avanzados para optimizar recorridos, distribuir cargas y mejorar la planificación logística.

La arquitectura propuesta permitirá ampliar las funcionalidades sin necesidad de modificar completamente la estructura del sistema.
