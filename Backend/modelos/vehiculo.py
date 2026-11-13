"""Define vehículos locales y copias de consulta de la flota persistente."""


class Vehiculo:
    """Representa capacidad y asignaciones locales de un vehículo.

    Usar FlotaSQLite y PedidosSQLite para guardar relaciones y transiciones.

    Attributes:
        patente (str): Identificador del vehículo.
        capacidad_maxima (float): Capacidad total de volumen.
        volumen_ocupado (float): Carga local o calculada del pedido Despachado.
        estado (str): Disponible, En Ruta o Mantenimiento.
        pedidos (list[Pedido]): Pedidos locales de la simulación.
        conductor_asignado (str | None): Nombre local o DNI recuperado de SQLite.
        pedido_asignado (str | None): Identificador persistente del pedido activo.
    """

    def __init__(self, patente, capacidad, estado="Disponible"):
        """Construye un vehículo sin carga ni asignaciones locales.

        Args:
            patente (str): Identificador del vehículo.
            capacidad (float): Capacidad en la unidad de volumen común del
                inventario.
            estado (str): Estado operativo solicitado. Por defecto:
                'Disponible'.
        """
        self.patente = patente
        self.capacidad_maxima = capacidad
        self.volumen_ocupado = 0.0
        self.estado = estado
        self.pedidos = []
        self.conductor_asignado = None
        self.pedido_asignado = None

    def asignar_pedido(self, pedido):
        """Carga el pedido local si está Disponible y tiene espacio suficiente.

        Args:
            pedido (Pedido): Pedido cuyo volumen o pertenencia se consulta.
        """
        espacio_disponible = self.capacidad_maxima - self.volumen_ocupado
        if self.estado == "Disponible" and espacio_disponible >= pedido.volumen_total:
            self.pedidos.append(pedido)
            self.volumen_ocupado += pedido.volumen_total  # Sumamos al volumen ocupado
            pedido.actualizar_estado("Asignado")
            print(f"Pedido {pedido.id_pedido} asignado al vehículo {self.patente}. Capacidad restante: {self.capacidad_maxima - self.volumen_ocupado}")
        else:
            print(f"No se puede asignar el pedido {pedido.id_pedido} al vehículo {self.patente}. Estado: {self.estado}, Espacio disponible: {espacio_disponible}")

    def actualizar_estado(self, nuevo_estado):
        """Cambia un estado local admitido o imprime un error.

        Args:
            nuevo_estado (str): Estado solicitado para el objeto en memoria.
        """
        estados_validos = ["Disponible", "En Ruta", "Mantenimiento"]
        if nuevo_estado in estados_validos:
            self.estado = nuevo_estado
        else:
            print(f"Error: '{nuevo_estado}' no es un estado válido para el vehículo {self.patente}.")

    def liberar_pedido(self, pedido):
        """Descarga el pedido local y lo marca Entregado si estaba a bordo.

        Args:
            pedido (Pedido): Pedido cuyo volumen o pertenencia se consulta.
        """
        if pedido in self.pedidos:
            self.pedidos.remove(pedido)
            self.volumen_ocupado -= pedido.volumen_total  # Liberamos el espacio ocupado
            pedido.actualizar_estado("Entregado")
            print(f"Pedido {pedido.id_pedido} liberado del vehículo {self.patente}. Capacidad disponible: {self.capacidad_maxima - self.volumen_ocupado}")
        else:
            print(f"Error: El pedido {pedido.id_pedido} no está asignado al vehículo {self.patente}.")

    def tiene_conductor(self):
        """Indica si esta copia conserva una referencia de conductor.

        Returns:
            bool: True si conductor_asignado no es None.
        """
        return self.conductor_asignado is not None

    def asignar_conductor(self, conductor):
        """Conserva una referencia local de conductor si no había otra.

        Args:
            conductor (str): Nombre o identificador usado por la simulación.
        """
        if not self.tiene_conductor():
            self.conductor_asignado = conductor
            print(f"Conductor asignado al vehículo {self.patente}.")
        else:
            print(f"Error: El vehículo {self.patente} ya tiene conductor.")

    def liberar_conductor(self):
        """Quita la referencia local de conductor sin modificar SQLite."""
        if self.tiene_conductor():
            print(f"Conductor liberado del vehículo {self.patente}.")
            self.conductor_asignado = None
        else:
            print(f"El vehículo {self.patente} no tenía conductor asignado.")

    def tiene_pedido(self, pedido):
        """Comprueba si el pedido pertenece a la lista local de carga.

        Args:
            pedido (Pedido): Pedido cuyo volumen o pertenencia se consulta.

        Returns:
            bool: True si la referencia está en pedidos.
        """
        return pedido in self.pedidos
