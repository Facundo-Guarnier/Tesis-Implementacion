import threading
import time

from App.zonas.ZonaList import ZonaList
from flask import Flask, jsonify
from App.App import App

class DetectorFlask(Flask):
    """
    La "lógica o toma de decisiones" consultará a la API para saber la cantidad de 
    vehículos que hay en cada zona.
    """
    
    def __init__(self, name:str):
        super().__init__(name)
        
        # #! Iniciar el hilo para la detección de vehículos
        # self.hilo_deteccion = threading.Thread(target=self.run_app)
        # self.hilo_deteccion.daemon = True
        # self.hilo_deteccion.start()

        #! Definir las rutas de la aplicación
        self.route('/cantidad', methods=['GET'])(self.cantidades)
        self.route('/cantidad/<zona>', methods=['GET'])(self.cantidad_zona)


    # def run_app(self):
    #     print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    #     print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    #     i = 0
    #     while True:
    #         time.sleep(5)
    #         print(f"{i}+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    #         i += 1


    def cantidades(self) -> jsonify:
        """
        Cantidades de vehículos en todas las zonas.
        """
        
        zonas = ZonaList()
        return jsonify(zonas.get_cantidades()), 200
        # return jsonify(
        #     {
        #         'info': f'Cantidad de todas las zonas. {self.name}',
        #         'zonas': [
        #             {
        #                 "zona": "A",
        #                 "cantidad": 5,
        #             },
        #             {
        #                 "zona": "B",
        #                 "cantidad": 3,
        #             },
        #             {
        #                 "zona": "C",
        #                 "cantidad": 2,
        #             },
        #         ]
        #     }
        # ), 200


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
        # return jsonify(
        #     {
        #         'zona': zona,
        #         "cantidad_detecciones": 5,
        #     }
        # ), 200