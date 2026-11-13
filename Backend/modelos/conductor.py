"""Define el conductor para simulación y copias de consulta de flota."""


class Conductor:
    """Representa un conductor y su asignación local.

    Para guardar cambios usar FlotaSQLite; estos métodos operan en memoria.

    Attributes:
        dni (str): Identificador del conductor.
        nombre (str): Nombre completo.
        estado (str): Disponible, Asignado o Inactivo.
        vehiculo_asignado (str | None): Patente asociada, si existe.
    """

    def __init__(self, dni, nombre):
        """Construye un conductor Disponible y sin vehículo.

        Args:
            dni (str): Identificador del conductor, conservado como texto.
            nombre (str): Nombre descriptivo.
        """
        self.dni = dni
        self.nombre = nombre
        
        self.estado = "Disponible"
        self.vehiculo_asignado = None

    def actualizar_estado(self, nuevo_estado):
        """Cambia el estado local si está admitido, o imprime un error.

        Args:
            nuevo_estado (str): Estado solicitado para el objeto en memoria.

        Returns:
            bool: True si se aceptó; False si el estado no es válido.
        """
        estados_validos = ["Disponible", "Asignado", "Inactivo"]
        if nuevo_estado in estados_validos:
            self.estado = nuevo_estado
            print(f"El conductor {self.nombre} ahora está: {self.estado}")
            return True
        else:
            print(f"Error: '{nuevo_estado}' no es un estado válido.")
            return False

    def asignar_vehiculo(self, patente):
        """Vincula una patente local si el conductor no está Inactivo.

        El método local puede reemplazar una patente. FlotaSQLite controla
        unicidad y liberación previa.

        Args:
            patente (str): Identificador del vehículo.

        Returns:
            bool: True si se asignó; False si no se permite asignar.
        """
        if self.estado in ["Disponible", "Asignado"]:
            self.vehiculo_asignado = patente
            self.actualizar_estado("Asignado")
            print(f"Conductor {self.nombre} asignado al vehículo {patente}.")
            return True
        else:
            print(f"Error: El conductor {self.nombre} se encuentra {self.estado} y no puede ser asignado.")
            return False

    def liberar_vehiculo(self):
        """Quita la patente local y deja al conductor Disponible.

        Returns:
            bool: True si había asignación; False si no tenía vehículo.
        """
        if self.vehiculo_asignado:
            print(f"Conductor {self.nombre} liberado del vehículo {self.vehiculo_asignado}.")
            self.vehiculo_asignado = None
            self.actualizar_estado("Disponible")
            return True
        return False

    def obtener_info(self):
        """Obtiene un resumen del conductor sin consultar SQLite.

        Returns:
            dict: DNI, nombre, estado y patente asignada.
        """
        return {
            "DNI": self.dni,
            "Nombre": self.nombre,
            "Estado": self.estado,
            "Vehículo Asignado": self.vehiculo_asignado
        }
