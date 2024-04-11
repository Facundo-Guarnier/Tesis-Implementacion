
import requests

class ApiClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def obtener_cantidad_vehiculos_todas_zonas(self):
        endpoint = '/cantidad'
        response = requests.get(self.base_url + endpoint)
        if response.status_code == 200:
            return response.json()
        else:
            return None

    def obtener_cantidad_vehiculos_zona(self, zona_name):
        endpoint = f'/cantidad/{zona_name}'
        response = requests.get(self.base_url + endpoint)
        if response.status_code == 200:
            return response.json()
        else:
            return None