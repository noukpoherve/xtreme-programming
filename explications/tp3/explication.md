# TP 3 — Gestion des vulnérabilités UrbanHub (+ SBOM)

> **Objectif du cours** : ne plus traiter les CVE « dans le désordre ». Trier, prioriser, planifier, inventaire.
> **Livrables** : grille de priorisation · plan daté · SBOM CycloneDX.

---

## 1. Quels problèmes essayons-nous de résoudre ?

Avoir des findings (TP2) ne suffit pas. Les problèmes du TP3 :

| # | Problème | Exemple |
|---|---|---|
| P1 | On confond **sévérité** et **priorité** | CVSS 9.0 théorique traité avant un HIGH sur les alertes eau |
| P2 | On ignore l’**exploitabilité réelle** | Pas de regard EPSS / catalogue KEV |
| P3 | On ignore la **criticité métier** | Même SLA pour le simulateur et l’ingestion eau |
| P4 | Pas de **plan daté** avec responsables | « Il faudrait patcher » sans échéance |
| P5 | Pas d’**inventaire** des composants (SBOM) | Impossible de répondre « avons-nous starlette 1.0.0 ? » |

En une phrase :
**« Parmi les vulnérabilités UrbanHub, lesquelles corriger en premier, pour quand, et avec quelle preuve d’inventaire ? »**

---

## 2. Pourquoi les résoudre ?

| Pourquoi | Explication débutant |
|---|---|
| **Temps limité** | On ne peut pas tout patcher le même jour |
| **Vie humaine** | Une CVE HIGH sur `alert-service` > une LOW sur le simulateur |
| **Preuve RSSI** | Un plan daté + owner = décision auditable |
| **Supply-chain** | Le SBOM permet de réagir vite quand une nouvelle CVE sort |
| **Éviter l’anti-pattern** | Trier au CVSS seul (explicitement condamné par le cours) |

Formule moderne du cours :

```text
Priorité ≈ CVSS × EPSS × criticité métier  (+ urgence si KEV)
SLA réel = SLA de base × multiplicateur métier
```

---

## 3. Comment on s’y prend pour les résoudre ?

### Étape 1 — Classifier par CVSS (+ CWE)

Lire score, niveau, vecteur, famille CWE.

Sur UrbanHub :

| CVE | Score | Niveau | CWE | Sens |
|---|---|---|---|---|
| CVE-2026-54283 | 7.5 | HIGH | CWE-770 | DoS (disponibilité) |
| CVE-2026-48818 | 7.5 | HIGH | CWE-918 | SSRF (confidentialité) |

### Étape 2 — Enrichir avec EPSS & KEV

```bash
curl -s "https://api.first.org/data/v1/epss?cve=CVE-2026-54283"
curl -s "https://api.first.org/data/v1/epss?cve=CVE-2026-48818"
```

Résultats retenus pour ce TP :

| CVE | EPSS | Sur CISA KEV ? |
|---|---|---|
| CVE-2026-54283 | ~0.004 (faible) | Non |
| CVE-2026-48818 | ~0.004 (faible) | Non |

→ Pas d’urgence « exploitation active mondiale », mais **priorité métier haute** quand même.

### Étape 3 — Croiser criticité métier UrbanHub

| Composant | Criticité | Multiplicateur SLA |
|---|---|---|
| `iot-service` (eau) | VIE HUMAINE | × 0.25 |
| `alert-service` | VIE HUMAINE | × 0.25 |
| simulateur | SUPPORT | × 2.0 |

Exemple : HIGH × 0.25 → **≈ 48 h** (pas 7 jours).

### Étape 4 — Plan de remédiation daté

Actions possibles : **patch / mitigation / workaround / accept**.

Livrable : `evidence/tp3/plan-remediation.md`
Grille : `evidence/tp3/grille-priorisation.csv`

### Étape 5 — Générer un SBOM CycloneDX

```bash
docker run --rm -v "$PWD:/src" aquasec/trivy \
  fs --format cyclonedx --output /src/evidence/tp3/sbom.json /src

docker run --rm -v "$PWD:/src" aquasec/trivy \
  fs --format cyclonedx --output /src/evidence/tp3/sbom-iot.json /src/iot-service

docker run --rm -v "$PWD:/src" aquasec/trivy \
  fs --format cyclonedx --output /src/evidence/tp3/sbom-alert.json /src/alert-service
```

Vérifier que `starlette 1.0.0` apparaît bien dans le SBOM (cohérence avec Trivy).

---

## 4. Comment le tester ?

### Tests de fond (méthode)

| Test | Comment | OK si… |
|---|---|---|
| CVSS lu correctement | Comparer au rapport Trivy | 7.5 HIGH, vecteurs notés |
| EPSS consulté | Refaire le `curl` FIRST | Scores présents dans la grille |
| KEV vérifié | Chercher la CVE sur le catalogue CISA | « Non » documenté (pas inventé) |
| Métier appliqué | Relire la grille | SLA eau/alertes << SLA simulateur |
| Plan exécutable | Chaque ligne a owner + date + action | Oui |
| SBOM cohérent | Chercher `starlette` dans `sbom*.json` | Version = celle du finding |

### Test technique SBOM (commande)

```bash
python3 -c "
import json
d=json.load(open('evidence/tp3/sbom.json'))
print('format', d.get('bomFormat'), d.get('specVersion'))
for c in d.get('components', []):
    if 'starlette' in (c.get('name') or '').lower():
        print('FOUND', c['name'], c.get('version'))
"
```

OK si : `CycloneDX` + `starlette 1.0.0`.

### Test de non-régression après patch (plus tard)

Quand Starlette sera upgradé :

```bash
docker run --rm -v "$PWD:/src" aquasec/trivy fs \
  --severity HIGH,CRITICAL --scanners vuln /src/iot-service /src/alert-service
```

OK si : les CVE V-01..V-04 **disparaissent**.
(Le cours interdit de fermer un ticket sans re-scan.)

### Mini auto-test

1. CVSS dit quoi / ne dit pas quoi ? → gravité théorique / pas la priorité métier
2. KEV présent = ? → urgence maximale
3. Pourquoi accepter F-07/F-08 ? → simulateur, pas crypto
4. À quoi sert le SBOM ? → inventaire pour réagir aux nouvelles CVE

### Preuve de rendu

- `evidence/tp3/grille-priorisation.csv`
- `evidence/tp3/plan-remediation.md`
- `evidence/tp3/sbom.json` (+ sbom par service)

---

## Lien avec la suite

Le TP3 décide **humainement**.
Le TP4 **automatise** : fail CI si secret / CVE CRITICAL, SBOM à chaque build, signature d’image.
