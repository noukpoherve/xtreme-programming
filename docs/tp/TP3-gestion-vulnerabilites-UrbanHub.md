# TP 3 — Gestion des vulnérabilités UrbanHub

> **Cours** : DevSecOps & outils d'analyse de vulnérabilités
> **Chapitre** : 3 — Triage + remédiation + SBOM
> **Durée prévue** : 1 h
> **Projet** : `urbanhub-water-quality` (Python / FastAPI)
> **Public** : débutant — chaque étape est expliquée « pourquoi + comment »

---

## Ce que tu dois comprendre avant de commencer

Imagine que ton scanner (Trivy) te donne une **liste de problèmes**. Si tu traites tout dans le désordre, tu perds du temps. Le TP 3 apprend à :

1. **Lire** la gravité (CVSS)
2. **Vérifier** si c’est vraiment urgent (EPSS + KEV)
3. **Croiser** avec l’importance métier UrbanHub (eau = vie humaine)
4. **Planifier** la correction avec une date et un responsable
5. **Publier** un inventaire des composants (SBOM)

### Vocabulaire minimal (à retenir)

| Mot | Signification simple |
|---|---|
| **CVE** | Identifiant d’une faille précise (ex. `CVE-2026-54283`) |
| **CWE** | Famille de faiblesse (ex. DoS = CWE-770, SSRF = CWE-918) |
| **CVSS** | Note de 0 à 10 : « à quel point c’est grave **en théorie** » |
| **EPSS** | Probabilité (0 à 1) qu’elle soit **exploitée sous 30 jours** |
| **KEV** | Catalogue CISA des failles **déjà exploitées** dans le monde réel |
| **SBOM** | Liste des « ingrédients » (libs) de ton logiciel |
| **SLA** | Délai maximum pour corriger |

**Règle d’or du cours** :
`Priorité ≠ CVSS seul`
`Priorité ≈ CVSS × EPSS × criticité métier (+ urgence si KEV)`

---

## Sources utilisées pour ce TP sur ton projet

| Source | Fichier / outil |
|---|---|
| Rapport de scan TP2 | `evidence/trivy-iot.json`, `evidence/trivy-alert.json`, `evidence/bandit.json` |
| Synthèse audit | `evidence/urbanhub-audit-report.md` |
| Grille de priorisation (livrable) | `evidence/tp3/grille-priorisation.csv` |
| Plan de remédiation (livrable) | `evidence/tp3/plan-remediation.md` |
| SBOM CycloneDX (livrable) | `evidence/tp3/sbom.json` (+ `sbom-iot.json`, `sbom-alert.json`) |

> Le cours parle de « ~30 CVE fictives ». Sur **ce** dépôt réel, Trivy a trouvé **2 CVE** (présentes dans 2 services = 4 findings SCA) + **4 findings Bandit**. On applique exactement la même méthode.

---

# Tâche 1 — Classifier par CVSS

## 1.1 Objectif (en français simple)

Pour chaque vulnérabilité, tu dois :

- lire le **score** (ex. 7.5)
- lire le **niveau** (HIGH, CRITICAL…)
- lire le **vecteur** (lettre par lettre)
- regrouper par **famille CWE**

## 1.2 Échelle CVSS (cours)

| Niveau | Score |
|---|---|
| CRITICAL | 9.0 – 10.0 |
| HIGH | 7.0 – 8.9 |
| MEDIUM | 4.0 – 6.9 |
| LOW | 0.1 – 3.9 |

## 1.3 Comment lire un vecteur CVSS

Exemple réel de ton projet (`CVE-2026-54283`) :

```text
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H
Score = 7.5 → HIGH
```

Traduction débutant :

| Abréviation | Valeur | Signification |
|---|---|---|
| AV:N | Network | Attaquable depuis le réseau / Internet |
| AC:L | Low | Facile à exploiter (peu de conditions) |
| PR:N | None | Pas besoin de compte |
| UI:N | None | Pas besoin que l’utilisateur clique |
| S:U | Unchanged | L’impact reste dans le composant |
| C:N | None | Pas d’impact confidentialité |
| I:N | None | Pas d’impact intégrité |
| A:H | High | Impact fort sur la **disponibilité** (DoS) |

