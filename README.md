# UrbanHub — Water Quality Microservice

> **Atelier 2 — Micro-boucle XP** | Génie logiciel · Niveau Master
> Pratiques : TDD · Pair Programming · CI/CD

---

## Contexte

Cet atelier s'inscrit dans le projet **UrbanHub**, une plateforme Smart City fluviale. Il porte sur l'implémentation d'une règle métier de détection automatique des anomalies de qualité de l'eau en appliquant la discipline XP :

- **TDD** — écrire les tests avant le code (cycle Red → Green → Refactor)
- **Pair Programming** — rôles Driver / Navigator alternés
- **CI/CD** — pipeline lint + tests + build en moins de 10 minutes

### Lien avec le backlog SCRUM

| Story    | Description                                  |
| -------- | -------------------------------------------- |
| SCRUM-8  | Surveiller la qualité de l'eau en temps réel |
| SCRUM-11 | Détecter les seuils d'anomalie               |
| BF04     | Détecter les situations anormales            |

---

## Microservice choisi : Water-Quality

Parmi les quatre microservices proposés (Air-Quality, Traffic-Signal, Parking-Alert, Maintenance), **Water-Quality** a été retenu car il correspond directement aux stories SCRUM-8 et SCRUM-11 et offre une règle métier claire et testable unitairement.

### Règle métier implémentée

Le service évalue la **turbidité de l'eau** (en NTU) et retourne un statut selon les seuils suivants :

La turbidité de l’eau (souvent appelée “eau trouble”) désigne simplement le degré de clarté ou de transparence de l’eau.

## 💧 Définition simple

👉 La turbidité, c’est la présence de particules en suspension dans l’eau qui empêchent la lumière de passer correctement.

Ces particules peuvent être :

boue / argile
sable
matières organiques (feuilles, algues)
micro-organismes (bactéries, plancton)
👀 Exemple concret
Eau claire → faible turbidité ✅
Eau marron après pluie → forte turbidité ❌

👉 Plus l’eau est trouble, plus la turbidité est élevée.

## 📏 Comment on la mesure ?

La turbidité se mesure avec un appareil appelé turbidimètre, en unités :
👉 NTU (Nephelometric Turbidity Unit)

0–1 NTU → eau très claire

5 NTU → eau déjà trouble

très élevé → eau impropre à la consommation

## Plage de turbidité

| Plage de turbidité                    | Statut     | Alerte |
| ------------------------------------- | ---------- | ------ |
| ≤ seuil attention                     | `NORMAL`   | non    |
| > seuil attention et < seuil critique | `WARNING`  | oui    |
| ≥ seuil critique                      | `CRITICAL` | oui    |

---

## Structure du projet

```
urbanhub-water-quality/
├── src/
│   └── water_quality_service.py   # Logique métier
├── tests/
│   └── test_water_quality.py      # Tests unitaires TDD
├── .pre-commit-config.yaml        # Hooks pre-commit (black, whitespace…)
├── pyproject.toml                 # Configuration projet & dépendances
└── README.md
```

---

## Étape 1 — Test d'acceptation (point de départ TDD)

Avant d'écrire une seule ligne de code métier, on rédige le scénario en Gherkin pour cadrer le comportement attendu.

```gherkin
Scénario : Turbidité critique détectée
  Given les seuils configurés sont : attention=10 NTU, critique=50 NTU
  When le capteur envoie une turbidité de 75 NTU
  Then le statut retourné est "CRITICAL"
  And une alerte est générée
```

Ce scénario est immédiatement traduit en code dans `tests/test_water_quality.py` :

```python
def test_turbidite_critique():
    service = WaterQualityService(warning_threshold=10, critical_threshold=50)
    result = service.evaluate_turbidity(75)
    assert result.status == "CRITICAL"
    assert result.alert == True
```

> Ce test est lancé **avant** que `WaterQualityService` existe. Il échoue avec `ModuleNotFoundError`. C'est intentionnel — c'est le point de départ du TDD.

