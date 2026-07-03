# Référence code — iot-service

Documentation **Markdown** (MkDocs) avec exemples Python exécutables (`doctest`).

## Mapping Hub'Eau

Correspondance entre les capteurs UrbanHub et les stations officielles Hub'Eau.

```python
>>> from iot_service.station_mapping import get_station_for_sensor, get_station_for_code
>>> get_station_for_sensor("SEINE-BERCY-003").station_code
'03081000'
>>> get_station_for_code("03081000").sensor_id
'SEINE-BERCY-003'
>>> get_station_for_sensor("SEINE-UNKNOWN-999") is None
True
```

## Capteurs Hub'Eau actifs

```python
>>> from iot_service.station_mapping import get_sensor_ids
>>> "SEINE-BERCY-003" in get_sensor_ids()
True
>>> len(get_sensor_ids())
6
```

## Profils simulateur

```python
>>> from iot_service.simulator.sensors import get_sensor
>>> get_sensor("SEINE-BERCY-003").sensor_id
'SEINE-BERCY-003'
```
