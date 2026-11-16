"""Guarda flota y asignaciones manuales de conductor y pedido.

FlotaSQLite obtiene la asignación desde vehiculos.dni_conductor y deriva
el estado Asignado del conductor. Los pedidos activos impiden alterar
su conductor o cambiar manualmente el estado del vehículo.
"""

from .modelos.conductor import Conductor
from .modelos.vehiculo import Vehiculo


class FlotaSQLite:
    """Gestiona vehículos y conductores con una única relación de asignación.

    El estado Asignado del conductor se deriva de la referencia en vehiculos.
    Las consultas devuelven copias; usar estos métodos para guardar cambios.
    Los errores de acceso a datos se propagan como sqlite3.Error.

    Attributes:
        inventario (InventarioSQLite): Sesión propietaria de las transacciones.
        conexion (sqlite3.Connection): Conexión compartida; no es propia.
    """

    def __init__(self, inventario):
        """Reutiliza conexión y transacciones de una sesión abierta.

        Args:
            inventario (InventarioSQLite): Sesión abierta que se reutiliza.
        """
        self.inventario = inventario
        self.conexion = inventario.conexion

    @staticmethod
    def _validar_textos(*valores):
        """Exige nombres e identificadores de texto no vacíos.

        Args:
            valores (str): Textos que se validan en conjunto.

        Raises:
            ValueError: Algún valor no es str o está vacío.
        """
        if any(not isinstance(valor, str) or not valor.strip() for valor in valores):
            raise ValueError("Los identificadores y nombres deben ser textos no vacíos.")

    def registrar_vehiculo(self, vehiculo):
        """Guarda un vehículo nuevo sin carga, conductor ni pedido activo.

        Args:
            vehiculo (Vehiculo): Datos, capacidad y estado del vehículo.

        Raises:
            ValueError: Datos físicos, estado o asignaciones iniciales
                inválidos.
            sqlite3.IntegrityError: Patente duplicada o datos inválidos.
        """
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
        """Guarda un conductor Disponible o Inactivo, sin vehículo.

        Args:
            conductor (Conductor): Datos y estado operativo del conductor.

        Raises:
            ValueError: Datos, estado o asignación inicial inválidos.
            sqlite3.IntegrityError: DNI duplicado o datos inválidos.
        """
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
        """Recupera vehículo, conductor, pedido activo y carga en una copia.

        La carga se calcula desde el pedido Despachado. La lista pedidos del
        modelo pertenece solo a la simulación.

        Args:
            patente (str): Identificador del vehículo.

        Returns:
            Vehiculo: Copia; el conductor es su DNI y la carga es la despachada.

        Raises:
            ValueError: El vehículo no existe.
        """
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
        """Recupera al conductor y deriva vehículo y estado Asignado.

        Args:
            dni (str): Identificador del conductor, conservado como texto.

        Returns:
            Conductor: Copia con datos y asignación actuales.

        Raises:
            ValueError: El conductor no existe.
        """
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
        """Lista copias de vehículos ordenadas por patente.

        Returns:
            list[Vehiculo]: Flota registrada con asignaciones y ocupación.
        """
        filas = self.conexion.execute("SELECT patente FROM vehiculos ORDER BY patente").fetchall()
        return [self.obtener_vehiculo(fila[0]) for fila in filas]

    def listar_conductores(self):
        """Lista copias de conductores ordenadas por DNI.

        Returns:
            list[Conductor]: Conductores registrados con asignaciones actuales.
        """
        filas = self.conexion.execute("SELECT dni FROM conductores ORDER BY dni").fetchall()
        return [self.obtener_conductor(fila[0]) for fila in filas]

    def asignar_conductor(self, patente, dni):
        """Vincula recursos Disponibles sin reemplazar asignaciones.

        Args:
            patente (str): Identificador del vehículo.
            dni (str): Identificador del conductor, conservado como texto.

        Raises:
            ValueError: Recursos ausentes, ocupados, inactivos o no disponibles.
        """
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
        """Libera al conductor de un vehículo Disponible sin pedido activo.

        Args:
            patente (str): Identificador del vehículo.

        Raises:
            ValueError: Asignación ausente o vehículo no liberable.
        """
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
        """Cambia el estado si no contradice conductor o pedido activo.

        Mantenimiento exige liberar conductor. En Ruta exige conductor. Con
        pedido activo, despacho y entrega coordinan los cambios.

        Args:
            patente (str): Identificador del vehículo.
            estado (str): Estado operativo solicitado.

        Raises:
            ValueError: Estado inválido o incompatible con las asignaciones.
        """
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
        """Cambia entre Disponible e Inactivo si no hay vehículo.

        Asignado se deriva de la relación con vehículos y no se fija
        manualmente.

        Args:
            dni (str): Identificador del conductor, conservado como texto.
            estado (str): Estado operativo solicitado.

        Raises:
            ValueError: Estado inválido, conductor ausente o asignación activa.
        """
        if estado not in ("Disponible", "Inactivo"):
            raise ValueError("Estado inválido; Asignado se obtiene al asignar un vehículo.")
        with self.inventario._transaccion():
            conductor = self.obtener_conductor(dni)
            if conductor.vehiculo_asignado is not None:
                raise ValueError("Liberar la asignación antes de cambiar el estado del conductor.")
            self.conexion.execute("UPDATE conductores SET estado = ? WHERE dni = ?", (estado, dni))