**En une phrase** : un attaquant distant peut saturer / faire tomber le service sans compte.

Autre CVE du projet (`CVE-2026-48818`) :

```text
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N
Score = 7.5 → HIGH
CWE-918 (SSRF)
```

Ici c’est surtout la **confidentialité** (C:H) qui est touchée.

## 1.4 Classification des findings UrbanHub

| ID | Objet | CVSS | Sévérité | CWE | Famille |
|---|---|---|---|---|---|
| V-01 / V-02 | `starlette` CVE-2026-54283 | 7.5 | HIGH | CWE-770 | Limitation de ressources / DoS |
| V-03 / V-04 | `starlette` CVE-2026-48818 | 7.5 | HIGH | CWE-918 | SSRF |
| F-05 | `urlopen` Bandit B310 | ~5 (estimé) | MEDIUM | CWE-22 | Path / schéma non contrôlé |
| F-06 | `except/pass` Bandit B110 | ~2 | LOW | CWE-703 | Gestion d’erreur |
| F-07 / F-08 | `random` Bandit B311 | ~2 | LOW | CWE-330 | Aléa faible |

### Ce que tu dois écrire dans ton rendu (Tâche 1)

> « Les 2 CVE Starlette sont HIGH (7.5). Elles se regroupent en CWE-770 (DoS) et CWE-918 (SSRF). Les findings Bandit sont MEDIUM/LOW et hors CVSS NVD. »

---

# Tâche 2 — Enrichir avec EPSS & KEV

## 2.1 Pourquoi ce n’est pas suffisant de regarder CVSS

CVSS dit « **grave en théorie** ».
EPSS / KEV disent « **urgent en pratique** ».

Exemple du cours (Log4Shell) :

- CVSS 10.0
- EPSS très élevé
- **présent dans KEV** → priorité absolue

## 2.2 Comment vérifier EPSS (commande du cours)

```bash
curl -s "https://api.first.org/data/v1/epss?cve=CVE-2026-48818"
curl -s "https://api.first.org/data/v1/epss?cve=CVE-2026-54283"
```

### Résultats réels (consultés pour ce TP)

| CVE | EPSS | Percentile | Interprétation débutant |
|---|---|---|---|
| CVE-2026-54283 | **0.00397** (~0.4 %) | ~32 % | Probabilité d’exploitation **faible** aujourd’hui |
| CVE-2026-48818 | **0.00368** (~0.4 %) | ~29 % | Probabilité d’exploitation **faible** aujourd’hui |

## 2.3 Comment vérifier KEV (CISA)

Catalogue : [CISA Known Exploited Vulnerabilities](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)

| CVE | Sur KEV ? |
|---|---|
| CVE-2026-54283 | **NON** |
| CVE-2026-48818 | **NON** |
| CVE-2021-44228 (Log4Shell, exemple cours) | **OUI** (référence pédagogique) |

## 2.4 Que conclure pour UrbanHub ?

- Ce ne sont **pas** des urgences « KEV / EPSS explosif ».
- Ce **sont** quand même des HIGH sur des services **vie humaine**.
- Donc : on **patch rapidement**, mais on ne panique pas comme pour Log4Shell.

### Ce que tu dois écrire (Tâche 2)

> « Enrichissement effectué via FIRST EPSS + CISA KEV. EPSS < 0.01, hors KEV → pas d’urgence exploitation active connue. La priorité reste élevée à cause de la criticité métier (pas à cause d’EPSS). »

---

# Tâche 3 — Croiser avec la criticité métier UrbanHub

## 3.1 La matrice du cours (slide « criticité métier »)

| Composant UrbanHub | Criticité | Multiplicateur SLA |
|---|---|---|
| Capteur pollution eau (ingestion) | **VIE HUMAINE** | × 0.25 (beaucoup plus urgent) |
| Moteur d’alertes + notifications | **VIE HUMAINE** | × 0.25 |
| Dashboard agents | SERVICE ESSENTIEL | × 0.5 |
| Reporting mensuel interne | SUPPORT | × 2.0 (moins urgent) |

