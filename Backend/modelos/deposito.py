"""Define el depósito y sus operaciones locales de capacidad."""


class Deposito:
    """Representa un depósito o una copia recuperada de SQLite.

    Sus métodos operan en memoria. InventarioSQLite reconstruye su ocupación
    desde las existencias; cambiar el modelo no escribe en SQLite.

    Attributes:
        id_deposito (str): Identificador del depósito.
        nombre (str): Nombre descriptivo.
        ubicacion (str): Dirección de almacenamiento.
        capacidad_maxima (float): Capacidad en la unidad común de volumen.
        volumen_ocupado (float): Ocupación física de esta copia del modelo.
    """

    def __init__(self, id_deposito, nombre, ubicacion, capacidad):
        """Construye un depósito con volumen ocupado inicial cero.

        Args:
            id_deposito (str): Identificador del depósito.
            nombre (str): Nombre descriptivo.
            ubicacion (str): Dirección de almacenamiento.
            capacidad (float): Capacidad en la unidad de volumen común del
                inventario.
        """
        self.id_deposito = id_deposito
        self.nombre = nombre
        self.ubicacion = ubicacion
        self.capacidad_maxima = capacidad
        self.volumen_ocupado = 0.0

    def espacio_disponible(self):
        """Calcula la capacidad libre según el estado local del depósito.

        Returns:
            float: Capacidad máxima menos volumen ocupado.
        """
        return self.capacidad_maxima - self.volumen_ocupado

    def actualizar_capacidad(self, nueva_capacidad):
        """Cambia la capacidad local si admite el volumen ya ocupado.

        Si no admite el volumen ocupado, imprime un error y conserva la
        capacidad anterior. No escribe en SQLite.

        Args:
            nueva_capacidad (float): Nueva capacidad de volumen local.
        """
        if nueva_capacidad >= self.volumen_ocupado:
            self.capacidad_maxima = nueva_capacidad
            print(f"Capacidad del depósito {self.nombre} actualizada a {nueva_capacidad}.")
        else:
            print(f"Error: La nueva capacidad ({nueva_capacidad}) choca con el volumen ya ocupado ({self.volumen_ocupado}).")

    def verificar_espacio(self, volumen_requerido):
        """Comprueba el volumen libre local e imprime el resultado.

        Args:
            volumen_requerido (float): Espacio necesario para la operación.

        Returns:
            bool: True si el volumen cabe; False si no hay espacio.
        """
        if volumen_requerido <= self.espacio_disponible():
            print(f"Hay suficiente espacio en el depósito {self.nombre} para almacenar {volumen_requerido}.")
            return True
        else:
            print(f"No hay suficiente espacio en el depósito {self.nombre}. Disponible: {self.espacio_disponible()}.")
            return False