---

## Étape 2 — Boucle 1 : Red → Green → Refactor

### 🔴 RED — Le test échoue

```
ModuleNotFoundError: No module named 'water_quality_service'
```

Le test est rouge car la classe n'existe pas encore. C'est la preuve que le test est valide et qu'il guide le développement.

**Commit associé :** `init: Xp course project structure`

---

### 🟢 GREEN — Minimum de code pour faire passer le test

On crée `src/water_quality_service.py` avec le strict minimum :

```python
class Result:
    def __init__(self, status: str, alert: bool):
        self.status = status
        self.alert = alert


class WaterQualityService:
    def __init__(self, warning_threshold: float, critical_threshold: float):
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold

    def evaluate_turbidity(self, value: float) -> Result:
        if value > self.critical_threshold:
            return Result(status="CRITICAL", alert=True)
        return Result(status="NORMAL", alert=False)
```

Le test `test_turbidite_critique` passe. On ne va pas plus loin — pas de cas `WARNING` encore, ce n'est pas ce que le test demande.

**Commit associé :** `feat(turbidity): GREEN loop 1 - critical case`

---

### 🔵 REFACTOR — Nettoyage sans casser les tests

- Ajout des annotations de type (`float`, `-> Result`)
- Renommage des paramètres pour correspondre au vocabulaire métier (`warning_threshold`, `critical_threshold`)
- Vérification : le test reste vert après chaque modification

```python
def evaluate_turbidity(self, value: float) -> Result:
    if value >= self.critical_threshold:
        return Result(status="CRITICAL", alert=True)
    return Result(status="NORMAL", alert=False)
```

> Note : la condition passe de `>` à `>=` pour inclure la valeur exacte du seuil critique (cas limite).

---

## Étape 3 — Boucle 2 : Red → Green → Refactor

### 🔴 RED — Nouveau test pour le cas WARNING

```python
def test_turbidite_attention():
    service = WaterQualityService(warning_threshold=10, critical_threshold=50)
    result = service.evaluate_turbidity(25)
    assert result.status == "WARNING"
    assert result.alert == True
```

Ce test échoue : pour une valeur de 25, le code retourne `"NORMAL"` car seul le cas critique est géré.

---

### 🟢 GREEN — Ajout du cas WARNING

```python
def evaluate_turbidity(self, value: float) -> Result:
    if value >= self.critical_threshold:
        return Result(status="CRITICAL", alert=True)
    elif value > self.warning_threshold:
        return Result(status="WARNING", alert=True)
    else:
        return Result(status="NORMAL", alert=False)
```

Les deux tests passent.

**Commit associé :** `feat(turbidity): GREEN loop 2 - warning case + normal`

---

### 🔵 REFACTOR — Généralisation et nettoyage

La structure `if / elif / else` est claire et couvre les trois états. Le refactoring consiste à :

- Supprimer les fichiers de configuration redondants (`flake8` retiré au profit de `black` uniquement)
- Supprimer les fichiers inutilisés créés lors de l'initialisation

**Commits associés :**

- `chore: remove flake8, black can manage code format`
- `refactor: Remove unused files`

---

## Étape 4 — Tests unitaires dérivés (suite)

Deux tests supplémentaires sont ajoutés pour couvrir les cas limites :

```python
def test_turbidite_normale():
    service = WaterQualityService(warning_threshold=10, critical_threshold=50)
    result = service.evaluate_turbidity(5)
    assert result.status == "NORMAL"
    assert result.alert == False


def test_turbidite_exactement_au_seuil_critique():
    service = WaterQualityService(warning_threshold=10, critical_threshold=50)
    result = service.evaluate_turbidity(50)
    assert result.status == "CRITICAL"
    assert result.alert == True
```

### Récapitulatif des 4 tests