## 3.2 Mapping sur ton projet réel

| Service / fichier | Rôle métier | Criticité |
|---|---|---|
| `iot-service` | Ingestion mesures qualité de l’eau | **VIE HUMAINE** |
| `alert-service` | Détection / diffusion d’alertes pollution | **VIE HUMAINE** |
| `dashboard` | Consultation agents | SERVICE ESSENTIEL |
| simulateur `iot_service/simulator/*` | Génération locale de fausses mesures | SUPPORT |

## 3.3 Formule du délai réel (cours)

```text
Délai réel = SLA de base (selon sévérité) × multiplicateur métier
```

Exemple du cours :
CVE HIGH sur capteur eau = `7 jours × 0.25 ≈ 42 h` → on arrondit à **48 h**.

Tableau SLA de base (cours) pour HIGH :

| Zone | SLA HIGH |
|---|---|
| Agent / dashboard | ≤ 7 j |
| Ingestion capteur pollution eau | ≤ 3 j |
| Composant interne bureau | ≤ 14 j |

Sur UrbanHub, pour Starlette HIGH sur `iot-service` / `alert-service` :

```text
7 j × 0.25 = 1.75 j ≈ 48 h   (formule slide)
ou directement ≤ 3 j         (colonne « ingestion eau »)
```

On retient **48 h / 2 jours** comme SLA calculé (plus strict = mieux pour un RSSI).

### Ce que tu dois écrire (Tâche 3)

> « Même CVSS 7.5 n’a pas le même SLA partout. Sur ingestion eau et alertes (vie humaine), SLA = 48 h. Sur le simulateur (support), les LOW peuvent être acceptés. »

---

# Tâche 4 — Produire le plan de remédiation daté

## 4.1 Les 4 types d’action (cours)

| Action | Quand l’utiliser |
|---|---|
| **Patch / Upgrade** | Une version corrigée existe (cas Starlette) |
| **Mitigation** | Tu réduis le risque sans corriger tout de suite |
| **Workaround** | Contournement temporaire |
| **Accept** | Risque faible, justifié, documenté, daté |

## 4.2 Plan exécutable UrbanHub

Le plan détaillé est dans :

📄 **`evidence/tp3/plan-remediation.md`**

Résumé :

| Priorité | ID | Action | Owner | Échéance | Statut |
|---|---|---|---|---|---|
| P1 | V-01..V-04 | Upgrade `starlette` (≥ 1.3.1 via FastAPI) | Dev backend | J+2 | OUVERT |
| P2 | F-05 | Remplacer `urlopen` par `httpx` + allowlist | Dev IoT | J+7 | OUVERT |
| P3 | F-06 | Logger l’exception WebSocket | Dev Alert | J+14 | OUVERT |
| P4 | F-07 / F-08 | Accepter (simulateur) | Dev IoT | J+30 revue | ACCEPTÉ |

La grille complète (importable Excel / Sheets) :

📊 **`evidence/tp3/grille-priorisation.csv`**

### Colonnes exigées par le cours

`CVE · composant · action · propriétaire · SLA calculé · statut`
→ toutes présentes dans le CSV.

---

# Tâche 5 — Générer un SBOM CycloneDX

## 5.1 Qu’est-ce qu’un SBOM ? (débutant)

Un SBOM = la **liste des ingrédients** de ton application (comme l’étiquette d’un produit alimentaire).

Ça sert à :

- savoir **quelle lib** contient une CVE
- répondre vite : « est-ce qu’on a Log4j / Starlette vulnérable ? »
- prouver la transparence supply-chain

## 5.2 Commandes (celles du cours, adaptées au projet)

