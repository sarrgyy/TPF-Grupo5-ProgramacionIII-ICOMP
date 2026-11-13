# entrega.py

class Entrega:
    """
    Representa el destino y las condiciones de entrega de un pedido.
    Es responsable de gestionar su estado (completada, fallida, etc.) y validar su ventana horaria.
    """
    
    def __init__(self, id_entrega, cliente, direccion, hora_inicio, hora_fin):
        """
        Inicializa una nueva entrega con su identidad y estado inicial.
        
        :param id_entrega: Identificador único de la entrega.
        :param cliente: Nombre del cliente o empresa receptora.
        :param direccion: Dirección física del destino de entrega.
        :param hora_inicio: Hora de inicio de la ventana de entrega (ej. "09:00").
        :param hora_fin: Hora de finalización de la ventana de entrega (ej. "13:00").
        """
        self.id_entrega = id_entrega
        self.cliente = cliente
        self.direccion = direccion
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin
        
        # Estado dinámico de la entrega
        self.estado = "Programada"  # Estados: Programada, En Camino, Completada, Fallida
        self.observaciones = ""

    def actualizar_estado(self, nuevo_estado, observaciones=""):
        """
        Modifica el estado actual de la entrega y registra observaciones si es necesario.
        
        :param nuevo_estado: El nuevo estado de la entrega.
        :param observaciones: Notas adicionales (ej. motivo de entrega fallida).
        """
        estados_validos = ["Programada", "En Camino", "Completada", "Fallida"]
        if nuevo_estado in estados_validos:
            self.estado = nuevo_estado
            self.observaciones = observaciones
            print(f"La entrega {self.id_entrega} para {self.cliente} ahora está: {self.estado}.")
            if observaciones:
                print(f"Observaciones: {self.observaciones}")
            return True
        else:
            print(f"Error: '{nuevo_estado}' no es un estado válido para la entrega.")
            return False

    def obtener_info(self):
        """
        Retorna un diccionario con la información y el estado actual de la entrega.
        """
        return {
            "ID Entrega": self.id_entrega,
            "Cliente": self.cliente,
            "Dirección": self.direccion,
            "Ventana Horaria": f"{self.hora_inicio} - {self.hora_fin}",
            "Estado": self.estado,
            "Observaciones": self.observaciones
        }
