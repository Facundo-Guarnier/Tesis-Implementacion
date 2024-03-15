from flask import Flask, jsonify

class DetectorFlask(Flask):
    """
    La "lógica o toma de decisiones" consultará a la API para saber la cantidad de vehículos que hay en cada zona.
    """
    
    def __init__(self, name:str, app:App):
        super().__init__(name)

        self.app = app
        
        #! Definir las rutas de la aplicación
        self.route('/cantidad', methods=['GET'])(self.cantidades)
        self.route('/cantidad/<zona>', methods=['GET'])(self.cantidad_zona)


    def cantidades(self) -> jsonify:
        """
        Cantidades de vehículos en todas las zonas.
        """
        return jsonify(
            {
                'info': f'Cantidad de todas las zonas. {self.name}',
                'zonas': [
                    {
                        "zona": "A",
                        "cantidad": 5,
                    },
                    {
                        "zona": "B",
                        "cantidad": 3,
                    },
                    {
                        "zona": "C",
                        "cantidad": 2,
                    },
                ]
            }
        ), 200
    


    def cantidad_zona(self, zona:str) -> jsonify:
        """
        Cantidad de vehículos en una zona específica.
        """
        
        return jsonify(
            {
                'info': 'Cantidad de una zona.',
                'zona': zona,
                "cantidad": 5,
            }
        ), 200

