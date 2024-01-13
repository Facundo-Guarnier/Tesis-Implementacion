import time
import traci
import traci.constants as tc


#! Obtener la cantidad de vehículos en una calle
def getVehiculos(edge):
    v = traci.edge.getLastStepVehicleNumber(edge)
    print(f"Vehículos: {v}")
    return v

#! Cambiar el color del semáforo (ejemplo: ponerlo en verde)
def cambiarEstado(semaforo, estado):
    traci.trafficlight.setRedYellowGreenState(semaforo, estado)

#! Obtener el estado actual del semáforo
def getEstado(semaforo):
    e = traci.trafficlight.getRedYellowGreenState(semaforo)
    print("Estado del semáforo: {e}")
    return e    


#! Iniciar la simulación de SUMO
traci.start(["sumo-gui", "-c", "SUMO/Mapa/osm.sumocfg"])

#! Main loop
while traci.simulation.getMinExpectedNumber() > 0:
    print("")
    print("Paso simulación: ", traci.simulation.getTime())



    getEstado("585119522")

    # cambiarEstado("585119522", "rrrrrrrrrr")

    getVehiculos("376549265")



    #! Avanzar la simulación un paso
    print("Avanzar la simulación un paso")
    traci.simulationStep()

#! Detener la simulación de SUMO al finalizar
traci.close()