| Test                                          | Valeur | Statut attendu | Alerte  |
| --------------------------------------------- | ------ | -------------- | ------- |
| `test_turbidite_critique`                     | 75 NTU | `CRITICAL`     | `True`  |
| `test_turbidite_attention`                    | 25 NTU | `WARNING`      | `True`  |
| `test_turbidite_normale`                      | 5 NTU  | `NORMAL`       | `False` |
| `test_turbidite_exactement_au_seuil_critique` | 50 NTU | `CRITICAL`     | `True`  |

---

## Étape 5 — Configuration CI/CD

### Pre-commit (qualité locale)

Le fichier `.pre-commit-config.yaml` configure des hooks exécutés à chaque `git commit` :

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.3.0
    hooks:
      - id: black # Formatage automatique du code

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace # Supprime les espaces en fin de ligne
      - id: end-of-file-fixer # Assure une ligne vide en fin de fichier
      - id: check-yaml # Valide la syntaxe YAML
      - id: check-toml # Valide la syntaxe TOML
```

### Pipeline GitHub Actions (CI distante)

Fichier `.github/workflows/ci.yml` à créer pour automatiser les 3 étapes obligatoires :

```yaml
name: CI - WaterQuality UrbanHub

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.13"

      - name: Install dependencies
        run: pip install pytest black

      # ÉTAPE 1 — Lint
      - name: Lint (black)
        run: black --check .

      # ÉTAPE 2 — Tests unitaires
      - name: Unit tests (pytest)
        run: pytest tests/ -v

      # ÉTAPE 3 — Build
      - name: Build check
        run: python -c "from src.water_quality_service import WaterQualityService; print('Build OK')"
```

---

## Étape 6 — Code final

### `src/water_quality_service.py`

```python
class Result:
    def __init__(self, status: str, alert: bool):
        self.status = status
        self.alert = alert


class WaterQualityService:
    def __init__(self, warning_threshold: float, critical_threshold: float):
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold

    def evaluate_turbidity(self, value: float) -> Result:
        if value >= self.critical_threshold:
            return Result(status="CRITICAL", alert=True)
        elif value > self.warning_threshold:
            return Result(status="WARNING", alert=True)
        else:
            return Result(status="NORMAL", alert=False)
```

### `tests/test_water_quality.py`

```python
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from water_quality_service import WaterQualityService

# Scénario : Turbidité critique détectée (SCRUM-8 + SCRUM-11)
# Given les seuils configurés sont : attention=10, critique=50
# When le capteur envoie une turbidité de 75 NTU
# Then le statut retourné est "CRITICAL"
# And une alerte est générée


def test_turbidite_critique():
    service = WaterQualityService(warning_threshold=10, critical_threshold=50)
    result = service.evaluate_turbidity(75)
    assert result.status == "CRITICAL"
    assert result.alert == True


def test_turbidite_attention():
    service = WaterQualityService(warning_threshold=10, critical_threshold=50)
    result = service.evaluate_turbidity(25)
    assert result.status == "WARNING"
    assert result.alert == True


def test_turbidite_normale():
    service = WaterQualityService(warning_threshold=10, critical_threshold=50)
    result = service.evaluate_turbidity(5)
    assert result.status == "NORMAL"
    assert result.alert == False


def test_turbidite_exactement_au_seuil_critique():
    service = WaterQualityService(warning_threshold=10, critical_threshold=50)
    result = service.evaluate_turbidity(50)
    assert result.status == "CRITICAL"
    assert result.alert == True
