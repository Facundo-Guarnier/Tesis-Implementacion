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
        
        #! Cantidades
        self.route('/cantidad', methods=['GET'])(self.cantidades)
        self.route('/cantidad/<zona_name>', methods=['GET'])(self.cantidad_zona)
        
        #! Tiempos
        self.route('/espera', methods=['GET'])(self.tiempos)
        
        #! Multas
        self.route('/multas/<zona_name>', methods=['POST'])(self.activar_multas)
    
    
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
    
    
    def tiempos(self) -> tuple[Response, int]:
        """
        Devuelve los tiempos de espera en cada zona.
        """
        return jsonify({
            "tiempo_espera_total": self.zonas.get_tiempos_total(),
            "tiempos_espera": self.zonas.get_tiempos(),
        }), 200
    
    
    def activar_multas(self, zona_name:str) -> tuple[Response, int]:
        """
        Activa las multas en las zonas.
        """
        
        return jsonify({"mensaje": f"Multas {zona_name}: {self.zonas.activar_multas(zona_name)}"}), 200