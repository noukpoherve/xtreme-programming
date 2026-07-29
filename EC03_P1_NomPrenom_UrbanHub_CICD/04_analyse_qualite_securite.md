# Analyse qualité et sécurité — EC03 · `iot-service`

> Exporter en PDF (`04_analyse_qualite_securite.pdf`) pour le ZIP final.

## 1. Synthèse

| Volet | Outils prévus (pipeline étape 3) | Statut |
|-------|----------------------------------|--------|
| Clean code | Ruff (lint + format), Mypy | À exécuter via `01_pipeline.yml` |
| Secrets | Gitleaks | À exécuter |
| SCA | Trivy fs (`uv.lock`) | À exécuter |
| SAST | Bandit (ou Semgrep) | À exécuter |
| SBOM | CycloneDX (ex. Trivy) | À exécuter |

## 2. Résultats attendus par outil

### Ruff

```text
# Coller sortie ruff check / ruff format --check
```

### Mypy

```text
# Coller sortie mypy src/
```

### Bandit

```text
# Coller résumé (HIGH/MEDIUM) ou extrait JSON
```

### Trivy (filesystem)

```text
# Coller CVE CRITICAL/HIGH pertinentes ou « aucune CRITICAL »
```

### Gitleaks

```text
# Coller « no leaks found » ou plan de remédiation (sans secrets dans le log)
```

### SBOM

- Fichier généré : *(nom du artefact CycloneDX)*
- Usage : traçabilité des dépendances `iot-service`

## 3. Analyse et décisions

*(2–3 paragraphes : findings acceptés vs corrigés, politique de gate CRITICAL/secrets, conformité Docker non-root.)*

## 4. Conformité anonymat

Confirmation que ce rapport et les logs joints ne contiennent :

- [ ] Aucun chemin absolu personnel
- [ ] Aucun identifiant GitHub / e-mail
- [ ] Aucun secret ou token
