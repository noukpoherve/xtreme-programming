# Travaux pratiques DevSecOps — UrbanHub

## Explications pédagogiques (structure fixe)

Pour **chaque TP 1 → 4**, lire d’abord :

📁 [`explications/`](../../explications/README.md)

Chaque fichier répond toujours à :

1. Quels problèmes essayons-nous de résoudre ?
2. Pourquoi les résoudre ?
3. Comment on s’y prend ?
4. Comment le tester ?

## Guides techniques longs (TP3 / TP4)

| TP | Thème | Guide | Livrables |
|---|---|---|---|
| **TP 3** | Gestion des vulnérabilités (CVSS, EPSS, KEV, SBOM) | [TP3-gestion-vulnerabilites-UrbanHub.md](./TP3-gestion-vulnerabilites-UrbanHub.md) | `evidence/tp3/` |
| **TP 4** | Pipeline CI/CD DevSecOps (6 gates) | [TP4-pipeline-DevSecOps-UrbanHub.md](./TP4-pipeline-DevSecOps-UrbanHub.md) | `evidence/tp4/` + `.github/workflows/devsecops.yml` |

## Ordre recommandé

1. `explications/tp1` → threat modeling
2. `explications/tp2` + `evidence/urbanhub-audit-report.md`
3. `explications/tp3` + `evidence/tp3/`
4. `explications/tp4` + pipeline CI

## Rappel cours

- **TP 1** = comprendre les risques
- **TP 2** = détecter avec des outils
- **TP 3** = prioriser et planifier (cerveau)
- **TP 4** = automatiser les gates (pipeline)
