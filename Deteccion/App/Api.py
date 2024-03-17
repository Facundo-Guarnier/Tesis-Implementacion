from flask import Flask, jsonify
from ZonaList import ZonaList

class DetectorFlask(Flask):
    """
    La "lógica o toma de decisiones" consultará a la API para saber la cantidad de 
    vehículos que hay en cada zona.
    """
    
    def __init__(self, name:str):
        super().__init__(name)

        #! Definir las rutas de la aplicación
        self.route('/cantidad', methods=['GET'])(self.cantidades)
        self.route('/cantidad/<zona>', methods=['GET'])(self.cantidad_zona)


    def cantidades(self) -> jsonify:
        """
        Cantidades de vehículos en todas las zonas.
        """
        
        zonas = ZonaList()
        return jsonify(zonas.get_cantidades()), 200


    def cantidad_zona(self, zona:str) -> jsonify:
        """
        Cantidad de vehículos en una zona específica.
        """
        zonas = ZonaList()
        return jsonify(
            {
                "zona": zona,
                "cantidad_detecciones": zonas.get_cantidad_zona(zona),
            }
        ), 200