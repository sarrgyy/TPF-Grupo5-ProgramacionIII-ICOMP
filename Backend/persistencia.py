"""Persistencia del inventario. Las operaciones de negocio usan SQL parametrizado."""

import math
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .modelos.deposito import Deposito
from .modelos.productos import Producto


class InventarioSQLite:
    def __init__(self, ruta):
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
        return self

    def __exit__(self, tipo, valor, traceback):
        self.close()

    def close(self):
        self.conexion.close()

    @contextmanager
    def _transaccion(self):
        # El bloqueo precede a las lecturas: otra escritura no puede invalidarlas.
        with self.conexion:
            self.conexion.execute("BEGIN IMMEDIATE")
            yield

    @staticmethod
    def _validar_medida(valor):
        if (isinstance(valor, bool) or not isinstance(valor, (int, float))
                or not math.isfinite(valor) or valor <= 0):
            raise ValueError("Las medidas deben ser números positivos y finitos.")

    @staticmethod
    def _validar_cantidad(cantidad):
        if type(cantidad) is not int or not -(2**63) <= cantidad < 2**63:
            raise ValueError("La cantidad debe ser un entero de 64 bits.")

    def _insertar_producto(self, producto):
        self._validar_medida(producto.volumen_unitario)
        self._validar_medida(producto.peso_unitario)
        self.conexion.execute(
            "INSERT INTO productos VALUES (?, ?, ?, ?)",
            (producto.id_producto, producto.nombre,
             producto.volumen_unitario, producto.peso_unitario),
        )

    def registrar_producto(self, producto):
        with self._transaccion():
            self._insertar_producto(producto)

    def _insertar_deposito(self, deposito):
        self._validar_medida(deposito.capacidad_maxima)
        self.conexion.execute(
            "INSERT INTO depositos VALUES (?, ?, ?, ?)",
            (deposito.id_deposito, deposito.nombre,
             deposito.ubicacion, deposito.capacidad_maxima),
        )

    def registrar_deposito(self, deposito):
        with self._transaccion():
            self._insertar_deposito(deposito)

    def obtener_producto(self, id_producto):
        fila = self.conexion.execute(
            "SELECT * FROM productos WHERE id_producto = ?", (id_producto,)
        ).fetchone()
        if fila is None:
            raise ValueError(f"No existe el producto {id_producto}.")
        return Producto(**dict(fila))

    def listar_productos(self):
        filas = self.conexion.execute("SELECT * FROM productos ORDER BY id_producto")
        return [Producto(**dict(fila)) for fila in filas]

    def obtener_deposito(self, id_deposito):
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
        ids = self.conexion.execute(
            "SELECT id_deposito FROM depositos ORDER BY id_deposito"
        ).fetchall()
        return [self.obtener_deposito(fila[0]) for fila in ids]

    def stock(self, id_deposito, id_producto):
        self.obtener_deposito(id_deposito)
        self.obtener_producto(id_producto)
        fila = self.conexion.execute(
            "SELECT cantidad FROM existencias WHERE id_deposito = ? AND id_producto = ?",
            (id_deposito, id_producto),
        ).fetchone()
        return fila[0] if fila else 0

    def stock_total(self, id_producto):
        self.obtener_producto(id_producto)
        filas = self.conexion.execute(
            "SELECT cantidad FROM existencias WHERE id_producto = ?",
            (id_producto,),
        )
        return sum(fila[0] for fila in filas)

    def stock_reservado(self, id_deposito, id_producto):
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
        return (self.stock(id_deposito, id_producto)
                - self.stock_reservado(id_deposito, id_producto))

    def _modificar_stock(self, id_deposito, id_producto, cantidad):
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
        """Suma ingresos positivos o retiros negativos; devuelve el stock resultante."""
        with self._transaccion():
            return self._modificar_stock(id_deposito, id_producto, cantidad)

    def transferir(self, origen, destino, id_producto, cantidad):
        self._validar_cantidad(cantidad)
        if cantidad <= 0 or origen == destino:
            raise ValueError("Un traslado requiere cantidad positiva y depósitos diferentes.")
        with self._transaccion():
            self._modificar_stock(origen, id_producto, -cantidad)
            self._modificar_stock(destino, id_producto, cantidad)

    def cargar_iniciales(self, productos, depositos, existencias):
        """Carga un escenario completo solo si no hay productos ni depósitos."""
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
