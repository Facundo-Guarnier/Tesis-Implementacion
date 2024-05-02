import logging
from flask import Flask, Response, jsonify, request

from SUMO.zonas.ZonaList import ZonaList
from SUMO.App import AppSUMO

class ApiSUMO(Flask):
    def __init__(self, name:str):
        super().__init__(name)
        
        self.zonas = ZonaList()
        self.app = AppSUMO()
        
        #! Configurar el logger de Flask para evitar imprimir registros de acceso
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        
        #! Cantidad vehículos
        self.route('/cantidad', methods=['GET'])(self.getCantidades)
        self.route('/cantidad/<zona_name>', methods=['GET'])(self.getCantidadZona)
        
        #! Tiempo de espera en zona
        self.route('/espera', methods=['GET'])(self.getTiemposEspera)
        self.route('/espera2', methods=['GET'])(self.getTiemposEspera2)
        self.route('/espera/<zona_id>', methods=['GET'])(self.getTiempoEspera)
        
        #! Avanzar simulación
        self.route('/avanzar', methods=['PUT'])(self.putAvanzar)
        
        #! Semáforos
        self.route('/semaforo', methods=['GET'])(self.getEstados)
        self.route('/semaforo', methods=['PUT'])(self.putEstados)
        self.route('/semaforo/<id>', methods=['GET'])(self.getEstado)
        self.route('/semaforo/<id>', methods=['PUT'])(self.putEstado)
        
        #! Simulación ok
        self.route('/simulacion', methods=['GET'])(self.getSimulacionOK)


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
        Obtener el tiempo de espera de todas las zonas en la simulación.
        """
        return jsonify({
            "tiempo_espera_total": self.app.getTiemposEsperaTotal(),
            "tiempos_espera": self.app.getTiemposEspera()
        }), 200
    
    def getTiemposEspera2(self) -> tuple[Response, int]:
        """
        Obtener el tiempo de espera de todas las zonas en la simulación.
        """
        return jsonify({
            "tiempo_espera_total": self.app.getTiemposEsperaTotal(True),
            "tiempos_espera": self.app.getTiemposEspera(True)
        }), 200


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
        steps = request.args.get('steps', type=int)
        if steps:
            done = self.app.avanzar(steps=steps)
            return jsonify({"done": done}), 200
        else:
            return jsonify({"error": "Falta el parámetro 'steps'."}), 400
    
    
    def putEstado(self, id) -> tuple[Response, int]:
        """
        Cambiar el estado de un semáforo.
        - Ej: semaforo/<id>?estado=valor'
        """
        estado = request.args.get('estado', type=str)
        if estado:
            self.app.setSemaforoEstado(id, estado)
            return jsonify({"estado": estado}), 200
        else:
            return jsonify({"error": "Falta el parámetro 'estado'."}), 400
    
    
    def putEstados(self) -> tuple[Response, int]:
        """
        Cambiar los estado de varios semáforos.
        Ej: {data=[{'id': 1, 'estado': 'ggggggggggg'}, {'id': 2, 'estado': 'gggggggggggg'}, {'id': 3, 'estado': 'rrrrrrrrrrrr'}, {'id': 4, 'estado': 'rrrrrrrrrr'}]}
        """
        data = request.json
        if data:
            for semaforo in list(data["data"]):
                semaforo_id = semaforo["id"]
                estado = semaforo["estado"]
                self.app.setSemaforoEstado(semaforo_id, estado)
            return jsonify({"estado": estado}), 200
        else:
            return jsonify({"error": "Falta el parámetro 'estado'."}), 400
    
    
    def getSimulacionOK(self) -> tuple[Response, int]:
        """
        Verificar si la simulación está en ejecución.
        """
        return jsonify({"simulacion": self.app.getSimulacionOK()}), 200