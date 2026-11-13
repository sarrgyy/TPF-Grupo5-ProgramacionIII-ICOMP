class Deposito:
    def __init__(self, id_deposito, nombre, ubicacion, capacidad):
        self.id_deposito = id_deposito
        self.nombre = nombre
        self.ubicacion = ubicacion
        self.capacidad_maxima = capacidad
        self.volumen_ocupado = 0.0  

    def espacio_disponible(self):
        """Calcula de forma dinámica el espacio libre."""
        return self.capacidad_maxima - self.volumen_ocupado

    def actualizar_capacidad(self, nueva_capacidad):
        """
        Actualiza la capacidad total (ej. ampliación del galpón).
        Solo permite el cambio si la nueva capacidad entra en lo que ya está ocupado.
        """
        if nueva_capacidad >= self.volumen_ocupado:
            self.capacidad_maxima = nueva_capacidad
            print(f"Capacidad del depósito {self.nombre} actualizada a {nueva_capacidad}.")
        else:
            print(f"Error: La nueva capacidad ({nueva_capacidad}) choca con el volumen ya ocupado ({self.volumen_ocupado}).")

    def verificar_espacio(self, volumen_requerido):
        """
        Verifica si hay suficiente espacio evaluando el volumen libre real.
        """
        if volumen_requerido <= self.espacio_disponible():
            print(f"Hay suficiente espacio en el depósito {self.nombre} para almacenar {volumen_requerido}.")
            return True
        else:
            print(f"No hay suficiente espacio en el depósito {self.nombre}. Disponible: {self.espacio_disponible()}.")
            return False
            
