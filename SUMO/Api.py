from flask import Flask, Response, jsonify, request

from SUMO.zonas.ZonaList import ZonaList
from SUMO.App import App

class SumoFlask(Flask):
    def __init__(self, name:str):
        super().__init__(name)
        
        self.zonas = ZonaList()
        self.app = App()
        
        #! Cantidad vehículos
        self.route('/cantidad', methods=['GET'])(self.getCantidades)
        self.route('/cantidad/<zona_name>', methods=['GET'])(self.getCantidadZona)
        
        #! Tiempo de espera en zona
        self.route('/espera', methods=['GET'])(self.getTiemposEspera)
        self.route('/espera/<zona_id>', methods=['GET'])(self.getTiempoEspera)
        
        #! Avanzar simulación
        self.route('/avanzar', methods=['PUT'])(self.putAvanzar)
        
        #! Semáforos
        self.route('/semaforo', methods=['GET'])(self.getEstados)
        self.route('/semaforo/<id>', methods=['GET'])(self.getEstado)
        self.route('/semaforo/<id>', methods=['PUT'])(self.putEstado)


    def getCantidades(self) -> tuple[Response, int]:
        """
        Cantidades de vehículos en todas las zonas.
        """
        self.app.setVehiculo()
        return jsonify(self.zonas.get_cantidades()), 200


    def getCantidadZona(self, zona_name:str) -> tuple[Response, int]:
        """
        Cantidad de vehículos en una zona específica.
        """
        return jsonify(
            {
                "zona": zona_name,
                "cantidad_detecciones": self.zonas.get_cantidad_zona(zona_name),
            }
        ), 200
    
    
    def getTiemposEspera(self) -> tuple[Response, int]:
        """
        Obtener el tiempo total de espera de todas las zonas en la simulación.
        """
        return jsonify({"tiempo_espera": self.app.getTiemposEspera()}), 200


    def getTiempoEspera(self, zona_id:str) -> tuple[Response, int]:
        """
        Obtener el tiempo total de espera de una zona en la simulación.
        """
        return jsonify({"tiempo_espera": self.app.getTiempoEspera(zona_id=zona_id)}), 200
    
    
    def getEstados(self) -> tuple[Response, int]:
        """
        Obtener el estado de un semáforo.
        - Ej: semaforo'
        """
        return jsonify({"estados": self.app.getSemaforosEstados()}), 200


    def getEstado(self, id:str) -> tuple[Response, int]:
        """
        Obtener el estado de un semáforo.
        """
        return jsonify({"estado": self.app.getSemaforoEstado(id)}), 200
    
    
    def putAvanzar(self) -> tuple[Response, int]:
        """
        Avanzar la simulación.
        """
        steps = request.args.get('steps', type=int, default=10)
        done = self.app.avanzar(steps=steps)
        return jsonify({"done": done}), 200
    
    
    def putEstado(self, id:str) -> tuple[Response, int]:
        """
        Cambiar el estado de un semáforo.
        - Ej: semaforo/<id>?estado=valor'
        """
        
        nuevo_estado = request.args.get('estado')
        
        if not nuevo_estado:
            return jsonify({"message": "No se ha especificado el nuevo estado"}), 400
        else:
            self.app.cambiarEstado(semaforo=id, estado=nuevo_estado)
            return jsonify({"message": "OK"}), 200