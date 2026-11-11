class Vehiculo:
    def __init__(self, patente, capacidad, estado="Disponible"):
        self.patente = patente
        self.capacidad_maxima = capacidad  # Mantenemos intacta la capacidad original
        self.volumen_ocupado = 0.0         # Nueva variable para el control dinámico
        self.estado = estado
        self.pedidos = []
        self.conductor_asignado = None     # Variable real para vincular al conductor

    def asignar_pedido(self, pedido):
        espacio_disponible = self.capacidad_maxima - self.volumen_ocupado
        if self.estado == "Disponible" and espacio_disponible >= pedido.volumen_total:
            self.pedidos.append(pedido)
            self.volumen_ocupado += pedido.volumen_total  # Sumamos al volumen ocupado
            pedido.actualizar_estado("Asignado")
            print(f"Pedido {pedido.id_pedido} asignado al vehículo {self.patente}. Capacidad restante: {self.capacidad_maxima - self.volumen_ocupado}")
        else:
            print(f"No se puede asignar el pedido {pedido.id_pedido} al vehículo {self.patente}. Estado: {self.estado}, Espacio disponible: {espacio_disponible}")

    def actualizar_estado(self, nuevo_estado):
        estados_validos = ["Disponible", "En Ruta", "Mantenimiento"]
        if nuevo_estado in estados_validos:
            self.estado = nuevo_estado
            #print(f"El vehículo {self.patente} ahora está: {self.estado}")
        else:
            print(f"Error: '{nuevo_estado}' no es un estado válido para el vehículo {self.patente}.")

    def liberar_pedido(self, pedido):
        if pedido in self.pedidos:
            self.pedidos.remove(pedido)
            self.volumen_ocupado -= pedido.volumen_total  # Liberamos el espacio ocupado
            pedido.actualizar_estado("Entregado")
            print(f"Pedido {pedido.id_pedido} liberado del vehículo {self.patente}. Capacidad disponible: {self.capacidad_maxima - self.volumen_ocupado}")
        else:
            print(f"Error: El pedido {pedido.id_pedido} no está asignado al vehículo {self.patente}.")

    def tiene_conductor(self):
        """Verifica si el vehículo tiene un conductor asignado revisando su estado interno."""
        return self.conductor_asignado is not None

    def asignar_conductor(self, conductor):
        """Asigna un conductor al vehículo guardando la referencia."""
        if not self.tiene_conductor():
            self.conductor_asignado = conductor
            print(f"Conductor asignado al vehículo {self.patente}.")
        else:
            print(f"Error: El vehículo {self.patente} ya tiene conductor.")

    def liberar_conductor(self):
        """Libera al conductor asignado blanqueando la variable."""
        if self.tiene_conductor():
            print(f"Conductor liberado del vehículo {self.patente}.")
            self.conductor_asignado = None
        else:
            print(f"El vehículo {self.patente} no tenía conductor asignado.")

    def tiene_pedido(self, pedido):
        return pedido in self.pedidos