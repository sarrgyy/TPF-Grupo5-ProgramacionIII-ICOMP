class Deposito:
    def __init__(self, id_deposito, nombre, ubicacion, capacidad):
        self.id_deposito = id_deposito
        self.nombre = nombre
        self.ubicacion = ubicacion
        self.capacidad = capacidad
    def espacio_ocupado(self, volumen_ocupado):
        """
        Calcula el espacio ocupado en el depósito.
        :param volumen_ocupado: Volumen total de productos almacenados.
        :return: Espacio disponible en el depósito.
        """
        espacio_disponible = self.capacidad - volumen_ocupado
        if espacio_disponible < 0:
            print(f"Advertencia: El depósito {self.nombre} está sobrecargado. Capacidad: {self.capacidad}, Volumen ocupado: {volumen_ocupado}")
            return 0
        return espacio_disponible
    def actualizar_capacidad(self, nuevo_volumen):
        """
        Actualiza la capacidad del depósito.
        :param nuevo_volumen: Nuevo volumen total de productos almacenados.
        """
        if nuevo_volumen <= self.capacidad:
            print(f"Capacidad del depósito {self.nombre} actualizada a {nuevo_volumen}.")
        else:
            print(f"Error: No se puede actualizar la capacidad del depósito {self.nombre} a {nuevo_volumen}. Capacidad máxima: {self.capacidad}.")
    def verificar_espacio(self, volumen_requerido):
        """
        Verifica si hay suficiente espacio en el depósito para un nuevo volumen.
        :param volumen_requerido: Volumen que se desea almacenar.
        :return: Booleano indicando si hay suficiente espacio.
        """
        if volumen_requerido <= self.capacidad:
            print(f"Hay suficiente espacio en el depósito {self.nombre} para almacenar {volumen_requerido}.")
            return True
        else:
            print(f"No hay suficiente espacio en el depósito {self.nombre} para almacenar {volumen_requerido}. Capacidad máxima: {self.capacidad}.")
            return False
    def obtener_informacion(self):
        """
        Retorna la información del depósito.
        :return: Diccionario con la información del depósito.
        """
        return {
            "id_deposito": self.id_deposito,
            "nombre": self.nombre,
            "ubicacion": self.ubicacion,
            "capacidad": self.capacidad
        }
