# TP 2 — Audit outillage UrbanHub (SAST + SCA + secrets)

> **Objectif du cours** : prendre une **photo initiale** des vulnérabilités du code et des dépendances.
> **Livrables** : justification du combo · top findings · plan de remédiation · dossier `evidence/`.

---

## 1. Quels problèmes essayons-nous de résoudre ?

Le threat model (TP1) dit *où* ça peut casser. Le TP2 répond : **qu’est-ce qui est déjà cassé dans le code aujourd’hui ?**

| # | Problème | Traduction débutant |
|---|---|---|
| P1 | Bugs de sécurité dans **notre code** | Ex. appel HTTP dangereux, exception silencieuse |
| P2 | Failles dans les **bibliothèques** | Ex. `starlette` vulnérable via FastAPI |
| P3 | **Secrets** commités (clés, mots de passe) | Token AWS / mot de passe DB dans Git |
| P4 | Trop d’outils possibles → mauvais choix | Perdre 2 h sur un outil inadapté à Python |
| P5 | Rapport illisible pour le RSSI | 200 lignes de JSON sans top 10 ni plan |

En une phrase :
**« Quels sont les findings concrets sur UrbanHub, classés, avec un plan pour les corriger ? »**

---

## 2. Pourquoi les résoudre ?

| Pourquoi | Explication |
|---|---|
| **Baseline** | Sans photo initiale, on ne mesure aucun progrès |
| **3 angles différents** | SAST ≠ SCA ≠ secrets : chacun voit ce que les autres ne voient pas |
| **Décision RSSI** | Il faut un top priorisé, pas un dump d’outil |
| **Préparer TP3/TP4** | Les findings deviennent le backlog de remédiation et les futurs gates |
| **Éviter la prod aveugle** | Mergers du code vulnérable sans le savoir |

Rappel cours :

- **SAST** lit le code source
- **SCA** lit la liste des dépendances
- **Secrets scan** cherche les fuites dans Git / fichiers

---

## 3. Comment on s’y prend pour les résoudre ?

### Étape A — Justifier le combo d’outils (matrice)

Sur UrbanHub (Python / FastAPI), le combo retenu :

| Besoin | Outil | Pourquoi |
|---|---|---|
| SAST | **Bandit** | Spécialisé Python, simple, CWE/sévérité |
| SCA | **Trivy fs** | CVE sur `uv.lock`, même outil réutilisable en image/IaC |
| Secrets | **Gitleaks** | Rapide, patterns natifs, sortie SARIF |

Note d’1 page : déjà dans `evidence/urbanhub-audit-report.md` (§ justification).

### Étape B — Exécuter les scans en local (Docker)

Depuis la racine du projet :

```bash
# 1) SAST — Bandit
docker run --rm -v "$PWD:/src" -w /src python:3.12-slim \
  bash -c "pip install -q bandit && bandit -r iot-service/src alert-service/src -f json -o evidence/bandit.json"

# 2) SCA — Trivy
docker run --rm -v "$PWD:/src" aquasec/trivy:latest fs \
  --severity HIGH,CRITICAL --scanners vuln --format json \
  -o /src/evidence/trivy-iot.json /src/iot-service

docker run --rm -v "$PWD:/src" aquasec/trivy:latest fs \
  --severity HIGH,CRITICAL --scanners vuln --format json \
  -o /src/evidence/trivy-alert.json /src/alert-service

# 3) Secrets — Gitleaks (historique Git)
docker run --rm -v "$PWD:/src" -w /src zricethezav/gitleaks:latest \
  detect --report-format sarif --report-path /src/evidence/gitleaks-git.sarif --no-banner
```

Astuce Windows (logs propres) : `evidence/run-audit.ps1` + `evidence/GUIDE-CAPTURES.md`.

### Étape C — Consolider le top findings

Tableau type cours :

`ID · outil · fichier/ligne · sévérité · CWE · description · exploitabilité`

Sur ce dépôt (résultats réels) :

| ID | Outil | Objet | Sévérité |
|---|---|---|---|
| F-01..F-04 | Trivy | `starlette@1.0.0` (2 CVE × 2 services) | HIGH |
| F-05 | Bandit B310 | `urlopen` Hub’Eau | MEDIUM |
| F-06 | Bandit B110 | `except/pass` WebSocket | LOW |
| F-07/F-08 | Bandit B311 | `random` simulateur | LOW |
| Secrets | Gitleaks | — | **0 secret confirmé** |

### Étape D — Plan de remédiation

Pour chaque finding : **patch / upgrade / mitigation / acceptation** + propriétaire + SLA.

Déjà rédigé dans le rapport d’audit TP2.

---

## 4. Comment le tester ?

### Tests « l’outil a bien tourné »

| Test | Commande / action | OK si… |
|---|---|---|
| Bandit a produit une sortie | Ouvrir `evidence/bandit.json` | Fichier non vide, findings listés |
| Trivy a scanné les locks | Ouvrir `trivy-iot.json` / `trivy-alert.json` | CVE Starlette visibles |
| Gitleaks a scanné Git | Ouvrir `gitleaks-git.sarif` | Report présent (0 finding = OK) |
| Captures | Logs `evidence/logs-*.txt` | Lisibles pour le rendu |

### Tests « le rapport est utile »

| Test | Question | OK si… |
|---|---|---|
| Combo justifié | Pourquoi Bandit et pas SpotBugs ? | Parce que stack Python |
| Top priorisé | Le RSSI lit en 2 min ? | Oui : tableau + synthèse |
| Remédiation actionnable | Y a-t-il un owner + SLA ? | Une ligne = une action |
| Faux positifs filtrés | Les hits `.venv` sont exclus ? | Oui, documentés |

### Mini auto-test

1. Quelle famille d’outil trouve une CVE dans `uv.lock` ? → **SCA (Trivy)**
2. Quelle famille trouve `urlopen` risqué dans le code ? → **SAST (Bandit)**
3. Que faire si Gitleaks trouve un vrai secret ? → **Révoquer + retirer de l’historique + bloquer en CI**
4. Pourquoi 4 findings Trivy pour 2 CVE ? → **2 services × 2 CVE**

### Preuve de rendu

- `evidence/urbanhub-audit-report.md` (+ PDF si demandé)
- JSON/SARIF dans `evidence/`
- 3 captures d’écran des runs

---

## Lien avec la suite

| TP2 produit… | TP3 / TP4 utilisent… |
|---|---|
| Liste de CVE + findings | Triage EPSS/KEV + plan daté (TP3) |
| Preuve qu’il y a des risques deps | Gates Trivy / Gitleaks automatiques (TP4) |
