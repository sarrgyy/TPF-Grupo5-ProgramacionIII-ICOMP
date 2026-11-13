# main.py

# Importamos las clases que modelamos en la Fase 1
from modelos.deposito import Deposito
from modelos.productos import Producto
from modelos.vehiculo import Vehiculo
from modelos.conductor import Conductor
from modelos.pedido import Pedido
from modelos.entrega import Entrega 

def main():
    print("--- INICIANDO SISTEMA DE GESTIÓN LOGÍSTICA ---")
    
    # 1. Instanciación del Depósito y control de espacio
    print("\n[1] CONFIGURANDO DEPÓSITO Y STOCK INICIAL")
    deposito_central = Deposito(id_deposito="D-001", nombre="Base Bariloche", ubicacion="Ruta 40 Sur", capacidad=1000.0)
    
    prod_leche = Producto(id_producto="PRD-1", nombre="Cajas de Leche", volumen_unitario=0.5, peso_unitario=1.0, stock_inicial=500)
    prod_harina = Producto(id_producto="PRD-2", nombre="Bolsas de Harina", volumen_unitario=0.2, peso_unitario=0.5, stock_inicial=800)
    
    # 2. Configuración de la Flota
    print("\n[2] PREPARANDO FLOTA DE DISTRIBUCIÓN")
    furgon_1 = Vehiculo(patente="AB123CD", capacidad=20.0)
    camioneta_1 = Vehiculo(patente="EF456GH", capacidad=10.0)
    
    chofer_1 = Conductor(dni="30111222", nombre="Carlos Gómez")
    chofer_2 = Conductor(dni="31333444", nombre="Ana Silva")
    
    furgon_1.asignar_conductor(chofer_1.nombre)
    chofer_1.asignar_vehiculo(furgon_1.patente)
    camioneta_1.asignar_conductor(chofer_2.nombre)
    chofer_2.asignar_vehiculo(camioneta_1.patente)

    # 3. Creación y Recepción de Pedidos con Entregas
    print("\n[3] INGRESANDO PEDIDOS Y PROGRAMANDO ENTREGAS")
    # Instanciamos el pedido y su entrega correspondiente
    pedido_01 = Pedido(id_pedido="P-100", cliente="Supermercado Sur", destino="Av. Pioneros 4500", prioridad=2)
    entrega_p01 = Entrega(id_entrega="ENT-100", cliente="Supermercado Sur", direccion="Av. Pioneros 4500", hora_inicio="08:00", hora_fin="12:00")
    
    cant_leche_p1 = 20
    if prod_leche.actualizar_stock(-cant_leche_p1):
        pedido_01.agregar_producto(prod_leche.nombre, cant_leche_p1, prod_leche.volumen_unitario)
        
    cant_harina_p1 = 30
    if prod_harina.actualizar_stock(-cant_harina_p1):
        pedido_01.agregar_producto(prod_harina.nombre, cant_harina_p1, prod_harina.volumen_unitario)

    pedido_02 = Pedido(id_pedido="P-101", cliente="Despensa Centro", destino="Mitre 200", prioridad=1)
    entrega_p02 = Entrega(id_entrega="ENT-101", cliente="Despensa Centro", direccion="Mitre 200", hora_inicio="13:00", hora_fin="17:00")
    
    cant_leche_p2 = 50
    if prod_leche.actualizar_stock(-cant_leche_p2):
        pedido_02.agregar_producto(prod_leche.nombre, cant_leche_p2, prod_leche.volumen_unitario)

    # 4. Lógica Imperativa de Asignación 
    print("\n[4] EJECUTANDO ALGORITMO DE ASIGNACIÓN IMPERATIVA")
    pedidos_pendientes = [(pedido_01, entrega_p01), (pedido_02, entrega_p02)] # Agrupamos pedido y entrega
    flota_disponible = [furgon_1, camioneta_1]
    
    for pedido, entrega in pedidos_pendientes:
        asignado = False
        for vehiculo in flota_disponible:
            espacio_libre = vehiculo.capacidad_maxima - vehiculo.volumen_ocupado
            if vehiculo.estado == "Disponible" and espacio_libre >= pedido.volumen_total:
                vehiculo.asignar_pedido(pedido)
                entrega.actualizar_estado("En Camino") # Actualizamos la entrega mediante un mensaje
                asignado = True
                break 
        
        if not asignado:
            print(f"Alerta: No se encontró vehículo con capacidad suficiente para el pedido {pedido.id_pedido}.")

    # 5. Salida de Datos y Resumen del Estado
    print("\n[5] RESUMEN DE OPERACIONES Y ESTADOS")
    print("\n--- Entregas Programadas ---")
    print(entrega_p01.obtener_info())
    print(entrega_p02.obtener_info())
    
    print("\n--- Conductores ---")
    print(chofer_1.obtener_info())
    print(chofer_2.obtener_info())

if __name__ == "__main__":
    main()