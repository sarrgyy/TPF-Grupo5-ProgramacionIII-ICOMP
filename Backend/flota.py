"""Persistencia de flota y consulta del pedido activo de cada vehículo."""

from .modelos.conductor import Conductor
from .modelos.vehiculo import Vehiculo


class FlotaSQLite:
    def __init__(self, inventario):
        self.inventario = inventario
        self.conexion = inventario.conexion

    @staticmethod
    def _validar_textos(*valores):
        if any(not isinstance(valor, str) or not valor.strip() for valor in valores):
            raise ValueError("Los identificadores y nombres deben ser textos no vacíos.")

    def registrar_vehiculo(self, vehiculo):
        self._validar_textos(vehiculo.patente)
        self.inventario._validar_medida(vehiculo.capacidad_maxima)
        if (vehiculo.estado not in ("Disponible", "Mantenimiento")
                or vehiculo.conductor_asignado is not None
                or vehiculo.pedido_asignado is not None
                or vehiculo.pedidos or vehiculo.volumen_ocupado != 0):
            raise ValueError("Registrar el vehículo sin carga ni conductor, Disponible o en Mantenimiento.")
        with self.inventario._transaccion():
            self.conexion.execute(
                "INSERT INTO vehiculos (patente, capacidad_maxima, estado) VALUES (?, ?, ?)",
                (vehiculo.patente, vehiculo.capacidad_maxima, vehiculo.estado),
            )

    def registrar_conductor(self, conductor):
        self._validar_textos(conductor.dni, conductor.nombre)
        if (conductor.estado not in ("Disponible", "Inactivo")
                or conductor.vehiculo_asignado is not None):
            raise ValueError("Registrar el conductor sin vehículo, Disponible o Inactivo.")
        with self.inventario._transaccion():
            self.conexion.execute(
                "INSERT INTO conductores (dni, nombre, estado) VALUES (?, ?, ?)",
                (conductor.dni, conductor.nombre, conductor.estado),
            )

    def obtener_vehiculo(self, patente):
        fila = self.conexion.execute(
            """SELECT v.*, p.id_pedido,
                CASE WHEN p.estado = 'Despachado' THEN COALESCE((
                    SELECT SUM(i.cantidad * pr.volumen_unitario)
                    FROM pedido_items i JOIN productos pr USING (id_producto)
                    WHERE i.id_pedido = p.id_pedido
                ), 0) ELSE 0 END AS carga
            FROM vehiculos v LEFT JOIN pedidos p
                ON p.patente_vehiculo = v.patente AND p.estado IN ('Confirmado', 'Despachado')
            WHERE v.patente = ?""", (patente,)
        ).fetchone()
        if fila is None:
            raise ValueError(f"No existe el vehículo {patente}.")
        vehiculo = Vehiculo(fila["patente"], fila["capacidad_maxima"], fila["estado"])
        vehiculo.conductor_asignado = fila["dni_conductor"]
        vehiculo.pedido_asignado = fila["id_pedido"]
        vehiculo.volumen_ocupado = fila["carga"]
        return vehiculo

    def obtener_conductor(self, dni):
        fila = self.conexion.execute(
            """SELECT c.*, v.patente FROM conductores c
            LEFT JOIN vehiculos v ON v.dni_conductor = c.dni WHERE c.dni = ?""", (dni,)
        ).fetchone()
        if fila is None:
            raise ValueError(f"No existe el conductor {dni}.")
        conductor = Conductor(fila["dni"], fila["nombre"])
        conductor.vehiculo_asignado = fila["patente"]
        conductor.estado = "Asignado" if fila["patente"] is not None else fila["estado"]
        return conductor

    def listar_vehiculos(self):
        filas = self.conexion.execute("SELECT patente FROM vehiculos ORDER BY patente").fetchall()
        return [self.obtener_vehiculo(fila[0]) for fila in filas]

    def listar_conductores(self):
        filas = self.conexion.execute("SELECT dni FROM conductores ORDER BY dni").fetchall()
        return [self.obtener_conductor(fila[0]) for fila in filas]

    def asignar_conductor(self, patente, dni):
        with self.inventario._transaccion():
            vehiculo = self.obtener_vehiculo(patente)
            conductor = self.obtener_conductor(dni)
            if vehiculo.pedido_asignado is not None:
                raise ValueError("El vehículo tiene un pedido activo; liberar el pedido primero.")
            if vehiculo.estado != "Disponible" or vehiculo.conductor_asignado is not None:
                raise ValueError("El vehículo debe estar Disponible y sin conductor.")
            if conductor.estado != "Disponible" or conductor.vehiculo_asignado is not None:
                raise ValueError("El conductor debe estar Disponible y sin vehículo.")
            self.conexion.execute("UPDATE vehiculos SET dni_conductor = ? WHERE patente = ?",
                                  (dni, patente))

    def liberar_conductor(self, patente):
        with self.inventario._transaccion():
            vehiculo = self.obtener_vehiculo(patente)
            if vehiculo.pedido_asignado is not None:
                raise ValueError("El vehículo tiene un pedido activo; liberar el pedido primero.")
            if vehiculo.conductor_asignado is None:
                raise ValueError("El vehículo no tiene conductor asignado.")
            if vehiculo.estado != "Disponible":
                raise ValueError("El vehículo debe volver a Disponible antes de liberar el conductor.")
            self.conexion.execute("UPDATE vehiculos SET dni_conductor = NULL WHERE patente = ?",
                                  (patente,))

    def actualizar_estado_vehiculo(self, patente, estado):
        if estado not in ("Disponible", "En Ruta", "Mantenimiento"):
            raise ValueError("Estado de vehículo inválido.")
        with self.inventario._transaccion():
            vehiculo = self.obtener_vehiculo(patente)
            if vehiculo.pedido_asignado is not None and estado != vehiculo.estado:
                raise ValueError("El estado del vehículo se actualiza al despachar o entregar su pedido.")
            if estado == "Mantenimiento" and vehiculo.conductor_asignado is not None:
                raise ValueError("Liberar al conductor antes de pasar a Mantenimiento.")
            if estado == "En Ruta" and vehiculo.conductor_asignado is None:
                raise ValueError("Un vehículo En Ruta debe tener conductor.")
            self.conexion.execute("UPDATE vehiculos SET estado = ? WHERE patente = ?",
                                  (estado, patente))

    def actualizar_estado_conductor(self, dni, estado):
        if estado not in ("Disponible", "Inactivo"):
            raise ValueError("Estado inválido; Asignado se obtiene al asignar un vehículo.")
        with self.inventario._transaccion():
            conductor = self.obtener_conductor(dni)
            if conductor.vehiculo_asignado is not None:
                raise ValueError("Liberar la asignación antes de cambiar el estado del conductor.")
            self.conexion.execute("UPDATE conductores SET estado = ? WHERE dni = ?", (estado, dni))
