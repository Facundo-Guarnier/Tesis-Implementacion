# 📚 Referencias y Comandos Útiles

## 🎯 Referencias para el Detector

[Detección y conteo de objetos con Yolov5](https://www.youtube.com/watch?v=sy8uRDZw8pk)

[Dominando la Detección y Conteo de Vehículos en Video con YOLO v8](https://www.youtube.com/watch?v=oig4o9RW_aM)

## 🔗 Enlaces Útiles

[Documentación de traci para Edges en SUMO](https://sumo.dlr.de/pydoc/traci._edge.html#EdgeDomain-getLastStepVehicleIDs)

[Video Tutorial de SUMO](https://www.youtube.com/watch?v=zQH1n0Fvxes)

## ⚙️ Comandos de SUMO

Generar viajes aleatorios con parámetros específicos:

```bash
netedit

python C:/Programas/SUMO/tools/randomTrips.py -n D:\Repositorios_GitHub\Tesis-Implementacion\SUMO\Mapa\osm.net.xml.gz --fringe-factor 50 --random --binomial 4

python C:/Programas/SUMO/tools/randomTrips.py -n D:\Repositorios_GitHub\Tesis-Implementacion\SUMO\MapaDe0\red.net.xml -r routes.rou.xml -e 20000 --period 2.2,1.9 --fringe-factor max --seed 7 --random
```

```
-e: tiempo
--period: cantidad que sale por segundo entre esos 2 números (1/periodo)
--fringe-factor: Solo spawn en los bordes
```
