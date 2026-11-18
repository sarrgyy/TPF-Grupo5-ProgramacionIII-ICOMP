"""Modela la capacidad volumétrica de un depósito."""
from .validaciones import validar_medida


class Deposito:
    """Representa un depósito y su ocupación de volumen en memoria.

    InventarioSQLite reconstruye la ocupación desde las existencias.
    Cambiar una copia de consulta no modifica la base de datos.

    Attributes:
        id_deposito (str): Identificador del depósito.
        nombre (str): Nombre visible.
        ubicacion (str): Dirección o referencia de ubicación.
        capacidad_maxima (float): Capacidad total, en m³.
        volumen_ocupado (float): Volumen ocupado, en m³.
    """

    def __init__(self, id_deposito, nombre, ubicacion, capacidad):
        """Crea el depósito con ocupación local inicial igual a cero.

        Args:
            id_deposito (str): Identificador del depósito.
            nombre (str): Nombre visible.
            ubicacion (str): Dirección o referencia de ubicación.
            capacidad (float): Volumen máximo en m³; se valida al persistir.
        """
        self.id_deposito = id_deposito
        self.nombre = nombre
        self.ubicacion = ubicacion
        self.capacidad_maxima = capacidad
        self.volumen_ocupado = 0.0

    def espacio_disponible(self):
        """Calcula la diferencia entre capacidad y volumen ocupado.

        Returns:
            float: Espacio disponible en m³.
        """
        return self.capacidad_maxima - self.volumen_ocupado

    def actualizar_capacidad(self, nueva_capacidad):
        """Actualiza la capacidad local si contiene la carga actual.

        Si la capacidad resulta menor que la ocupación, conserva el valor
        anterior e informa el rechazo por consola.

        Args:
            nueva_capacidad (float): Capacidad positiva y finita, en m³.

        Raises:
            ValueError: La capacidad es booleana, no numérica o no positiva finita.
        """
        validar_medida(nueva_capacidad)
        if nueva_capacidad >= self.volumen_ocupado:
            self.capacidad_maxima = nueva_capacidad
            print(f"Capacidad del depósito {self.nombre} actualizada a {nueva_capacidad}.")
        else:
            print(f"Error: La nueva capacidad ({nueva_capacidad}) choca con el volumen ya ocupado ({self.volumen_ocupado}).")

    def verificar_espacio(self, volumen_requerido):
        """Comprueba si un volumen cabe en el espacio disponible.

        Args:
            volumen_requerido (float): Volumen no negativo y finito, en m³.

        Returns:
            bool: True si el volumen cabe; False si supera el espacio libre.

        Raises:
            ValueError: El volumen no es una medida no negativa y finita.
        """
        validar_medida(volumen_requerido, permitir_cero=True)
        if volumen_requerido <= self.espacio_disponible():
            print(f"Hay suficiente espacio en el depósito {self.nombre} para almacenar {volumen_requerido}.")
            return True
        else:
            print(f"No hay suficiente espacio en el depósito {self.nombre}. Disponible: {self.espacio_disponible()}.")
            return False
