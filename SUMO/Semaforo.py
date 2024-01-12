import time
import traci
import traci.constants as tc

#! Iniciar la simulación de SUMO
traci.start(["sumo", "-c", r"mapa\osm.sumocfg"])

#! Main loop
while traci.simulation.getMinExpectedNumber() > 0:
    #! Obtener el estado actual del semáforo
    semaforo_estado = traci.trafficlight.getRedYellowGreenState("cluster_10816689636_10816689929_1663714600")
    print("Estado del semáforo: " + semaforo_estado)

    #! Cambiar el color del semáforo (ejemplo: ponerlo en verde)
    nuevo_estado = "GGGG"
    traci.trafficlight.setRedYellowGreenState("cluster_10816689636_10816689929_1663714600", nuevo_estado)

    #! Avanzar la simulación un paso
    print("Avanzar la simulación un paso")
    traci.simulationStep()
    time.sleep(1)

#! Detener la simulación de SUMO al finalizar
traci.close()