```bash
# SBOM global du dépôt
docker run --rm -v "$PWD:/src" aquasec/trivy \
  fs --format cyclonedx --output /src/evidence/tp3/sbom.json /src

# SBOM par service (recommandé)
docker run --rm -v "$PWD:/src" aquasec/trivy \
  fs --format cyclonedx --output /src/evidence/tp3/sbom-iot.json /src/iot-service

docker run --rm -v "$PWD:/src" aquasec/trivy \
  fs --format cyclonedx --output /src/evidence/tp3/sbom-alert.json /src/alert-service
```

## 5.3 Vérifier que les libs vulnérables sont dans le SBOM

```bash
# Chercher starlette dans le SBOM
python3 -c "
import json
d=json.load(open('evidence/tp3/sbom.json'))
for c in d.get('components', []):
    if 'starlette' in (c.get('name') or '').lower():
        print(c.get('name'), c.get('version'))
"
```

### Résultat obtenu sur ce projet

| Fichier | Format | Version spec | Composants | `starlette` trouvé |
|---|---|---|---|---|
| `evidence/tp3/sbom.json` | CycloneDX | 1.7 | 97 | **oui** (`1.0.0`) |
| `evidence/tp3/sbom-iot.json` | CycloneDX | 1.7 | 19 | **oui** (`1.0.0`) |
| `evidence/tp3/sbom-alert.json` | CycloneDX | 1.7 | 28 | **oui** (`1.0.0`) |

✅ Cohérence validée : les CVE Trivy portent sur `starlette@1.0.0`, et le SBOM liste bien `starlette 1.0.0`.

### Optionnel (commandes du cours)

```bash
# EPSS
curl -s "https://api.first.org/data/v1/epss?cve=CVE-2026-54283"

# Si tu as une image Docker buildée :
# docker run --rm anchore/syft urbanhub/iot-service:local -o cyclonedx-json > evidence/tp3/sbom-image.json
# grype sbom:evidence/tp3/sbom.json | grep CVE-2026
```

---

## Livrables TP 3 — checklist de rendu

| Livrable exigé | Fichier dans ce repo | Statut |
|---|---|---|
| Grille de priorisation (Excel/Sheets) | `evidence/tp3/grille-priorisation.csv` | ✅ |
| Plan de remédiation daté | `evidence/tp3/plan-remediation.md` | ✅ |
| SBOM CycloneDX | `evidence/tp3/sbom.json` | ✅ |
| Guide pédagogique (ce fichier) | `docs/tp/TP3-gestion-vulnerabilites-UrbanHub.md` | ✅ |

### Grille d’évaluation du cours (rappel)

| Critère | Points |
|---|---|
| Justesse classification CVSS + CWE | 4 |
| Enrichissement EPSS/KEV effectif | 3 |
| Croisement criticité métier UrbanHub | 4 |
| Plan de remédiation exécutable | 5 |
| SBOM CycloneDX correct + cohérent | 3 |
| Clarté & forme | 1 |
| **Total** | **/20** |

---

## Mini-FAQ débutant

**Q : Pourquoi 4 findings SCA pour seulement 2 CVE ?**
Parce que la même CVE apparaît dans `iot-service` **et** `alert-service`. On compte par *occurrence métier*.

**Q : Pourquoi patcher si EPSS est bas ?**
Parce que la criticité métier est « vie humaine ». Un DoS sur les alertes eau reste inacceptable même si l’exploit n’est pas encore populaire.

**Q : Pourquoi accepter F-07 / F-08 ?**
Parce que `random` est utilisé pour **simuler** des capteurs, pas pour générer des tokens / mots de passe. L’acceptation doit être **écrite** (sinon ce n’est pas une décision, c’est de l’oubli).

**Q : SBOM 1.7 au lieu de 1.5+ ?**
Le cours demande CycloneDX **v1.5+**. La 1.7 est plus récente → **conforme**.

---

## Enchaînement vers le TP 4

Une fois le triage fait, le TP 4 automatise la protection dans le **pipeline CI/CD** :

- empêcher un secret de passer
- échouer si CVE CRITICAL
- scanner l’image Docker
- signer + publier un SBOM à chaque build

👉 Continuer avec : [`TP4-pipeline-DevSecOps-UrbanHub.md`](./TP4-pipeline-DevSecOps-UrbanHub.md)
