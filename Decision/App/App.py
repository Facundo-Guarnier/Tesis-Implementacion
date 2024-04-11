from Decision.App.Api import ApiClient

base_url = 'http://tu_direccion_ip:puerto'  # Reemplaza con la dirección y puerto de tu servidor Flask
cliente_api = ApiClient(base_url)

# Obtener cantidad de vehículos en todas las zonas
cantidad_todas_zonas = cliente_api.obtener_cantidad_vehiculos_todas_zonas()
if cantidad_todas_zonas:
    print("Cantidad de vehículos en todas las zonas:")
    print(cantidad_todas_zonas)

# Obtener cantidad de vehículos en una zona específica
zona_name = 'nombre_de_la_zona'  # Reemplaza con el nombre de la zona deseada
cantidad_zona_especifica = cliente_api.obtener_cantidad_vehiculos_zona(zona_name)
if cantidad_zona_especifica:
    print(f"Cantidad de vehículos en la zona '{zona_name}':")
    print(cantidad_zona_especifica)
