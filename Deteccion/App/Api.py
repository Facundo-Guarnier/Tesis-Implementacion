from flask import Flask, jsonify, Response

from Deteccion.App.zonas.ZonaList import ZonaList 

class ApiDeteccion(Flask):
    """
    La "lógica o toma de decisiones" consultará a la API para saber la cantidad de 
    vehículos que hay en cada zona.
    """
    
    def __init__(self, name:str):
        super().__init__(name)
        
        self.zonas = ZonaList()
        
        #! Definir las rutas de la aplicación
        self.route('/cantidad', methods=['GET'])(self.cantidades)
        self.route('/cantidad/<zona_name>', methods=['GET'])(self.cantidad_zona)


    def cantidades(self) -> tuple[Response, int]:
        """
        Cantidades de vehículos en todas las zonas.
        """
        return jsonify(self.zonas.get_cantidades()), 200


    def cantidad_zona(self, zona_name:str) -> tuple[Response, int]:
        """
        Cantidad de vehículos en una zona específica.
        """
        return jsonify(
            {
                "zona": zona_name,
                "cantidad_detecciones": self.zonas.get_cantidad_zona(zona_name),
            }
        ), 200