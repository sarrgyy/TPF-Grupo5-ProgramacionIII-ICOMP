"""Pedidos persistentes con abastecimiento manual desde varios depósitos."""

import math

from .modelos.pedido import Pedido
from .flota import FlotaSQLite


class StockInsuficiente(ValueError):
    def __init__(self, faltantes):
        self.faltantes = faltantes
        detalle = "; ".join(
            f"{f['id_producto']} en {f['id_deposito']}: faltan {f['faltan']} unidades "
            f"(solicitadas {f['solicitadas']}, disponibles {f['disponibles']})"
            for f in faltantes
        )
        super().__init__("No se confirmó el pedido. " + detalle)


class PedidosSQLite:
    def __init__(self, inventario):
        self.inventario = inventario
        self.conexion = inventario.conexion

    @staticmethod
    def _validar_cabecera(id_pedido, cliente, destino, prioridad):
        if any(not isinstance(texto, str) or not texto.strip()
               for texto in (id_pedido, cliente, destino)):
            raise ValueError("Identificador, cliente y destino deben ser textos no vacíos.")
        if type(prioridad) is not int or prioridad not in (1, 2, 3):
            raise ValueError("La prioridad debe ser 1, 2 o 3.")

    def _cabecera(self, id_pedido):
        fila = self.conexion.execute(
            "SELECT * FROM pedidos WHERE id_pedido = ?", (id_pedido,)
        ).fetchone()
        if fila is None:
            raise ValueError(f"No existe el pedido {id_pedido}.")
        return fila

    def _exigir_estado(self, id_pedido, *estados):
        fila = self._cabecera(id_pedido)
        if fila["estado"] not in estados:
            raise ValueError(f"El pedido {id_pedido} está {fila['estado']}; "
                             f"la operación requiere: {', '.join(estados)}.")

    def _items(self, id_pedido):
        return self.conexion.execute(
            """SELECT i.id_deposito, i.id_producto, i.cantidad,
                p.nombre AS producto, p.volumen_unitario
            FROM pedido_items i JOIN productos p USING (id_producto)
            WHERE i.id_pedido = ? ORDER BY i.id_deposito, i.id_producto""",
            (id_pedido,),
        ).fetchall()

    def crear_borrador(self, id_pedido, cliente, destino, prioridad=1):
        self._validar_cabecera(id_pedido, cliente, destino, prioridad)
        with self.inventario._transaccion():
            self.conexion.execute(
                "INSERT INTO pedidos (id_pedido, cliente, destino, prioridad) VALUES (?, ?, ?, ?)",
                (id_pedido, cliente, destino, prioridad),
            )

    def editar_borrador(self, id_pedido, cliente, destino, prioridad=1):
        self._validar_cabecera(id_pedido, cliente, destino, prioridad)
        with self.inventario._transaccion():
            self._exigir_estado(id_pedido, "Borrador")
            self.conexion.execute(
                "UPDATE pedidos SET cliente = ?, destino = ?, prioridad = ? WHERE id_pedido = ?",
                (cliente, destino, prioridad, id_pedido),
            )

    def establecer_producto(self, id_pedido, id_deposito, id_producto, cantidad):
        """Establece la cantidad de esa pareja depósito/producto; no la incrementa."""
        self.inventario._validar_cantidad(cantidad)
        if cantidad <= 0:
            raise ValueError("La cantidad solicitada debe ser positiva.")
        with self.inventario._transaccion():
            self._exigir_estado(id_pedido, "Borrador")
            self.inventario.obtener_deposito(id_deposito)
            self.inventario.obtener_producto(id_producto)
            self.conexion.execute(
                """INSERT INTO pedido_items (id_pedido, id_deposito, id_producto, cantidad)
                VALUES (?, ?, ?, ?) ON CONFLICT (id_pedido, id_deposito, id_producto)
                DO UPDATE SET cantidad = excluded.cantidad""",
                (id_pedido, id_deposito, id_producto, cantidad),
            )

    def quitar_producto(self, id_pedido, id_deposito, id_producto):
        with self.inventario._transaccion():
            self._exigir_estado(id_pedido, "Borrador")
            cursor = self.conexion.execute(
                "DELETE FROM pedido_items WHERE id_pedido = ? AND id_deposito = ? AND id_producto = ?",
                (id_pedido, id_deposito, id_producto),
            )
            if cursor.rowcount == 0:
                raise ValueError("El pedido no tiene ese producto de ese depósito.")

    def obtener_pedido(self, id_pedido):
        """Devuelve una copia para consulta; modificarla no escribe en la base."""
        fila = self._cabecera(id_pedido)
        pedido = Pedido(fila["id_pedido"], fila["cliente"], fila["destino"], fila["prioridad"])
        pedido.estado = fila["estado"]
        pedido.creado_en = fila["creado_en"]
        pedido.vehiculo_asignado = fila["patente_vehiculo"]
        pedido.productos = [dict(item) for item in self._items(id_pedido)]
        pedido.volumen_total = sum(i["cantidad"] * i["volumen_unitario"] for i in pedido.productos)
        return pedido

    def listar_pedidos(self):
        filas = self.conexion.execute("SELECT id_pedido FROM pedidos ORDER BY id_pedido").fetchall()
        return [self.obtener_pedido(fila[0]) for fila in filas]

    def confirmar(self, id_pedido):
        with self.inventario._transaccion():
            self._exigir_estado(id_pedido, "Borrador")
            items = self._items(id_pedido)
            if not items:
                raise ValueError("No se puede confirmar un pedido sin productos.")
            faltantes = []
            for item in items:
                disponible = self.inventario.stock_disponible(item["id_deposito"], item["id_producto"])
                if disponible < item["cantidad"]:
                    faltantes.append({
                        "id_deposito": item["id_deposito"], "id_producto": item["id_producto"],
                        "solicitadas": item["cantidad"], "disponibles": disponible,
                        "faltan": item["cantidad"] - disponible,
                    })
            if faltantes:
                raise StockInsuficiente(faltantes)
            self._cambiar_estado(id_pedido, "Confirmado")

    def _cambiar_estado(self, id_pedido, estado):
        self.conexion.execute("UPDATE pedidos SET estado = ? WHERE id_pedido = ?", (estado, id_pedido))

    def _validar_vehiculo(self, pedido, patente):
        flota = FlotaSQLite(self.inventario)
        vehiculo = flota.obtener_vehiculo(patente)
        if vehiculo.estado != "Disponible" or vehiculo.pedido_asignado not in (None, pedido.id_pedido):
            raise ValueError("El vehículo debe estar Disponible y sin otro pedido activo.")
        if vehiculo.conductor_asignado is None:
            raise ValueError("El vehículo debe tener conductor asignado.")
        conductor = flota.obtener_conductor(vehiculo.conductor_asignado)
        if conductor.estado != "Asignado":
            raise ValueError("El conductor del vehículo no está habilitado para el despacho.")
        volumen = pedido.volumen_total
        if (not math.isfinite(volumen)
                or (volumen > vehiculo.capacidad_maxima
                    and not math.isclose(volumen, vehiculo.capacidad_maxima, rel_tol=1e-12, abs_tol=0))):
            raise ValueError("El vehículo no tiene capacidad para todo el pedido.")

    def asignar_vehiculo(self, id_pedido, patente):
        with self.inventario._transaccion():
            self._exigir_estado(id_pedido, "Confirmado")
            pedido = self.obtener_pedido(id_pedido)
            if pedido.vehiculo_asignado is not None:
                raise ValueError("Liberar el vehículo anterior antes de asignar otro.")
            self._validar_vehiculo(pedido, patente)
            self.conexion.execute("UPDATE pedidos SET patente_vehiculo = ? WHERE id_pedido = ?",
                                  (patente, id_pedido))

    def liberar_vehiculo(self, id_pedido):
        with self.inventario._transaccion():
            self._exigir_estado(id_pedido, "Confirmado")
            if self._cabecera(id_pedido)["patente_vehiculo"] is None:
                raise ValueError("El pedido no tiene vehículo asignado.")
            self.conexion.execute("UPDATE pedidos SET patente_vehiculo = NULL WHERE id_pedido = ?",
                                  (id_pedido,))

    def cancelar(self, id_pedido):
        with self.inventario._transaccion():
            self._exigir_estado(id_pedido, "Borrador", "Confirmado")
            self._cambiar_estado(id_pedido, "Cancelado")

    def despachar(self, id_pedido):
        with self.inventario._transaccion():
            self._exigir_estado(id_pedido, "Confirmado")
            pedido = self.obtener_pedido(id_pedido)
            if pedido.vehiculo_asignado is None:
                raise ValueError("Asignar un vehículo antes de despachar el pedido.")
            self._validar_vehiculo(pedido, pedido.vehiculo_asignado)
            # Libera solo las reservas propias dentro de la misma transacción.
            # Si cualquier descuento falla, se revierten estado y movimientos.
            self._cambiar_estado(id_pedido, "Despachado")
            for item in self._items(id_pedido):
                self.inventario._modificar_stock(
                    item["id_deposito"], item["id_producto"], -item["cantidad"]
                )
            self.conexion.execute("UPDATE vehiculos SET estado = 'En Ruta' WHERE patente = ?",
                                  (pedido.vehiculo_asignado,))

    def entregar(self, id_pedido):
        with self.inventario._transaccion():
            self._exigir_estado(id_pedido, "Despachado")
            patente = self._cabecera(id_pedido)["patente_vehiculo"]
            self._cambiar_estado(id_pedido, "Entregado")
            # Los pedidos despachados por versiones anteriores pueden no tener vehículo.
            if patente is not None:
                self.conexion.execute("UPDATE vehiculos SET estado = 'Disponible' WHERE patente = ?",
                                      (patente,))