```

---

## Étape 7 — Historique des commits (trace des boucles R-G-R)

```
89751ce  refactor: Remove unused files
231fde9  feat(turbidity): GREEN loop 2 - warning case + normal
72c0d87  chore: remove flake8, black can manage code format
f18d623  feat(turbidity): GREEN loop 1 - critical case
9018e28  init: Xp course project structure
```

Chaque commit correspond à une étape identifiable du cycle TDD. Pas de gros commit unique : la progression est traçable.

---

## Étape 8 — Rétro Pairing (Driver / Navigator)

### Ce qui a bien fonctionné

- Le **Navigator** anticipait les cas limites (valeur exacte au seuil, cas négatifs) que le Driver n'envisageait pas encore en tapant le code.
- Le fait de committer à chaque boucle RED-GREEN-REFACTOR a permis de ne jamais perdre un état stable.
- Écrire le test en Gherkin d'abord a aligné les deux membres du binôme sur la même définition du comportement attendu.

### Ce qui était difficile

- Résister à l'envie d'écrire plus de logique que nécessaire lors du GREEN (tentation d'ajouter le cas WARNING dès la boucle 1).
- Alterner les rôles régulièrement : la concentration sur le problème pousse naturellement à garder le clavier.

### Ce qu'on referait différemment

- Switcher Driver/Navigator à chaque boucle R-G-R plutôt qu'à mi-atelier.
- Écrire le scénario Gherkin en binôme avant de toucher le clavier, pas après coup.

---

## Lancer les tests localement

```bash
# Installer les dépendances de développement
uv sync --group dev

# Lancer les tests
pytest tests/ -v

# Vérifier le formatage
black --check .

# Installer les hooks pre-commit
pre-commit install
```

---

## Acces API IoT (Hub'Eau) et connexion du client

Le client IoT du projet (`src/hubeau_client.py`) se connecte a l'API Hub'Eau Hydrometrie pour recuperer les mesures de la Seine.

### 1) Endpoint utilise

- URL de base : `https://hubeau.eaufrance.fr/api/v2/hydrometrie/observations_tr`
- Station Seine configuree dans le projet : `code_entite=F700000103`
- Grandeurs interrogees :
  - `H` : niveau d'eau (retourne en mm, converti en metres dans le code)
  - `Q` : debit (retourne en L/s, converti en m3/s dans le code)

Exemple d'appel manuel :

```bash
curl "https://hubeau.eaufrance.fr/api/v2/hydrometrie/observations_tr?code_entite=F700000103&grandeur_hydro=H&size=5&pretty"
```

### 2) Verifier l'acces API depuis votre machine

Test niveau (H) :

```bash
curl "https://hubeau.eaufrance.fr/api/v2/hydrometrie/observations_tr?code_entite=F700000103&grandeur_hydro=H&size=1&pretty"
```

Test debit (Q) :

```bash
curl "https://hubeau.eaufrance.fr/api/v2/hydrometrie/observations_tr?code_entite=F700000103&grandeur_hydro=Q&size=1&pretty"
```

Si la cle `data` contient des elements, le client pourra recuperer les donnees.

### 3) Lancer le client pour recuperer les donnees

```bash
uv run python main.py
```

Le script :
- appelle Hub'Eau via `HubEauSensorClient`
- construit une mesure capteur (`SensorMeasurement`)
- envoie la mesure au `WaterQualityService` pour analyse
- affiche le statut global et les alertes eventuelles

### 4) Changer la station fluviale

Dans `main.py`, modifier le parametre `code_entite` :

```python
client = HubEauSensorClient(code_entite="F700000103")
```

Vous pouvez remplacer cette valeur par un autre code station Hub'Eau pour pointer une autre zone.

> Note : l'endpoint hydrometrie ne fournit pas le pH ni la turbidite. Dans la version actuelle, ces deux valeurs sont des valeurs par defaut configurees dans le client.

---

## Récapitulatif des livrables

| Livrable                                   | Fichier                        | Statut  |
| ------------------------------------------ | ------------------------------ | ------- |
| Code métier                                | `src/water_quality_service.py` | Complet |
| Tests unitaires (4 tests, 2 boucles R-G-R) | `tests/test_water_quality.py`  | Complet |
| Hooks pre-commit (lint local)              | `.pre-commit-config.yaml`      | Complet |
| Pipeline CI distant                        | `.github/workflows/ci.yml`     | Complet |
| Rétro Pairing                              | Section ci-dessus              | Complet |
