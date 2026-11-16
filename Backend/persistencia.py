"""Administra inventario, conexión y migraciones aditivas de SQLite.

InventarioSQLite guarda existencias por depósito y calcula reservas desde
pedidos Confirmados. PedidosSQLite y FlotaSQLite comparten su conexión.
Los repositorios propagan sqlite3.Error ante problemas de acceso a datos.
"""

import math
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .modelos.deposito import Deposito
from .modelos.productos import Producto


class InventarioSQLite:
    """Gestiona productos, depósitos y existencias persistentes.

    Usar como gestor de contexto para cerrar la conexión. Volumen y capacidad
    comparten unidad; las reservas siguen ocupando espacio físico. Las consultas
    devuelven copias y las mutaciones usan transacciones. Los errores de acceso
    a datos se propagan como sqlite3.Error.

    Attributes:
        conexion (sqlite3.Connection): Sesión compartida con pedidos y flota.
    """

    def __init__(self, ruta):
        """Abre la conexión y prepara tablas y migraciones sin borrar datos.

        Args:
            ruta (str | pathlib.Path): Archivo SQLite o :memory:; la carpeta
                debe existir.

        Raises:
            sqlite3.Error: Falló la apertura o preparación de la base.
            OSError: No se pudo leer schema.sql.
        """
        self.conexion = sqlite3.connect(ruta)
        self.conexion.row_factory = sqlite3.Row
        try:
            self.conexion.executescript(
                Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
            )
            # Bases anteriores conservan sus tablas y reciben solo la nueva columna.
            with self._transaccion():
                columnas = {fila["name"] for fila in self.conexion.execute("PRAGMA table_info(pedidos)")}
                if "patente_vehiculo" not in columnas:
                    self.conexion.execute(
                        "ALTER TABLE pedidos ADD COLUMN patente_vehiculo TEXT REFERENCES vehiculos(patente)"
                    )
                self.conexion.execute(
                    """CREATE UNIQUE INDEX IF NOT EXISTS pedido_vehiculo_activo
                    ON pedidos(patente_vehiculo)
                    WHERE estado IN ('Confirmado', 'Despachado')"""
                )
        except Exception:
            self.close()
            raise

    def __enter__(self):
        """Devuelve la misma sesión para utilizarla en un bloque with.

        Returns:
            InventarioSQLite: Sesión abierta.
        """
        return self

    def __exit__(self, tipo, valor, traceback):
        """Cierra la conexión al salir del bloque sin suprimir excepciones.

        Args:
            tipo (type[BaseException] | None): Tipo de excepción recibida al salir del
                contexto.
            valor (BaseException | None): Excepción recibida, si la hubiera.
            traceback (types.TracebackType | None): Traza recibida al salir del
                contexto.
        """
        self.close()

    def close(self):
        """Cierra la conexión compartida; no admite operaciones posteriores."""
        self.conexion.close()

    @contextmanager
    def _transaccion(self):
        """Agrupa la escritura con BEGIN IMMEDIATE y rollback ante errores.

        No admite transacciones anidadas. El bloqueo precede a las lecturas para
        que otra escritura no invalide las comprobaciones.

        Yields:
            None: Contexto con confirmación o rollback automático.
        """
        with self.conexion:
            self.conexion.execute("BEGIN IMMEDIATE")
            yield

    @staticmethod
    def _validar_medida(valor):
        """Exige una medida positiva y finita, excluyendo booleanos.

        Args:
            valor (object): Valor que debe validarse.

        Raises:
            ValueError: La medida no es un número positivo y finito.
        """
        if (isinstance(valor, bool) or not isinstance(valor, (int, float))
                or not math.isfinite(valor) or valor <= 0):
            raise ValueError("Las medidas deben ser números positivos y finitos.")

    @staticmethod
    def _validar_cantidad(cantidad):
        """Exige un entero con signo de 64 bits, excluyendo booleanos.

        Args:
            cantidad (int): Entero con signo que debe caber en 64 bits.

        Raises:
            ValueError: La cantidad no es un entero admitido por SQLite.
        """
        if type(cantidad) is not int or not -(2**63) <= cantidad < 2**63:
            raise ValueError("La cantidad debe ser un entero de 64 bits.")

    def _insertar_producto(self, producto):
        """Inserta el producto dentro de la transacción del llamador.

        Args:
            producto (Producto): Datos y características del producto.

        Raises:
            ValueError: Peso o volumen inválidos.
            sqlite3.IntegrityError: Clave duplicada o datos inválidos.
        """
        self._validar_medida(producto.volumen_unitario)
        self._validar_medida(producto.peso_unitario)
        self.conexion.execute(
            "INSERT INTO productos VALUES (?, ?, ?, ?)",
            (producto.id_producto, producto.nombre,
             producto.volumen_unitario, producto.peso_unitario),
        )

    def registrar_producto(self, producto):
        """Guarda un producto nuevo sin asignarle existencias.

        Args:
            producto (Producto): Datos y características del producto.

        Raises:
            ValueError: Peso o volumen inválidos.
            sqlite3.IntegrityError: Identificador repetido o datos inválidos.
        """
        with self._transaccion():
            self._insertar_producto(producto)

    def _insertar_deposito(self, deposito):
        """Inserta el depósito dentro de la transacción del llamador.

        Args:
            deposito (Deposito): Datos y capacidad del depósito.

        Raises:
            ValueError: Capacidad inválida.
            sqlite3.IntegrityError: Clave duplicada o datos inválidos.
        """
        self._validar_medida(deposito.capacidad_maxima)
        self.conexion.execute(
            "INSERT INTO depositos VALUES (?, ?, ?, ?)",
            (deposito.id_deposito, deposito.nombre,
             deposito.ubicacion, deposito.capacidad_maxima),
        )

    def registrar_deposito(self, deposito):
        """Guarda un depósito nuevo, inicialmente sin mercadería.

        Args:
            deposito (Deposito): Datos y capacidad del depósito.

        Raises:
            ValueError: Capacidad inválida.
            sqlite3.IntegrityError: Identificador repetido o datos inválidos.
        """
        with self._transaccion():
            self._insertar_deposito(deposito)

    def obtener_producto(self, id_producto):
        """Recupera una copia de las características de un producto.

        Args:
            id_producto (str): Identificador del producto.

        Returns:
            Producto: Copia independiente de las filas guardadas.

        Raises:
            ValueError: El producto no existe.
        """
        fila = self.conexion.execute(
            "SELECT * FROM productos WHERE id_producto = ?", (id_producto,)
        ).fetchone()
        if fila is None:
            raise ValueError(f"No existe el producto {id_producto}.")
        return Producto(**dict(fila))

    def listar_productos(self):
        """Lista copias de los productos ordenadas por identificador.

        Returns:
            list[Producto]: Catálogo registrado; puede estar vacío.
        """
        filas = self.conexion.execute("SELECT * FROM productos ORDER BY id_producto")
        return [Producto(**dict(fila)) for fila in filas]

    def obtener_deposito(self, id_deposito):
        """Recupera un depósito y calcula su volumen físico ocupado.

        Args:
            id_deposito (str): Identificador del depósito.

        Returns:
            Deposito: Copia con ocupación calculada desde las existencias.

        Raises:
            ValueError: El depósito no existe.
        """
        fila = self.conexion.execute(
            """SELECT d.*, COALESCE((
                SELECT SUM(e.cantidad * p.volumen_unitario)
                FROM existencias e JOIN productos p USING (id_producto)
                WHERE e.id_deposito = d.id_deposito
            ), 0) AS volumen_ocupado
            FROM depositos d WHERE d.id_deposito = ?""", (id_deposito,)
        ).fetchone()
        if fila is None:
            raise ValueError(f"No existe el depósito {id_deposito}.")
        deposito = Deposito(fila["id_deposito"], fila["nombre"], fila["ubicacion"],
                            fila["capacidad_maxima"])
        deposito.volumen_ocupado = fila["volumen_ocupado"]
        return deposito

    def listar_depositos(self):
        """Lista copias de los depósitos con su ocupación actual.

        Returns:
            list[Deposito]: Depósitos ordenados por identificador.
        """
        ids = self.conexion.execute(
            "SELECT id_deposito FROM depositos ORDER BY id_deposito"
        ).fetchall()
        return [self.obtener_deposito(fila[0]) for fila in ids]

    def stock(self, id_deposito, id_producto):
        """Consulta el stock físico de una pareja depósito/producto registrada.

        Args:
            id_deposito (str): Identificador del depósito.
            id_producto (str): Identificador del producto.

        Returns:
            int: Unidades físicas; cero si esa pareja no tiene existencias.

        Raises:
            ValueError: El depósito o el producto no está registrado.
        """
        self.obtener_deposito(id_deposito)
        self.obtener_producto(id_producto)
        fila = self.conexion.execute(
            "SELECT cantidad FROM existencias WHERE id_deposito = ? AND id_producto = ?",
            (id_deposito, id_producto),
        ).fetchone()
        return fila[0] if fila else 0

    def stock_total(self, id_producto):
        """Suma stock entre depósitos con enteros Python, sin desbordar.

        Args:
            id_producto (str): Identificador del producto.

        Returns:
            int: Total físico exacto del producto.

        Raises:
            ValueError: El producto no existe.
        """
        self.obtener_producto(id_producto)
        filas = self.conexion.execute(
            "SELECT cantidad FROM existencias WHERE id_producto = ?",
            (id_producto,),
        )
        return sum(fila[0] for fila in filas)

    def stock_reservado(self, id_deposito, id_producto):
        """Suma las unidades comprometidas en pedidos Confirmados.

        Args:
            id_deposito (str): Identificador del depósito.
            id_producto (str): Identificador del producto.

        Returns:
            int: Reservas activas de esa pareja depósito/producto.

        Raises:
            ValueError: El depósito o el producto no existe.
        """
        self.obtener_deposito(id_deposito)
        self.obtener_producto(id_producto)
        filas = self.conexion.execute(
            """SELECT i.cantidad FROM pedido_items i
            JOIN pedidos p USING (id_pedido)
            WHERE i.id_deposito = ? AND i.id_producto = ? AND p.estado = 'Confirmado'""",
            (id_deposito, id_producto),
        )
        return sum(fila[0] for fila in filas)

    def stock_disponible(self, id_deposito, id_producto):
        """Calcula las unidades físicas que no están reservadas.

        Args:
            id_deposito (str): Identificador del depósito.
            id_producto (str): Identificador del producto.

        Returns:
            int: Stock físico menos reservas activas.

        Raises:
            ValueError: El depósito o el producto no existe.
        """
        return (self.stock(id_deposito, id_producto)
                - self.stock_reservado(id_deposito, id_producto))

    def _modificar_stock(self, id_deposito, id_producto, cantidad):
        """Valida y cambia existencias dentro de la transacción del llamador.

        El llamador mantiene la transacción. La comparación de volumen admite
        tolerancia relativa 1e-12 por representación decimal.

        Args:
            id_deposito (str): Identificador del depósito.
            id_producto (str): Identificador del producto.
            cantidad (int): Variación firmada; positiva ingresa y negativa retira.

        Returns:
            int: Stock físico resultante.

        Raises:
            ValueError: Referencias, cantidad, stock, reservas o capacidad
                impiden el movimiento.
        """
        self._validar_cantidad(cantidad)
        producto = self.obtener_producto(id_producto)
        deposito = self.obtener_deposito(id_deposito)
        nuevo_stock = self.stock(id_deposito, id_producto) + cantidad
        self._validar_cantidad(nuevo_stock)
        if nuevo_stock < 0:
            raise ValueError("Stock insuficiente en el depósito de origen.")
        if cantidad < 0 and nuevo_stock < self.stock_reservado(id_deposito, id_producto):
            raise ValueError("La operación consumiría mercadería reservada para pedidos.")
        nuevo_volumen = deposito.volumen_ocupado + cantidad * producto.volumen_unitario
        if (not math.isfinite(nuevo_volumen)
                or (nuevo_volumen > deposito.capacidad_maxima
                    and not math.isclose(nuevo_volumen, deposito.capacidad_maxima,
                                         rel_tol=1e-12, abs_tol=0))):
            raise ValueError("La operación supera la capacidad del depósito.")
        self.conexion.execute(
            """INSERT INTO existencias (id_deposito, id_producto, cantidad)
            VALUES (?, ?, ?) ON CONFLICT (id_deposito, id_producto)
            DO UPDATE SET cantidad = excluded.cantidad""",
            (id_deposito, id_producto, nuevo_stock),
        )
        return nuevo_stock

    def actualizar_stock(self, id_deposito, id_producto, cantidad):
        """Guarda un ingreso positivo o retiro negativo en una transacción.

        Args:
            id_deposito (str): Identificador del depósito.
            id_producto (str): Identificador del producto.
            cantidad (int): Variación firmada; positiva ingresa y negativa retira.

        Returns:
            int: Stock físico resultante.

        Raises:
            ValueError: Referencias, cantidad, reservas o capacidad impiden el
                movimiento.
        """
        with self._transaccion():
            return self._modificar_stock(id_deposito, id_producto, cantidad)

    def transferir(self, origen, destino, id_producto, cantidad):
        """Traslada unidades y revierte el origen si falla la entrada en destino.

        Args:
            origen (str): Identificador del depósito de salida.
            destino (str): Identificador del depósito de destino.
            id_producto (str): Identificador del producto.
            cantidad (int): Cantidad positiva de unidades, entera de 64 bits.

        Raises:
            ValueError: Cantidad no positiva, depósitos iguales o movimiento no
                permitido.
        """
        self._validar_cantidad(cantidad)
        if cantidad <= 0 or origen == destino:
            raise ValueError("Un traslado requiere cantidad positiva y depósitos diferentes.")
        with self._transaccion():
            self._modificar_stock(origen, id_producto, -cantidad)
            self._modificar_stock(destino, id_producto, cantidad)

    def cargar_iniciales(self, productos, depositos, existencias):
        """Carga todo el escenario solo si no hay productos ni depósitos.

        No repone stock en otras ejecuciones. Un error revierte todo el
        escenario.

        Args:
            productos (Iterable[Producto]): Catálogo inicial.
            depositos (Iterable[Deposito]): Depósitos iniciales.
            existencias (Iterable[tuple[str, str, int]]): Depósito, producto y
                cantidad inicial.

        Returns:
            bool: True si se cargó; False si ya había datos.

        Raises:
            ValueError: Datos iniciales o movimientos inválidos.
            sqlite3.IntegrityError: Identificadores duplicados o datos
                inválidos.
        """
        with self._transaccion():
            if self.listar_productos() or self.listar_depositos():
                return False
            for producto in productos:
                self._insertar_producto(producto)
            for deposito in depositos:
                self._insertar_deposito(deposito)
            for id_deposito, id_producto, cantidad in existencias:
                self._modificar_stock(id_deposito, id_producto, cantidad)
        return True
