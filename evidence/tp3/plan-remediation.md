# Plan de remédiation daté — UrbanHub (TP 3)

**Date du plan** : 2026-07-28
**Périmètre** : `iot-service`, `alert-service`
**Sources** : Trivy fs + Bandit (TP2) + enrichissement EPSS/KEV (TP3)
**Validé pour** : RSSI / Direction IT (exercice pédagogique)

---

## 1. Synthèse exécutive (1 minute de lecture)

| Indicateur | Valeur |
|---|---|
| CVE confirmées | 2 (`CVE-2026-54283`, `CVE-2026-48818`) |
| Occurrences SCA | 4 (2 services × 2 CVE) |
| Findings SAST | 4 (Bandit) |
| Secrets confirmés | 0 |
| Présence CISA KEV | Non |
| EPSS max observé | ~0.004 (faible) |
| Priorité #1 | Upgrade `starlette` ≥ 1.3.1 sous **48 h** |

**Décision RSSI** : traiter d’abord les CVE Starlette sur les services **vie humaine** (ingestion eau + alertes), malgré un EPSS bas.

---

## 2. Hypothèses de calendrier

| Jalon | Date |
|---|---|
| J0 — Découverte / triage | 2026-07-28 |
| J+2 — Patch Starlette mergé + re-scan vert | 2026-07-30 |
| J+7 — Mitigation `urlopen` | 2026-08-04 |
| J+14 — Fix logs WebSocket | 2026-08-11 |
| J+30 — Revue acceptations simulateur | 2026-08-27 |

---

## 3. Plan détaillé

### P1 — Upgrade Starlette (bloquant métier)

| Champ | Contenu |
|---|---|
| IDs | V-01, V-02, V-03, V-04 |
| CVE | `CVE-2026-54283` (DoS, CWE-770) + `CVE-2026-48818` (SSRF, CWE-918) |
| Composant | `starlette@1.0.0` (via FastAPI) |
| Services | `iot-service`, `alert-service` |
| Action | **PATCH / UPGRADE** |
| Fix minimal | `starlette>=1.3.1` (couvre les deux CVE ; 1.1.0 ne suffit que pour CVE-2026-48818) |
| Comment faire | Mettre à jour les dépendances (`uv lock` / bump FastAPI si besoin), puis `uv sync` |
| Preuve de fermeture | Re-scan Trivy fs sans ces CVE + SBOM montrant `starlette>=1.3.1` |
| Propriétaire | Dev backend (IoT + Alert) |
| SLA calculé | **48 h** (HIGH × criticité VIE HUMAINE × 0.25) |
| Échéance | **2026-07-30** |
| Statut | OUVERT |
| Mitigation temporaire | Limiter la taille des body HTTP côté reverse proxy (Nginx/Traefik) |

Commandes de vérification après patch :

```bash
docker run --rm -v "$PWD:/src" aquasec/trivy fs \
  --severity HIGH,CRITICAL --scanners vuln \
  /src/iot-service /src/alert-service
```

---

### P2 — Encadrer l’appel HTTP Hub’Eau

| Champ | Contenu |
|---|---|
| ID | F-05 |
| Finding | Bandit B310 — `urllib.request.urlopen` |
| Fichier | `iot-service/src/iot_service/hubeau_qualite_client.py` |
| Action | **MITIGATION** puis **PATCH** |
| Détail | Remplacer par `httpx` ; forcer schéma `https` ; allowlist host `hubeau.eaufrance.fr` ; timeout strict |
| Propriétaire | Dev backend IoT |
| SLA | ~7 j (MEDIUM × vie humaine) |
| Échéance | **2026-08-04** |
| Statut | OUVERT |

---

### P3 — Ne plus masquer les erreurs WebSocket

| Champ | Contenu |
|---|---|
| ID | F-06 |
| Finding | Bandit B110 — `except Exception: pass` |
| Fichier | `alert-service/src/alert_service/websocket.py` |
| Action | **PATCH** |
| Détail | Remplacer `pass` par `logger.debug(...)` / `logger.warning(...)` avec l’exception |
| Propriétaire | Dev backend Alert |
| SLA | ~14–22 j |
| Échéance | **2026-08-11** |
| Statut | OUVERT |

---

### P4 — Acceptation formalisée (simulateur)

| Champ | Contenu |
|---|---|
| IDs | F-07, F-08 |
| Finding | Bandit B311 — `random` non cryptographique |
| Fichiers | `simulator/generator.py`, `simulator/orchestrator.py` |
| Action | **ACCEPT** |
| Justification | Code de simulation locale uniquement ; pas de tokens, pas d’auth, pas de crypto |
| Condition | Si ce code est réutilisé pour de la sécurité → passer à `secrets` |
| Propriétaire | Dev backend IoT |
| Revue | **2026-08-27** |
| Statut | ACCEPTÉ (documenté) |

---

## 4. Matrice de suivi (vue tableau)

| ID | Action | Owner | Échéance | Statut |
|---|---|---|---|---|
| V-01 | Upgrade starlette (iot) | Dev IoT | 2026-07-30 | OUVERT |
| V-02 | Upgrade starlette (alert) | Dev Alert | 2026-07-30 | OUVERT |
| V-03 | Upgrade starlette SSRF (iot) | Dev IoT | 2026-07-30 | OUVERT |
| V-04 | Upgrade starlette SSRF (alert) | Dev Alert | 2026-07-30 | OUVERT |
| F-05 | httpx + allowlist | Dev IoT | 2026-08-04 | OUVERT |
| F-06 | logger WebSocket | Dev Alert | 2026-08-11 | OUVERT |
| F-07 | Accept simulateur | Dev IoT | 2026-08-27 | ACCEPTÉ |
| F-08 | Accept jitter | Dev IoT | 2026-08-27 | ACCEPTÉ |

---

## 5. Règle de fermeture (anti-pattern du cours)

> On **ne ferme pas** un ticket parce que quelqu’un a coché « done ».
> On ferme uniquement si un **re-scan** ne trouve plus la CVE / le finding.

Preuves attendues dans `evidence/` :

1. Nouveau rapport Trivy sans CVE Starlette
2. SBOM mis à jour (`starlette` version corrigée)
3. (Optionnel) sortie Bandit sans B310/B110 si corrigés

---

## 6. Lien avec le pipeline (TP 4)

Pour empêcher la régression :

- gate CI : **fail** si Trivy trouve CRITICAL (et idéalement HIGH non excepté)
- gate secrets : **fail** si Gitleaks trouve un secret
- publier le SBOM à chaque build

Voir le guide TP 4 : `docs/tp/TP4-pipeline-DevSecOps-UrbanHub.md`
