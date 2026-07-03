# Doctests de la documentation

Les blocs ci-dessous sont des **exemples exécutables** intégrés à la doc MkDocs.
Ils sont validés par le plugin [`pytest-doctest-mkdocstrings`](https://pypi.org/project/pytest-doctest-mkdocstrings/)
lors du build CI et en local.

## alert-service — gravité des états

```python
>>> from alert_service.state_config import StateMetadata, SensorState
>>> StateMetadata.rank(SensorState.NORMAL)
0
>>> StateMetadata.rank(SensorState.CRITICAL)
2
>>> StateMetadata.label(SensorState.WARNING)
'Attention'
```

## iot-service — mapping Hub'Eau

```python
>>> from iot_service.station_mapping import get_station_for_sensor, get_sensor_ids
>>> get_station_for_sensor("SEINE-BERCY-003").station_code
'03081000'
>>> len(get_sensor_ids())
6
```

## iot-service — simulateur

```python
>>> from iot_service.simulator.sensors import get_sensor
>>> get_sensor("SEINE-BERCY-003").sensor_id
'SEINE-BERCY-003'
```
