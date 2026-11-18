"""Representa conductores y sus vínculos locales con vehículos."""

class Conductor:
    """Conserva identidad, estado y patente asignada de un conductor.

    Los métodos cambian el objeto local. FlotaSQLite persiste la relación
    mediante el vehículo y deriva el estado Asignado al consultarlo.

    Attributes:
        dni (str): Identificador del conductor.
        nombre (str): Nombre visible.
        estado (str): Disponible, Asignado o Inactivo.
        vehiculo_asignado (str | None): Patente local o consultada.
    """
    
    def __init__(self, dni, nombre):
        """Crea un conductor Disponible y sin vehículo asignado.

        Args:
            dni (str): Identificador del conductor.
            nombre (str): Nombre visible.
        """
        self.dni = dni
        self.nombre = nombre
        
        # Estado dinámico del objeto
        self.estado = "Disponible"  
        self.vehiculo_asignado = None

    def actualizar_estado(self, nuevo_estado):
        """Actualiza el estado local si su nombre está admitido.

        Args:
            nuevo_estado (str): Disponible, Asignado o Inactivo.

        Returns:
            bool: True si se actualizó; False si se rechazó el nombre.
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
        """Vincula una patente al modelo si está Disponible o Asignado.

        En memoria reemplaza la patente anterior. La asignación persistente
        requiere las verificaciones y operaciones de FlotaSQLite.

        Args:
            patente (str): Patente que se guarda en el objeto local.

        Returns:
            bool: True si se vinculó; False si el conductor está Inactivo.
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
        """Libera la patente local y deja al conductor Disponible.

        Returns:
            bool: True si había vehículo; False si no había asignación.
        """
        if self.vehiculo_asignado:
            print(f"Conductor {self.nombre} liberado del vehículo {self.vehiculo_asignado}.")
            self.vehiculo_asignado = None
            self.actualizar_estado("Disponible")
            return True
        return False

    def obtener_info(self):
        """Construye un resumen de identidad, estado y asignación local.

        Returns:
            dict[str, object]: DNI, Nombre, Estado y Vehículo Asignado.
        """
        return {
            "DNI": self.dni,
            "Nombre": self.nombre,
            "Estado": self.estado,
            "Vehículo Asignado": self.vehiculo_asignado
        }
