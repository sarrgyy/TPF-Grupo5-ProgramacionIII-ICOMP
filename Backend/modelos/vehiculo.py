"""Modela vehículos y asignaciones locales para simulaciones."""
class Vehiculo:
    """Representa un vehículo, su capacidad y sus asignaciones de consulta.

    Los métodos del modelo operan en memoria. FlotaSQLite y PedidosSQLite
    mantienen las relaciones y restricciones persistentes.

    Attributes:
        patente (str): Identificador del vehículo.
        capacidad_maxima (float): Volumen máximo de carga en m³.
        volumen_ocupado (float): Volumen local o carga despachada consultada.
        estado (str): Disponible, En Ruta o Mantenimiento.
        pedidos (list[Pedido]): Pedidos asignados en la simulación local.
        conductor_asignado (str | Conductor | None): Referencia local;
            el repositorio devuelve el DNI del conductor.
        pedido_asignado (str | None): ID activo informado por el repositorio.
    """

    def __init__(self, patente, capacidad, estado="Disponible"):
        """Inicializa un vehículo sin carga, conductor ni pedido activo.

        Args:
            patente (str): Identificador del vehículo.
            capacidad (float): Volumen máximo de carga, en m³.
            estado (str): Estado inicial; por defecto, Disponible.
        """
        self.patente = patente
        self.capacidad_maxima = capacidad
        self.volumen_ocupado = 0.0
        self.estado = estado
        self.pedidos = []
        self.conductor_asignado = None
        self.pedido_asignado = None        # id del pedido activo (lo informa la persistencia)

    def asignar_pedido(self, pedido):
        """Asigna un Confirmado en memoria si hay conductor y capacidad.

        Conserva el estado Confirmado. Si está ocupado, no está Disponible
        o el volumen no cabe, informa el rechazo sin modificar la asignación.

        Args:
            pedido (Pedido): Pedido confirmado cuyo volumen se desea cargar.

        Raises:
            ValueError: El pedido no es Confirmado o falta conductor.
        """
        if pedido.estado != "Confirmado":
            raise ValueError("Solo se puede asignar un pedido Confirmado.")
        if not self.tiene_conductor():
            raise ValueError("El vehículo debe tener conductor asignado.")
        espacio_disponible = self.capacidad_maxima - self.volumen_ocupado
        if self.estado == "Disponible" and not self.pedidos and espacio_disponible >= pedido.volumen_total:
            self.pedidos.append(pedido)
            self.volumen_ocupado += pedido.volumen_total
            # Asignar vehículo conserva el pedido Confirmado; despachar es otra operación.
            print(f"Pedido {pedido.id_pedido} asignado al vehículo {self.patente}. Capacidad restante: {self.capacidad_maxima - self.volumen_ocupado}")
        else:
            print(f"No se puede asignar el pedido {pedido.id_pedido} al vehículo {self.patente}. Estado: {self.estado}, Espacio disponible: {espacio_disponible}")

    def actualizar_estado(self, nuevo_estado):
        """Actualiza el nombre del estado local si está admitido.

        Args:
            nuevo_estado (str): Disponible, En Ruta o Mantenimiento.
        """
        estados_validos = ["Disponible", "En Ruta", "Mantenimiento"]
        if nuevo_estado in estados_validos:
            self.estado = nuevo_estado

        else:
            print(f"Error: '{nuevo_estado}' no es un estado válido para el vehículo {self.patente}.")

    def liberar_pedido(self, pedido):
        """Quita un pedido local y recupera el volumen que ocupaba.

        Un Despachado pasa a Entregado; un Confirmado conserva su estado.
        Al quedar sin pedidos, el vehículo pasa a Disponible. Un pedido
        no asignado solo produce un mensaje de rechazo.

        Args:
            pedido (Pedido): Objeto que se desea liberar de la simulación.
        """
        if pedido in self.pedidos:
            self.pedidos.remove(pedido)
            self.volumen_ocupado -= pedido.volumen_total
            if pedido.estado == "Despachado":
                pedido.actualizar_estado("Entregado")
            if not self.pedidos:
                self.estado = "Disponible"
                self.pedido_asignado = None
            print(f"Pedido {pedido.id_pedido} liberado del vehículo {self.patente}. Capacidad disponible: {self.capacidad_maxima - self.volumen_ocupado}")
        else:
            print(f"Error: El pedido {pedido.id_pedido} no está asignado al vehículo {self.patente}.")

    def tiene_conductor(self):
        """Consulta si existe una referencia local a un conductor.

        Returns:
            bool: True si conductor_asignado no es None.
        """
        return self.conductor_asignado is not None

    def asignar_conductor(self, conductor):
        """Guarda una referencia local a un conductor si no hay otro.

        Args:
            conductor (str | Conductor): DNI, nombre u objeto de la simulación.
        """
        if not self.tiene_conductor():
            self.conductor_asignado = conductor
            print(f"Conductor asignado al vehículo {self.patente}.")
        else:
            print(f"Error: El vehículo {self.patente} ya tiene conductor.")

    def liberar_conductor(self):
        """Elimina la referencia local al conductor, si estaba asignado."""
        if self.tiene_conductor():
            print(f"Conductor liberado del vehículo {self.patente}.")
            self.conductor_asignado = None
        else:
            print(f"El vehículo {self.patente} no tenía conductor asignado.")

    def tiene_pedido(self, pedido):
        """Comprueba si el objeto pedido pertenece a la asignación local.

        Args:
            pedido (Pedido): Objeto que se busca en la lista local.

        Returns:
            bool: True si el pedido está en la lista de la simulación.
        """
        return pedido in self.pedidos
