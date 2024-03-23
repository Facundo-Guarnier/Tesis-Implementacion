from flask import Flask, Response, jsonify, request

from SUMO.zonas.ZonaList import ZonaList
from SUMO.App import App

class SumoFlask(Flask):
    def __init__(self, name:str):
        super().__init__(name)
        
        self.zonas = ZonaList()
        self.app = App()
        
        #! Definir las rutas de la aplicación
        self.route('/cantidad', methods=['GET'])(self.cantidades)
        self.route('/cantidad/<zona_name>', methods=['GET'])(self.cantidad_zona)
        
        self.route('/semaforo/<id>', methods=['PUT'])(self.cambiarEstado)
        self.route('/semaforo/<id>', methods=['GET'])(self.getEstado)



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


    def cambiarEstado(self, id:str) -> tuple[Response, int]:
        """
        Cambiar el estado de un semáforo.
        - Ej: semaforo/<id>?estado=valor'
        """
        
        nuevo_estado = request.args.get('estado')

        if not nuevo_estado:
            return jsonify({"message": "No se ha especificado el nuevo estado"}), 400
        else:
            self.app.cambiarEstado(id, nuevo_estado)
            return jsonify({"message": "OK"}), 200


    def getEstado(self, id:str) -> tuple[Response, int]:
        """
        Obtener el estado de un semáforo.
        """
        return jsonify({"estado": self.app.getEstado(id)}), 200