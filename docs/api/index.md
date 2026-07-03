# Doctests MkDocs

Cette section contient des **exemples Python dans la documentation Markdown**.
Ils sont exécutés automatiquement pour vérifier que la doc reste correcte.

## Comment ça marche

1. Les pages `docs/api/*.md` contiennent des blocs ` ```python ` avec des lignes `>>>`.
2. `pytest` + `pytest-doctest-mkdocstrings` exécute ces exemples comme des tests.
3. MkDocs affiche ces pages telles quelles sur le site (pas d'injection depuis le code).

## Lancer les doctests

```bash
uv sync --group docs --group docs-test
uv run --group docs-test pytest docs/api -v
```

## Pages couvertes

| Page | Contenu testé |
|------|----------------|
| [alert-service](alert-service.md) | `StateMetadata` (rangs, libellés, ordre) |
| [iot-service](iot-service.md) | Mapping Hub'Eau, capteurs, simulateur |
| [doctests](doctests.md) | Scénarios combinés |
