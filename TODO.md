# TODO
## General
    [ ] Las alertas que se guarden en un .log   
    [ ] Los reportes se guarden en una DB así puedo hacer consultas.
    [ ] Agregar 100 / (tiempo + cantidad + 100) ??

    [ ] Hacer lo de la multas con los autos de la Zona C, parece que está bastante bien grabado.
    [ ] Mejorar la descripcion de los metodos: attributes, args, returns...
    [ ] Dockerizar o implementar otra forma de despliegue.
    [ ] Limpiar los endpoints que no se usan.
    
    [~] No puedo usar flask en debug porque duplica al hilo detector.
    [x] ¿Qué conviene?: El Detector notifique a la Lógica o la Lógica consulte al Detector.
        Creo que conviene que la lógica solicite la cantidad al detector.


## Toma de decisiones
    [ ] Buscar a ver si hay algún parametro de traci que indique el tipo total de los autos en una calle, no importa si es detenido o no.
    [ ] En vez de tiempo de espera por calle, que sea por carril?
    [ ] Agregar tf.keras.layers.Dropout(0.15) ?

    [x] Agregar las luces en amarillo antes de aplicar la accion futura que eligió el modelo.
    [x] REVISAR POLITICA
    [x] REVISAR LA FUNCION DE RECOMPENSA.
    [x] Cambiar estado de cantidad por tiempo de espera
    [x] Ejecutar sumo sin gui: sumo -c your_configuration_file.sumocfg --no-gui
    [x] Evitar que los semaforos se pongan todos en verdes: nunca porque no está en las opciones que le dí al modelo.
    [x] Ver porque hace 2 peticiones de "GET /cantidad".

    [-] Agregar algún tipo de regla para los vehiculos que llevan mucho esperando. 
    [-] Evitar que un semaforo se quede para siempre en verde.


## SUMO
    [ ] Se puede medir las emisiones de CO2 con SUMO (getCO2Emission), consumo combustible, etc.

    [x] Arreglar que los autos se quedan frenado en las subidas al acceso (cuando pasa de 3 a 2 carriles)
    [x] Reducir la longitud de las calles que son "zonas" para que no tome toda la calle. Ej: todo el lateral del acceso al lado del carrefour.
    [x] Api
    [x] Aprender sobre SUMO, a ver si puedo obtener info de la cantidad de vehículos y si puedo modificar los semáforos.


## Detector
    [ ] Detectar varios videos a la vez.

    [ ] Agregar try/except.
    [ ] Detectar ambulancias y patrulleros.

    [~] Ver si puedo detectar varios videos a la vez: No da la potencia de procesamiento y no puedo usar la gpu por ser AMD.

    [x] Detectar tiempo de espera
    [x] Agregar una detección que sea en vivo con cámara.
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


# INFO
## Detector:
https://www.youtube.com/watch?v=sy8uRDZw8pk

https://www.youtube.com/watch?v=oig4o9RW_aM

## Sumo:
netedit

    python C:/Programas/SUMO/tools/randomTrips.py -n D:\Repositorios_GitHub\Tesis-Implementacion\SUMO\Mapa\osm.net.xml.gz --fringe-factor 50 --random --binomial 4

    python C:/Programas/SUMO/tools/randomTrips.py -n D:\Repositorios_GitHub\Tesis-Implementacion\SUMO\MapaDe0\red.net.xml -r routes.rou.xml -e 20000 --period 2.2,1.9 --fringe-factor max --seed 7 --random

    -e: tiempo
    --period: cantidad que sale por segundo entre esos 2 números (1/periodo)
    --fringe-factor: Solo spawn en los bordes

https://sumo.dlr.de/pydoc/traci._edge.html#EdgeDomain-getLastStepVehicleIDs 

https://www.youtube.com/watch?v=zQH1n0Fvxes


# Instalaciones
- pip install Flask
- pip install mypy      #Para ver los tipos de datos de las variables.
- pip install types-PyYAML
- pip install cvzone
- pip install --upgrade opencv-python
- pip install ultralytics
- pip install traci
- pip install supervision

- sudo add-apt-repository ppa:sumo/stable -y
- sudo apt-get update
- sudo apt-get install sumo sumo-tools sumo-doc



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


# Semafors
Semaforo 1: 
GGGGGGrrrrr
yyyyyyrrrrr
rrrrrrGGgGG
rrrrrrGyGyy
rrGGGGGrGrr
rrGGGGyryrr

Semaforo 2:
GgGGrrrrGgGg
GgGGrrrryyyy
GGGGGGrrrrrr
yyyyGGrrrrrr
GrrrGGGGrrrr
yrrryyyyrrrr
grrrrrrrGGGG

Semaforo 3:
GgGgGgGGrrrr
yyyyGGGGrrrr
rrrrGGGGGGrr
rrrrGyyyGGrr
rrrrGrrrGGGG
rrrrgrrryyyy
GGGGgrrrrrrr 

Semaforo 4:
GGGrrrrGGg
yyyrrrryyy
rrrGGGGrrr
rrryyyyrrr

# Detecciones de YOLO
0: 'person'
1: 'bicycle'
2: 'car'
3: 'motorcycle'
4: 'airplane'
5: 'bus'
6: 'train'
7: 'truck'
8: 'boat'
9: 'traffic light'
10: 'fire hydrant'
11: 'stop sign'
12: 'parking meter'
13: 'bench'
14: 'bird'
15: 'cat'
16: 'dog'
17: 'horse'
18: 'sheep'
19: 'cow'
20: 'elephant'
21: 'bear'
22: 'zebra'
23: 'giraffe'
24: 'backpack'
25: 'umbrella'
26: 'handbag'
27: 'tie'
28: 'suitcase'
29: 'frisbee'
30: 'skis'
31: 'snowboard'
32: 'sports ball'
33: 'kite'
34: 'baseball bat'
35: 'baseball glove'
36: 'skateboard'
37: 'surfboard'
38: 'tennis racket'
39: 'bottle'
40: 'wine glass'
41: 'cup'
42: 'fork'
43: 'knife'
44: 'spoon'
45: 'bowl'
46: 'banana'
47: 'apple'
48: 'sandwich'
49: 'orange'
50: 'broccoli'
51: 'carrot'
52: 'hot dog'
53: 'pizza'
54: 'donut'
55: 'cake'
56: 'chair'
57: 'couch'
58: 'potted plant'
59: 'bed'
60: 'dining table'
61: 'toilet'
62: 'tv'
63: 'laptop'
64: 'mouse'
65: 'remote'
66: 'keyboard'
67: 'cell phone'
68: 'microwave'
69: 'oven'
70: 'toaster'
71: 'sink'
72: 'refrigerator'
73: 'book'
74: 'clock'
75: 'vase'
76: 'scissors'
77: 'teddy bear'
78: 'hair drier'
79: 'toothbrush'