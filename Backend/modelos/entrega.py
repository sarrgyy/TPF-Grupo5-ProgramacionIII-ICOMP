"""Representa las condiciones de entrega asociadas a un pedido."""
# entrega.py

class Entrega:
    """Conserva destino, ventana horaria y estado local de una entrega.

    PedidosSQLite valida la ventana y deriva el estado al reconstruir
    un pedido. Este modelo conserva los valores que recibe.

    Attributes:
        id_entrega (str): Identificador de la entrega.
        cliente (str): Destinatario.
        direccion (str): Dirección de entrega.
        hora_inicio (str): Inicio de ventana, en HH:MM.
        hora_fin (str): Fin de ventana, en HH:MM.
        estado (str): Programada, En Camino, Completada o Fallida.
        observaciones (str): Notas locales sobre la entrega.
    """
    
    def __init__(self, id_entrega, cliente, direccion, hora_inicio, hora_fin):
        """Crea una entrega Programada con la ventana proporcionada.

        Args:
            id_entrega (str): Identificador de la entrega.
            cliente (str): Destinatario.
            direccion (str): Dirección de entrega.
            hora_inicio (str): Inicio de ventana en HH:MM.
            hora_fin (str): Fin de ventana en HH:MM.
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
        """Actualiza estado y notas si el nombre del estado es válido.

        Args:
            nuevo_estado (str): Programada, En Camino, Completada o Fallida.
            observaciones (str): Notas que reemplazan las anteriores.

        Returns:
            bool: True si se actualizó; False si se rechazó el estado.
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
        """Construye el detalle legible de destino, ventana y estado.

        Returns:
            dict[str, str]: Identidad, destinatario, dirección, ventana y notas.
        """
        return {
            "ID Entrega": self.id_entrega,
            "Cliente": self.cliente,
            "Dirección": self.direccion,
            "Ventana Horaria": f"{self.hora_inicio} - {self.hora_fin}",
            "Estado": self.estado,
            "Observaciones": self.observaciones
        }
