
# General

[ ] DIVIDIR EN CLASES MAS PEQUEÑAS, mucho lío de funcionalidades.
    Ver principalmente clase App, Api y Detector.
    Video no deberia manejar zona.
    Detector hace falta que sea singleton?
    Detector tiene procesar_guardar y procesar_vivo, optimizar estas 2.

[ ] Agregar una detección que sea en vivo con cámara.
[ ] Tomar mediciones de tiempo en los semáforos reales.

[~] No puedo usar flask en debug porque duplica al hilo detector.

[x] ¿Qué conviene?: El Detector notifique a la Lógica o la Lógica consulte al Detector.
    Creo que conviene que la lógica solicite la cantidad al detector.


# Toma de decisiones

https://www.youtube.com/watch?v=zQH1n0Fvxes
https://www.tutorai.me/modules/Introducci%C3%B3n%20a%20la%20biblioteca%20sumo%20TraCI?description=Este+m%C3%B3dulo+te+proporcionar%C3%A1+una+introducci%C3%B3n+a+la+biblioteca+sumo+TraCI%2C+explicando+qu%C3%A9+es+y+para+qu%C3%A9+se+utiliza?utm_source=manual&utm_medium=link&utm_campaign=first
[ ] Arreglar que los autos se quedan frenado en las subidas al acceso (cuando pasa de 3 a 4 carriles)

[x] Aprender sobre SUMO, a ver si puedo obtener info de la cantidad de vehículos y si puedo modificar los semáforos.


# Detector

https://www.youtube.com/watch?v=sy8uRDZw8pk
https://www.youtube.com/watch?v=oig4o9RW_aM
[ ] Usar el callback de Detector en la clase de detectar en Vivo.
[ ] Agregar try/except.
[ ] Ver si puedo estabilizar los videos.
[ ] Detectar ambulancias y patrulleros.

[~] Ver si puedo detectar varios videos a la vez: No da la potencia de procesamiento y no puedo usar la gpu por ser AMD.

[x] Pasar el socket a Flask como si fuera una API.
[x] Ver si puedo hacer que el detector sea en vivo.
[x] Sistema de notificaciones (productor/consumidor) para que el detector pueda enviar la cantidad de vehículos mediante socket.
[x] Hacer que devuelva la cantidad de vehículos en cada zona.
[x] Agregar la detección en las distintas Zonas.
[x] Cambiar tamaño fijo de letras y lineas por un factor de escala.
[x] Borrar la linea de in/out


# Instalaciones

- pip install Flask


# Estructura
Detector/
├── App/
│   ├── __init__.py
│   ├── Detector.py
│   ├── Api.py
│   └── ...
├── requirements.txt
└── run.py
