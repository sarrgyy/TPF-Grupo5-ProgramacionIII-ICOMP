class Vehiculo:
    def __init__(self, patente, capacidad, estado, pedidos):
        self.patente = patente
        self.capacidad = capacidad 
        self.estado = estado
        self.pedidos = []

    def asignar_pedido(self, pedido):
        if self.estado == "Disponible" and self.capacidad >= pedido.volumen_total:
            self.pedidos.append(pedido)
            self.capacidad -= pedido.volumen_total
            pedido.actualizar_estado("Asignado")
            print(f"Pedido {pedido.id_pedido} asignado al vehículo {self.patente}. Capacidad restante: {self.capacidad}")
        else:
            print(f"No se puede asignar el pedido {pedido.id_pedido} al vehículo {self.patente}. Estado: {self.estado}, Capacidad: {self.capacidad}, Volumen del pedido: {pedido.volumen_total}")

    def actualizar_estado(self, nuevo_estado):
        estados_validos = ["Disponible", "En Ruta", "Mantenimiento"]
        if nuevo_estado in estados_validos:
            self.estado = nuevo_estado
            print(f"El vehículo {self.patente} ahora está: {self.estado}")
        else:
            print(f"Error: '{nuevo_estado}' no es un estado válido para el vehículo {self.patente}.")

    def liberar_pedido(self, pedido):
        if pedido in self.pedidos:
            self.pedidos.remove(pedido)
            self.capacidad += pedido.volumen_total
            pedido.actualizar_estado("Entregado")
            print(f"Pedido {pedido.id_pedido} liberado del vehículo {self.patente}. Capacidad disponible: {self.capacidad}")
        else:
            print(f"Error: El pedido {pedido.id_pedido} no está asignado al vehículo {self.patente}.")

    def tiene_conductor(self):
        """
        Verifica si el vehículo tiene un conductor asignado.
        :return: Booleano indicando si hay un conductor.
        """
        # Aquí se podría implementar la lógica para verificar si hay un conductor asignado.
        # Por ahora, simplemente retornamos False como placeholder.
        return False

    def asignar_conductor(self, conductor):
        """
        Asigna un conductor al vehículo.
        :param conductor: Objeto que representa al conductor.
        """
        # Aquí se podría implementar la lógica para asignar un conductor al vehículo.
        # Por ahora, simplemente imprimimos un mensaje como placeholder.
        print(f"Conductor {conductor} asignado al vehículo {self.patente}.")

    def liberar_conductor(self):
        """
        Libera al conductor asignado del vehículo.
        """
        # Aquí se podría implementar la lógica para liberar al conductor del vehículo.
        # Por ahora, simplemente imprimimos un mensaje como placeholder.
        print(f"Conductor liberado del vehículo {self.patente}.")

    def tiene_pedido(self, pedido):
        """
        Verifica si el vehículo tiene un pedido específico asignado.
        :param pedido: Objeto que representa el pedido a verificar.
        :return: Booleano indicando si el pedido está asignado al vehículo.
        """
        return pedido in self.pedidos

