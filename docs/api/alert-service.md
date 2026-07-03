# Référence code — alert-service

Documentation **Markdown** (MkDocs) avec exemples Python exécutables (`doctest`).

## StateMetadata — gravité et libellés

`StateMetadata` fournit le rang de sévérité et les libellés affichés pour chaque état capteur.

```python
>>> from alert_service.state_config import StateMetadata, SensorState
>>> StateMetadata.rank(SensorState.NORMAL)
0
>>> StateMetadata.rank(SensorState.WARNING)
1
>>> StateMetadata.rank(SensorState.CRITICAL)
2
>>> StateMetadata.label(SensorState.NORMAL)
'Normal'
>>> StateMetadata.label(SensorState.CRITICAL)
'Critique'
```

## Ordre d'affichage des états

Les états sont triés du plus grave au moins grave (utile pour le dashboard).

```python
>>> from alert_service.state_config import StateMetadata, SensorState
>>> StateMetadata.ordered()[0]
<SensorState.CRITICAL: 'CRITICAL'>
>>> StateMetadata.ordered()[-1]
<SensorState.NORMAL: 'NORMAL'>
```
