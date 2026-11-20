"""Publica la API HTTP y sirve el frontend desde el mismo origen.

Cada operación abre y cierra su conexión SQLite. Los repositorios conservan
las reglas de negocio y las transacciones. Los errores se traducen a
respuestas 400, 404, 409 o 422 con detail.mensaje y faltantes cuando aplica.
"""

import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from .flota import FlotaSQLite
from .main import RUTA_DB_POR_DEFECTO, cargar_datos_base
from .modelos.productos import Producto
from .pedidos import PedidosSQLite, StockInsuficiente
from .prolog import PrologNoDisponible, recomendar_vehiculos
from .persistencia import InventarioSQLite

Identificador = Annotated[str, StringConstraints(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")]
Texto = Annotated[str, StringConstraints(min_length=1, max_length=200)]
Referencia = Annotated[str, StringConstraints(min_length=1, strip_whitespace=False)]
Cantidad = Annotated[int, Field(strict=True, gt=0, le=2**63 - 1)]
Medida = Annotated[float, Field(strict=True, gt=0, allow_inf_nan=False)]


class Entrada(BaseModel):
    """Configura los cuerpos HTTP para rechazar campos extra y recortar textos.

    Las referencias de catálogo conservan sus espacios para admitir
    identificadores ya registrados por consola.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ProductoEntrada(Entrada):
    """Describe el alta de un producto, sin ingreso implícito de stock.

    Attributes:
        id_producto (str): ID ASCII de hasta 64 caracteres: letras, dígitos o _-.
        nombre (str): Nombre no vacío de hasta 200 caracteres.
        volumen_unitario (float): Volumen positivo y finito por unidad, en m³.
        peso_unitario (float): Peso positivo y finito por unidad, en kg.
    """

    id_producto: Identificador
    nombre: Texto
    volumen_unitario: Medida
    peso_unitario: Medida


class ItemEntrada(Entrada):
    """Identifica una pareja depósito/producto y una cantidad total.

    En un ingreso, cantidad suma existencias; en un ítem de pedido, reemplaza
    la cantidad de esa pareja. Los booleanos y fracciones no son cantidades.

    Attributes:
        id_deposito (str): Referencia no vacía a un depósito existente.
        id_producto (str): Referencia no vacía a un producto existente.
        cantidad (int): Unidades entre 1 y 2**63 - 1.
    """

    id_deposito: Referencia
    id_producto: Referencia
    cantidad: Cantidad


class PedidoEntrada(Entrada):
    """Describe la cabecera de un borrador recibido por HTTP.

    Attributes:
        id_pedido (str): ID ASCII de hasta 64 caracteres: letras, dígitos o _-.
        cliente (str): Cliente no vacío de hasta 200 caracteres.
        destino (str): Dirección no vacía de hasta 200 caracteres.
        prioridad (int): Nivel de urgencia entre 1 y 3; por defecto, 1.
        hora_inicio (str | None): Inicio opcional de ventana en HH:MM.
        hora_fin (str | None): Fin opcional de ventana; debe acompañar al inicio.
        observaciones (str | None): Notas de hasta 2000 caracteres.
    """

    id_pedido: Identificador
    cliente: Texto
    destino: Texto
    prioridad: Annotated[int, Field(strict=True, ge=1, le=3)] = 1
    hora_inicio: str | None = None
    hora_fin: str | None = None
    observaciones: Annotated[str, Field(max_length=2000)] | None = None


class VehiculoEntrada(Entrada):
    """Identifica el vehículo que se desea asignar a un Confirmado.

    Attributes:
        patente (str): Referencia no vacía; admite espacios de registros previos.
    """

    patente: Referencia


def pedido_json(pedido):
    """Serializa los campos públicos de un pedido y su entrega derivada.

    Args:
        pedido (Pedido): Copia completa reconstruida por PedidosSQLite.

    Returns:
        dict[str, object]: Cabecera, metadatos, ítems, volumen y entrega opcional.
    """
    entrega = None
    if pedido.entrega is not None:
        entrega = {"estado": pedido.entrega.estado, "hora_inicio": pedido.hora_inicio,
                   "hora_fin": pedido.hora_fin, "observaciones": pedido.observaciones}
    return {"id_pedido": pedido.id_pedido, "cliente": pedido.cliente, "destino": pedido.destino,
            "prioridad": pedido.prioridad, "estado": pedido.estado, "creado_en": pedido.creado_en,
            "vehiculo_asignado": pedido.vehiculo_asignado, "volumen_total": pedido.volumen_total,
            "hora_inicio": pedido.hora_inicio, "hora_fin": pedido.hora_fin,
            "observaciones": pedido.observaciones, "productos": pedido.productos, "entrega": entrega}


def exigir_pedido(repositorio, identificador):
    """Comprueba que existe el pedido antes de ejecutar una ruta HTTP.

    Args:
        repositorio (PedidosSQLite): Repositorio de la sesión abierta.
        identificador (str): ID del pedido solicitado.

    Raises:
        HTTPException: El pedido no existe; se responde con estado 404.
    """
    if repositorio.conexion.execute("SELECT 1 FROM pedidos WHERE id_pedido=?", (identificador,)).fetchone() is None:
        raise HTTPException(404, detail={"mensaje": "No existe el pedido solicitado."})


def create_app(ruta_db: str | Path | None = None, *, cargar_base: bool = True) -> FastAPI:
    """Construye la aplicación con una base configurable y rutas estáticas.

    La base debe ser un archivo cuya carpeta exista. Las migraciones y la
    carga inicial ocurren al arrancar, no al importar el módulo. Las rutas
    del frontend se resuelven respecto del código, no del directorio actual.

    Args:
        ruta_db (str | Path | None): Ruta de archivo; precede a LOGISTICA_DB y a la ruta predeterminada.
        cargar_base (bool): Inicializa valores de schema.sql al arrancar; False permite pruebas aisladas.

    Returns:
        FastAPI: Aplicación con ciclo de vida, manejadores y rutas configurados.
    """
    ruta = Path(ruta_db if ruta_db is not None else os.environ.get("LOGISTICA_DB", RUTA_DB_POR_DEFECTO)).resolve()

    @asynccontextmanager
    async def lifespan(_app):
        """Prepara el esquema y la carga inicial al iniciar el servidor.

        Args:
            _app (FastAPI): Instancia cuyo ciclo de vida se está iniciando.

        Yields:
            None: Control al servidor después de cerrar la sesión de preparación.

        Raises:
            sqlite3.Error: No se pudo preparar o inicializar la base.
            OSError: No se pudo leer el esquema SQL.
        """
        with InventarioSQLite(ruta) as inv:
            if cargar_base:
                cargar_datos_base(inv)
        yield

    app = FastAPI(title="Gestión Logística · Grupo 5", version="1.0.0", lifespan=lifespan)

    @app.exception_handler(StockInsuficiente)
    async def stock_insuficiente(_request, error):
        """Informa un conflicto de stock con sus faltantes por HTTP.

        Args:
            _request (Request): Solicitud de origen, sin uso adicional en el manejador.
            error (StockInsuficiente): Excepción recibida del framework o repositorio.

        Returns:
            JSONResponse: Respuesta 409 con mensaje y faltantes.
        """
        return JSONResponse(status_code=409, content={"detail": {"mensaje": str(error), "faltantes": error.faltantes}})

    @app.exception_handler(ValueError)
    async def error_negocio(_request, error):
        """Traduce un rechazo de las reglas de negocio a una respuesta HTTP.

        Args:
            _request (Request): Solicitud de origen, sin uso adicional en el manejador.
            error (ValueError): Excepción recibida del framework o repositorio.

        Returns:
            JSONResponse: Respuesta 400 con mensaje.
        """
        return JSONResponse(status_code=400, content={"detail": {"mensaje": str(error)}})

    @app.exception_handler(sqlite3.IntegrityError)
    async def error_integridad(_request, _error):
        """Traduce duplicados o restricciones SQLite a un conflicto HTTP.

        Args:
            _request (Request): Solicitud de origen, sin uso adicional en el manejador.
            _error (sqlite3.IntegrityError): Excepción recibida del framework o repositorio.

        Returns:
            JSONResponse: Respuesta 409 sin exponer detalles SQL internos.
        """
        return JSONResponse(status_code=409, content={"detail": {"mensaje": "El identificador ya existe o los datos entran en conflicto."}})

    @app.exception_handler(RequestValidationError)
    async def error_entrada(_request, error):
        """Informa los campos inválidos de una solicitud HTTP.

        Args:
            _request (Request): Solicitud de origen, sin uso adicional en el manejador.
            error (RequestValidationError): Excepción recibida del framework o repositorio.

        Returns:
            JSONResponse: Respuesta 422 con los nombres de los campos.
        """
        campos = sorted({str(e["loc"][-1]) for e in error.errors()})
        return JSONResponse(status_code=422, content={"detail": {"mensaje": "Revisá los campos: " + ", ".join(campos)}})

    @app.get("/productos")
    def productos():
        """Lista los productos registrados y sus medidas unitarias.

        Returns:
            list[dict]: Catálogo sin existencias implícitas.
        """
        with InventarioSQLite(ruta) as inv:
            return [dict(id_producto=p.id_producto, nombre=p.nombre, volumen_unitario=p.volumen_unitario,
                         peso_unitario=p.peso_unitario) for p in inv.listar_productos()]

    @app.post("/productos", status_code=201)
    def registrar_producto(datos: ProductoEntrada):
        """Registra un producto sin asignarle existencias en depósitos.

        Args:
            datos (ProductoEntrada): Identidad, nombre, volumen y peso validados.

        Returns:
            dict[str, object]: Producto creado; la ruta responde con estado 201.
        """
        with InventarioSQLite(ruta) as inv:
            inv.registrar_producto(Producto(**datos.model_dump()))
        return datos.model_dump()

    @app.get("/depositos")
    def depositos():
        """Lista capacidad, ocupación física y espacio libre de cada depósito.

        Las reservas siguen ocupando lugar hasta el despacho. El espacio
        disponible se limita a cero ante diferencias de redondeo decimal.

        Returns:
            list[dict]: IDs, nombres, ubicaciones y capacidad máxima, volumen
                ocupado y espacio disponible en m³.
        """
        with InventarioSQLite(ruta) as inv:
            return [dict(id_deposito=d.id_deposito, nombre=d.nombre, ubicacion=d.ubicacion,
                         capacidad_maxima=d.capacidad_maxima, volumen_ocupado=d.volumen_ocupado,
                         espacio_disponible=max(0.0, d.espacio_disponible()))
                    for d in inv.listar_depositos()]

    @app.get("/stock")
    def stock():
        """Consulta stock físico, reservado y disponible por depósito/producto.

        Returns:
            list[dict]: Todas las parejas, incluidas las que tienen cero unidades.
        """
        with InventarioSQLite(ruta) as inv:
            return [dict(fila) for fila in inv.conexion.execute("""
                SELECT d.id_deposito, p.id_producto, COALESCE(e.cantidad,0) AS fisico,
                    COALESCE(r.cantidad,0) AS reservado,
                    COALESCE(e.cantidad,0)-COALESCE(r.cantidad,0) AS disponible
                FROM depositos d CROSS JOIN productos p
                LEFT JOIN existencias e ON e.id_deposito=d.id_deposito AND e.id_producto=p.id_producto
                LEFT JOIN (
                    SELECT i.id_deposito, i.id_producto, SUM(i.cantidad) AS cantidad
                    FROM pedido_items i JOIN pedidos pe USING(id_pedido)
                    WHERE pe.estado='Confirmado' GROUP BY i.id_deposito,i.id_producto
                ) r ON r.id_deposito=d.id_deposito AND r.id_producto=p.id_producto
                ORDER BY d.id_deposito,p.id_producto""")]

    @app.post("/stock/ingresos")
    def ingresar_stock(datos: ItemEntrada, clave: Annotated[str | None, Header(alias="Idempotency-Key", min_length=1, max_length=100)] = None):
        """Registra un ingreso y permite reintentos con la misma clave.

        Una clave repetida con los mismos datos no vuelve a sumar unidades.
        La misma clave con datos diferentes produce un conflicto 409.

        Args:
            datos (ItemEntrada): Depósito, producto y unidades positivas a ingresar.
            clave (str | None): Encabezado Idempotency-Key de hasta 100 caracteres; opcional.

        Returns:
            dict[str, int]: Stock físico, reservado y disponible después del ingreso.
        """
        with InventarioSQLite(ruta) as inv:
            cantidad = inv.actualizar_stock(datos.id_deposito, datos.id_producto, datos.cantidad, clave=clave)
            return {"fisico": cantidad, "reservado": inv.stock_reservado(datos.id_deposito, datos.id_producto),
                    "disponible": inv.stock_disponible(datos.id_deposito, datos.id_producto)}

    @app.get("/pedidos")
    def pedidos():
        """Lista pedidos completos por prioridad descendente y fecha/ID.

        Returns:
            list[dict]: Pedidos serializados en una lista nueva ordenada.
        """
        with InventarioSQLite(ruta) as inv:
            ordenados = sorted(PedidosSQLite(inv).listar_pedidos(), key=lambda p: (-p.prioridad, p.creado_en, p.id_pedido))
            return [pedido_json(p) for p in ordenados]

    @app.post("/pedidos", status_code=201)
    def crear_pedido(datos: PedidoEntrada):
        """Crea un borrador sin ítems y conserva su ventana opcional.

        Args:
            datos (PedidoEntrada): Cabecera validada; las horas se comprueban juntas.

        Returns:
            dict[str, object]: Pedido creado; la ruta responde con estado 201.
        """
        with InventarioSQLite(ruta) as inv:
            repo = PedidosSQLite(inv)
            repo.crear_borrador(**datos.model_dump())
            return pedido_json(repo.obtener_pedido(datos.id_pedido))

    @app.get("/pedidos/{identificador}")
    def obtener_pedido(identificador: str):
        """Recupera el detalle de un pedido por su identificador.

        Args:
            identificador (str): ID del pedido persistido.

        Returns:
            dict[str, object]: Pedido serializado.

        Raises:
            HTTPException: El pedido no existe; se responde con estado 404.
        """
        with InventarioSQLite(ruta) as inv:
            repo = PedidosSQLite(inv)
            exigir_pedido(repo, identificador)
            return pedido_json(repo.obtener_pedido(identificador))

    @app.put("/pedidos/{identificador}/items")
    def establecer_item(identificador: str, datos: ItemEntrada):
        """Establece la cantidad total de una pareja de ítem en un borrador.

        Args:
            identificador (str): ID del pedido Borrador.
            datos (ItemEntrada): Producto, depósito y cantidad que reemplaza la anterior.

        Returns:
            dict[str, object]: Pedido actualizado sin confirmar ni reservar stock.
        """
        with InventarioSQLite(ruta) as inv:
            repo = PedidosSQLite(inv)
            exigir_pedido(repo, identificador)
            repo.establecer_producto(identificador, **datos.model_dump())
            return pedido_json(repo.obtener_pedido(identificador))

    @app.put("/pedidos/{identificador}/vehiculo")
    def asignar_vehiculo(identificador: str, datos: VehiculoEntrada):
        """Asigna un vehículo disponible y con conductor a un Confirmado.

        Args:
            identificador (str): ID del pedido Confirmado.
            datos (VehiculoEntrada): Patente solicitada.

        Returns:
            dict[str, object]: Pedido con vehículo asignado, aún sin despachar.
        """
        with InventarioSQLite(ruta) as inv:
            repo = PedidosSQLite(inv)
            exigir_pedido(repo, identificador)
            repo.asignar_vehiculo(identificador, datos.patente)
            return pedido_json(repo.obtener_pedido(identificador))

    def transicion(identificador, operacion):
        """Ejecuta una transición del repositorio y devuelve el pedido actual.

        Args:
            identificador (str): ID del pedido persistido.
            operacion (str): Nombre interno: confirmar, cancelar, despachar o entregar.

        Returns:
            dict[str, object]: Pedido después de completar la transacción.

        Raises:
            HTTPException: El pedido no existe; se responde con estado 404.
        """
        with InventarioSQLite(ruta) as inv:
            repo = PedidosSQLite(inv)
            exigir_pedido(repo, identificador)
            getattr(repo, operacion)(identificador)
            return pedido_json(repo.obtener_pedido(identificador))

    @app.post("/pedidos/{identificador}/confirmar")
    def confirmar(identificador: str):
        """Confirma un borrador y reserva todos sus ítems o informa faltantes.

        Args:
            identificador (str): ID del pedido sobre el que se opera.

        Returns:
            dict[str, object]: Pedido serializado después de la transición.
        """
        return transicion(identificador, "confirmar")

    @app.post("/pedidos/{identificador}/cancelar")
    def cancelar(identificador: str):
        """Cancela un Borrador o Confirmado y libera sus reservas y vehículo.

        Args:
            identificador (str): ID del pedido sobre el que se opera.

        Returns:
            dict[str, object]: Pedido serializado después de la transición.
        """
        return transicion(identificador, "cancelar")

    @app.post("/pedidos/{identificador}/despachar")
    def despachar(identificador: str):
        """Despacha un Confirmado, descuenta su stock y deja el vehículo En Ruta.

        Args:
            identificador (str): ID del pedido sobre el que se opera.

        Returns:
            dict[str, object]: Pedido serializado después de la transición.
        """
        return transicion(identificador, "despachar")

    @app.post("/pedidos/{identificador}/entregar")
    def entregar(identificador: str):
        """Finaliza un Despachado y deja el vehículo Disponible.

        Args:
            identificador (str): ID del pedido sobre el que se opera.

        Returns:
            dict[str, object]: Pedido serializado después de la transición.
        """
        return transicion(identificador, "entregar")

    @app.get("/pedidos/{identificador}/vehiculos-recomendados")
    def vehiculos_recomendados(identificador: str):
        """Recomienda con Prolog vehículos aptos para un pedido Confirmado."""
        with InventarioSQLite(ruta) as inv:
            repo = PedidosSQLite(inv)
            exigir_pedido(repo, identificador)
            pedido = repo.obtener_pedido(identificador)
            if pedido.estado != "Confirmado":
                raise HTTPException(409, detail={"mensaje": "Confirmá el pedido antes de buscar vehículos."})
            try:
                candidatos = recomendar_vehiculos(
                    pedido.volumen_total, FlotaSQLite(inv).listar_vehiculos()
                )
            except PrologNoDisponible as error:
                raise HTTPException(503, detail={"mensaje": str(error)}) from error
            return {"id_pedido": identificador, "volumen_pedido": pedido.volumen_total,
                    "motor": "SWI-Prolog", "recomendaciones": candidatos}

    @app.get("/vehiculos")
    def vehiculos():
        """Lista vehículos con su conductor, pedido activo y volumen ocupado.

        Returns:
            list[dict]: Estado y asignaciones de cada vehículo consultado.
        """
        with InventarioSQLite(ruta) as inv:
            return [dict(patente=v.patente, capacidad_maxima=v.capacidad_maxima, estado=v.estado,
                         conductor_asignado=v.conductor_asignado, pedido_asignado=v.pedido_asignado,
                         volumen_ocupado=v.volumen_ocupado) for v in FlotaSQLite(inv).listar_vehiculos()]

    @app.get("/reportes/kpis")
    def kpis():
        """Calcula los cuatro conteos de operaciones mostrados en Inicio.

        Pendientes incluye Borrador y Confirmado. Productos con stock cuenta
        IDs con existencia física positiva en al menos un depósito.

        Returns:
            dict[str, int]: Pendientes, vehículos asignados, productos con stock y entregados.
        """
        with InventarioSQLite(ruta) as inv:
            fila = inv.conexion.execute("""SELECT
                (SELECT COUNT(*) FROM pedidos WHERE estado IN ('Borrador','Confirmado')) AS pedidos_pendientes,
                (SELECT COUNT(DISTINCT patente_vehiculo) FROM pedidos WHERE estado IN ('Confirmado','Despachado')) AS vehiculos_asignados,
                (SELECT COUNT(DISTINCT id_producto) FROM existencias WHERE cantidad>0) AS productos_con_stock,
                (SELECT COUNT(*) FROM pedidos WHERE estado='Entregado') AS pedidos_entregados""").fetchone()
            return dict(fila)

    app.mount("/", StaticFiles(directory=Path(__file__).resolve().parents[1] / "Frontend", html=True), name="frontend")
    return app


app = create_app()
