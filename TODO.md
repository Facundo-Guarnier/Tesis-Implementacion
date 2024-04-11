# General

[ ] Agregar una detección que sea en vivo con cámara.
[ ] Tomar mediciones de tiempo en los semáforos reales.

[~] No puedo usar flask en debug porque duplica al hilo detector.

[x] ¿Qué conviene?: El Detector notifique a la Lógica o la Lógica consulte al Detector.
    Creo que conviene que la lógica solicite la cantidad al detector.


# Toma de decisiones
[ ] 


# SUMO
netedit
python C:/Programas/SUMO/tools/randomTrips.py -n D:\Repositorios_GitHub\Tesis-Implementacion\SUMO\Mapa\osm.net.xml.gz --fringe-factor 50 --random --binomial 4


python C:/Programas/SUMO/tools/randomTrips.py -n D:\Repositorios_GitHub\Tesis-Implementacion\SUMO\MapaDe0\red.net.xml -r routes.rou.xml -e 20000 --period 2.2,1.9 --fringe-factor max --seed 7 --random
-e: tiempo
--period: cantidad que sale por segundo entre esos 2 números (1/periodo)
--fringe-factor: Solo spawn en los bordes


https://www.youtube.com/watch?v=zQH1n0Fvxes
[x] Arreglar que los autos se quedan frenado en las subidas al acceso (cuando pasa de 3 a 2 carriles)
[x] Reducir la longitud de las calles que son "zonas" para que no tome toda la calle. Ej: todo el lateral del acceso al lado del carrefour.
[x] Api
[x] Aprender sobre SUMO, a ver si puedo obtener info de la cantidad de vehículos y si puedo modificar los semáforos.


# Detector

https://www.youtube.com/watch?v=sy8uRDZw8pk
https://www.youtube.com/watch?v=oig4o9RW_aM
[ ] Detectar varios videos a la vez.

[ ] Agregar try/except.
[ ] Detectar ambulancias y patrulleros.

[~] Ver si puedo detectar varios videos a la vez: No da la potencia de procesamiento y no puedo usar la gpu por ser AMD.

[x] DIVIDIR EN CLASES MAS PEQUEÑAS, mucho lío de funcionalidades.
    - [x] Ver principalmente clase App, Api y Detector.
    - [-] Video no deberia manejar zona.
    - [x] Detector hace falta que sea singleton?
    - [x] Detector tiene procesar_guardar y procesar_vivo, optimizar estas 2.
[x] Usar el callback de Detector en la clase de detectar en Vivo.
[x] Pasar el socket a Flask como si fuera una API.
[x] Ver si puedo hacer que el detector sea en vivo.
[x] Sistema de notificaciones (productor/consumidor) para que el detector pueda enviar la cantidad de vehículos mediante socket.
[x] Hacer que devuelva la cantidad de vehículos en cada zona.
[x] Agregar la detección en las distintas Zonas.
[x] Cambiar tamaño fijo de letras y lineas por un factor de escala.
[x] Borrar la linea de in/out


# Instalaciones

- pip install Flask
- pip install mypy      #Para ver los tipos de datos de las variables.
- pip install types-PyYAML
- pip install cvzone
- pip install --upgrade opencv-python
- pip install ultralytics
- pip install traci

# Estructura
Main/
├── Detector/
|   ├── App/
│   |   ├── Detector.py
│   |   ├── Api.py
│   |   └── ...
|   ├── Dataset/
│       ├── Dataset_original/ 
│       └── ...
|
├── SUMO/
│   ├── App.py
│   ├── Api.py
│   ├── Mapa/
│   └── ...
|
├── run.py
├── clases.drawio
└── ...