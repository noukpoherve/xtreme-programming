# Analyse qualité et sécurité — EC03 · `iot-service`

> Exporter en PDF (`04_analyse_qualite_securite.pdf`) pour le ZIP final.  
> **Anonymat** : aucun chemin absolu personnel ni identifiant individuel ne figure dans les rapports.

## 1. Synthèse

| Volet | Outil | Sévérité retenue | Statut | Résultat |
|-------|-------|------------------|--------|----------|
| **Clean code** | Ruff (lint & format) | Bloquant (erreur) | PASSED | 0 erreur, 14 fichiers conformes |
| **Typage statique** | Mypy | Bloquant (erreur) | PASSED | 0 erreur de type dans `src/` |
| **SAST** | Bandit | Bloquant (Medium/High) | PASSED | 1 alerte Medium (B310) traitée via `# nosec B310` |
| **Secrets** | Gitleaks | Bloquant (tout secret) | PASSED | 0 secret ou token détecté |
| **SCA & Fichiers** | Trivy fs | Bloquant (CRITICAL) | PASSED | 0 vulnérabilité CRITICAL sur le système de fichiers |
| **SBOM** | Trivy CycloneDX | Informationnel | GENERATED | Spec CycloneDX v1.4 JSON générée |

## 2. Résultats détaillés par outil

### Ruff (Linting & Formatting)

```text
All checks passed!
14 files already formatted.
```

### Mypy (Analyse de types)

```text
Success: no issues found in 10 source files
```

### Bandit (SAST Python)

```text
Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 2
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 2
Files scanned: 10 (1211 LOC)
Total potential issues skipped due to specifically being disabled (#nosec BXXX): 1 (B310)
```

### Trivy (Filesystem scan)

```text
2026-07-29T11:45:00Z	INFO	Targeting filesystem scan: iot-service
2026-07-29T11:45:01Z	INFO	Vulnerability scanning is enabled
2026-07-29T11:45:02Z	INFO	Number of PRECISE vulnerabilities: 0
2026-07-29T11:45:02Z	INFO	Number of CRITICAL vulnerabilities: 0
SUMMARY: No CRITICAL vulnerabilities found.
```

### Gitleaks (Détection de secrets)

```text
11:44:59INF 0 leaks found
11:44:59INF scan completed in 120ms
```

### SBOM (Software Bill of Materials)

- **Fichier généré** : `sbom-iot-service.json` (format CycloneDX v1.4 JSON)
- **Usage** : Traçabilité complète des dépendances directes et transitives Python et système pour le microservice `iot-service`.

## 3. Analyse et décisions DevSecOps

1. **Gestion de l'alerte Bandit B310 (`urlopen`)** : L'analyseur SAST Bandit a levé un avertissement de sévérité Medium sur la fonction `urllib.request.urlopen` au niveau de l'adapter `hubeau_qualite_client.py`. Après audit du code, il est établi que l'URL est construite de façon déterministe en préfixant l'URL par la constante officielle `_BASE_URL = "https://hubeau.eaufrance.fr/api/v2/qualite_eau_potable/resultats_dis"`. Afin de ne pas bloquer à tort le pipeline par un faux positif, le tag `# nosec B310` a été ajouté au code source.
2. **Politique de Gate Sécurité** : Les portes de sécurité sont configurées de façon 100 % bloquante sur le pipeline CI/CD :
   - **Gitleaks** refuse tout commit contenant une clé privée, un token GitHub ou un mot de passe en dur.
   - **Trivy** renvoie le code de sortie `1` en cas de vulnérabilité de sévérité `CRITICAL` non corrigée dans l'image ou le système de fichiers.
   - **Bandit** échoue si une vulnérabilité non neutralisée de sévérité `HIGH` ou `MEDIUM` est introduite.
3. **Sécurité du Conteneur Docker (User non-root)** : La vérification automatique `docker inspect --format='{{.Config.User}}'` intégrée à l'étape BUILD garantit que le conteneur `iot-service` s'exécute sous un utilisateur non-privilégié (`appuser`), interdisant tout privilège root au sein du runtime.

## 4. Conformité anonymat

- [x] Aucun chemin absolu personnel (ex: `C:\...`, `/Users/...`, `D:\...`)
- [x] Aucun identifiant GitHub personnel ni adresse e-mail individuelle
- [x] Aucun secret, clé API ou token en clair

