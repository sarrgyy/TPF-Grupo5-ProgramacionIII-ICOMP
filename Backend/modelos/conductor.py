
class Conductor:
    """
    Representa un conductor de distribución.
    """
    
    def __init__(self, dni, nombre):
        """
        Inicializa un nuevo conductor.
        
        :param dni: Documento Nacional de Identidad (Identificador único).
        :param nombre: Nombre completo del conductor.
        """
        self.dni = dni
        self.nombre = nombre
        
        # Estado dinámico del objeto
        self.estado = "Disponible"  # Estados válidos: Disponible, Asignado, Inactivo
        self.vehiculo_asignado = None

    def actualizar_estado(self, nuevo_estado):
        """
        Modifica el estado operativo del conductor garantizando que sea un estado válido.
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
        """
        Vincula al conductor con un vehículo si se encuentra apto para trabajar.
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
        """
        Desvincula al conductor de su vehículo actual, retornándolo a disponibilidad.
        """
        if self.vehiculo_asignado:
            print(f"Conductor {self.nombre} liberado del vehículo {self.vehiculo_asignado}.")
            self.vehiculo_asignado = None
            self.actualizar_estado("Disponible")
            return True
        return False

    def obtener_info(self):
        """
        Retorna una vista resumida del estado actual del conductor.
        """
        return {
            "DNI": self.dni,
            "Nombre": self.nombre,
            "Estado": self.estado,
            "Vehículo Asignado": self.vehiculo_asignado
        }
