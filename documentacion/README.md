# Documentación del proyecto

Esta carpeta reúne la documentación generada del Sistema de Gestión Logística y Distribución. Los archivos se organizan por tema.

## UML y base de datos

Todo lo referido al diagrama de tablas y sus relaciones está en [`uml/`](uml/).

| Documento | Contenido |
|---|---|
| [Diagrama UML y detalle del esquema](uml/diagrama-base-datos.md) | Tablas, campos, claves, multiplicidades, restricciones y fuente editable en Mermaid. |
| [Imagen del diagrama](uml/diagrama-base-datos.png) | Versión PNG para consultar o incorporar a una presentación. |
| [Diagrama vectorial](uml/diagrama-base-datos.svg) | Versión ampliable sin perder calidad. |
| [Guía para defender la base de datos](uml/guia-defensa-base-datos.md) | Por qué existe cada relación, ejemplos, explicación de `inicializaciones`, preguntas posibles y guion oral. |

## Implementación y tecnologías

Las explicaciones sobre cómo está construido el sistema están en [`implementacion/`](implementacion/).

| Documento | Contenido |
|---|---|
| [Guía para defender las tecnologías](implementacion/guia-defensa-tecnologias.md) | Qué usamos, para qué sirve, qué hace y cómo justificar cada elección: Python, HTML, CSS, JavaScript, FastAPI, Pydantic, Uvicorn, SQLite, SQL y herramientas de pruebas. Incluye el recorrido de una solicitud y un guion oral. |
| [Guía para defender los paradigmas](implementacion/guia-defensa-paradigmas.md) | Orientación a objetos, estilo imperativo, funcional y declarativo, con ejemplos del código, eventos, asincronía, preguntas posibles y guion oral. |

## Orden sugerido para preparar la defensa

1. Leer la [guía de tecnologías](implementacion/guia-defensa-tecnologias.md) para entender la arquitectura general.
2. Abrir el [diagrama UML](uml/diagrama-base-datos.png) para ubicar las tablas.
3. Repasar la [guía de base de datos](uml/guia-defensa-base-datos.md) para explicar los vínculos y practicar las preguntas.
4. Leer la [guía de paradigmas](implementacion/guia-defensa-paradigmas.md) para relacionar los conceptos de la materia con ejemplos de la implementación.

## Cómo ubicar la documentación futura

- Los diagramas y sus explicaciones se guardan en `uml/`, junto con sus imágenes y fuentes editables.
- Las explicaciones de arquitectura, tecnologías y funcionamiento del código se guardan en `implementacion/`.
- Cuando aparezca otro tema, se crea una carpeta con un nombre descriptivo, por ejemplo `api/`, `pruebas/` o `manuales/`, al incorporar su primer documento.
- Cada documento nuevo debe tener un nombre descriptivo y un enlace en este índice. Al mover archivos, deben actualizarse sus enlaces e imágenes.

## Documentación previa del repositorio

- [README principal](../README.md): instalación, ejecución y operación del sistema.
- [Informe del proyecto](../Informe.md): arquitectura, reglas del negocio, paradigmas y alcance.
- [Verificación](../docs/VERIFICACION.md) y [pruebas exhaustivas](../docs/PRUEBAS_EXHAUSTIVAS.md): registros de comprobaciones anteriores.
