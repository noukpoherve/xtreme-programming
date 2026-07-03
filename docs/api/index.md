# API Python (auto-documentation)

Cette section est générée avec **[mkdocstrings](https://mkdocstrings.github.io/)** :
les signatures, docstrings et exemples `>>>` proviennent directement du code source.

Les exemples sont **exécutables** et vérifiés par `pytest-doctest-mkdocstrings` (voir [Doctests](doctests.md)).

## Modules documentés

| Service | Module | Contenu |
|---------|--------|---------|
| alert-service | `alert_service.state_config` | États capteurs, seuils, métadonnées |
| iot-service | `iot_service.station_mapping` | Mapping Hub'Eau ↔ capteurs UrbanHub |
| iot-service | `iot_service.simulator.sensors` | Profils capteurs simulés |

## Lancer la validation des exemples

```bash
uv sync --group docs --group docs-test
uv run --group docs-test pytest docs/api --doctest-modules --doctest-glob="docs/api/*.md" --doctest-mdcodeblocks -v
```
