# ✅ TODO

## ⚙️ Principal

    [ ] Ver como registrar estas tareas (TODOs), que no sea en un txt pero que sea visibles para todos
    [ ] Comprender la estructura general del proyecto (Deteccion, Decision, Reporte, SUMO)
    [ ] Implementar ramas para cada cosa usando un kanban
    [ ] Buscar alguna forma para saber que librerías se necesitan y dejarlas en un archivo `dependencies`
    [ ] Revisar la necesidad de tener multiples APIs o no.
    [ ] Refactorizar `config.yaml`, simplificar su uso.
    [ ] Refactorizar la forma de mostrar las 2 simulaciones (con tiempos fijos y con toma de decision)
    [ ] Refactorizar estructuras y usar ingles
    [ ] Actualizar el project_structure.md

## 🔩 General

    [ ] Dockerizar o implementar otra forma de despliegue.
    [ ] Agregar 100 / (tiempo + cantidad + 100) ??

    [ ] Mejorar la descripcion de los metodos: attributes, args, returns...
    [ ] Limpiar los endpoints que no se usan.

    [x] Hacer lo de la multas con los autos de la Zona C, parece que está bastante bien grabado.
    [x] Revisar las multas. Como funcionan las lineas? tiene que pasar el centro o el box entero de un objeto para ser contado?
    [x] Los reportes se guarden en una DB así puedo hacer consultas.
    [x] Las alertas que se guarden en un .log
    [~] No puedo usar flask en debug porque duplica al hilo detector.
    [x] ¿Qué conviene?: El Detector notifique a la Lógica o la Lógica consulte al Detector.
        Creo que conviene que la lógica solicite la cantidad al detector.

## 🤔 Toma de decisiones

    [ ] Buscar a ver si hay algún parametro de traci que indique el tipo total de los autos en una calle, no importa si es detenido o no.
    [ ] En vez de tiempo de espera por calle, que sea por carril?
    [ ] Agregar tf.keras.layers.Dropout(0.15) ?
                tf.keras.layers.MaxPool2D() ?

    [x] Agregar las luces en amarillo antes de aplicar la accion futura que eligió el modelo.
    [x] REVISAR POLITICA
    [x] REVISAR LA FUNCION DE RECOMPENSA.
    [x] Cambiar estado de cantidad por tiempo de espera
    [x] Ejecutar sumo sin gui: sumo -c your_configuration_file.sumocfg --no-gui
    [x] Evitar que los semaforos se pongan todos en verdes: nunca porque no está en las opciones que le dí al modelo.
    [x] Ver porque hace 2 peticiones de "GET /cantidad".

    [-] Agregar algún tipo de regla para los vehiculos que llevan mucho esperando.
    [-] Evitar que un semaforo se quede para siempre en verde.

## 🚦 SUMO

    [ ] Se puede medir las emisiones de CO2 con SUMO (getCO2Emission), consumo combustible, etc.

    [x] Arreglar que los autos se quedan frenado en las subidas al acceso (cuando pasa de 3 a 2 carriles)
    [x] Reducir la longitud de las calles que son "zonas" para que no tome toda la calle. Ej: todo el lateral del acceso al lado del carrefour.
    [x] Api
    [x] Aprender sobre SUMO, a ver si puedo obtener info de la cantidad de vehículos y si puedo modificar los semáforos.

## 🚗 Detector

    [ ] Detectar varios videos a la vez.

    [ ] Detectar ambulancias y patrulleros.
    [ ] Agregar try/except.

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
