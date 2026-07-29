# UrbanHub — Microservice `iot-service` (Documentation Doc-as-Code)

> **Documentation Technique & d'Exploitation** (Épreuve certifiante **EC03 — Partie 2**, Compétence **C20** du référentiel EADL / RNCP 39765).

---

## Présentation Générale

Ce dépôt contient la documentation technique versionnée (**Doc-as-Code**) pour le microservice **`iot-service`** de la plateforme Smart City **UrbanHub**.

Le microservice `iot-service` assure l'ingestion, la validation et la publication en temps réel des mesures de **qualité de l'eau de la Seine** provenant de deux sources distinctes :
1. ** API Officielle Hub'Eau (v2 qualite_rivieres)** : Ingestion réelle auprès de 6 stations physiques le long de la Seine (pH, température, oxygène dissous, DCO, ammonium).
2. ** Simulateur Local Intégré** : Génération autonome de séries temporelles simulées pour 6 capteurs virtuels (cycle diurne, marche aléatoire, événements de pollution injectables).

Les événements validés sont publiés sur le bus de messages **Apache Kafka** (topic `mesure.qualite.eau`) pour alimenter le moteur de détection d'anomalies (`alert-service`) et le tableau de bord temps réel (`dashboard`).

---

## Organisation Diátaxis

Cette documentation s'appuie strictement sur le framework **Diátaxis** afin d'offrir une structure claire, reproductible et adaptée aux besoins de chaque profil de lecteur :

```text
EC03_P2_NomPrenom_UrbanHub_Documentation/
├── mkdocs.yml ← Configuration du portail MkDocs Material
├── README.md ← Ce document (Présentation + Section IA)
└── docs/
 ├── index.md ← Accueil du portail & Vue d'ensemble
 ├── tutorial.md ← 1. TUTORIEL : Prise en main pas-à-pas (débutant)
 ├── how-to-guides.md ← 2. GUIDES PRATIQUES : Déploiement Docker & Exploitation
 ├── reference.md ← 3. RÉFÉRENCE : Spécifications API REST, Pydantic v2 & Env Vars
 ├── explanation.md ← 4. EXPLICATION : Architecture SOLID, DDD & Diagrammes Mermaid.js
 ├── security-and-cicd.md ← Pipeline CI/CD 6 étapes & Résultats DevSecOps
 ├── troubleshooting.md ← Guide de dépannage & Matrice des 5 incidents courants
 ├── maintenance-changelog.md ← Guide de maintenance & Changelog Conventional Commits
 └── client-summary.md ← Synthèse BLUF Décideur / Impacts écologiques & financiers
```

---

## Consultation & Navigation

- **Portail web interactif** : Généré via **MkDocs Material** avec recherche full-text, thème clair/sombre et diagrammes Mermaid.js.
- **Publication multi-versions** : Support de la stratégie `mike` pour le suivi des versions sur GitHub Pages.
- **Rapport compilé unique** : Document PDF rassembleur `EC03P2Documentation.pdf` joint à l'archive pour la correction.

---

## Section IA (Déclaration Obligatoire)

### 1. Outils IA et Plateformes Utilisées

| Outil | Plateforme / Modèle | Usage principal |
|-------|---------------------|-----------------|
| **Antigravity AI** | Agent Coding (Google DeepMind) | Rapprochement code/doc, génération des diagrammes Mermaid.js, rédaction des guides Diátaxis et du rapport BLUF |
| **Cursor** | IDE Agent Composer | Structuration initiale de l'arborescence Markdown et des fichiers `mkdocs.yml` |
| **ChatGPT / Claude** | Web / LLM | Relecture syntaxique des schémas Pydantic v2, validation des règles de conformité EC03 |

### 2. Périmètre d'Utilisation

L'Intelligence Artificielle a été mobilisée pour :
- La structuration du site MkDocs Material et des 9 pages Markdown selon le cadre **Diátaxis**.
- La modélisation visuelle d'architecture via des diagrammes **UML Mermaid.js** (diagramme de classes du domaine `iot-service` et diagramme de séquence de flux Kafka).
- La rédaction du guide de dépannage (matrice des 5 incidents courants).
- La mise en forme du rapport de synthèse **BLUF** pour le décideur/client (analyse des bénéfices métiers, financiers et de sobriété numérique/écologique).

### 3. Prompts Majeurs Formulés

1. *« Générer un diagramme de classes UML Mermaid.js valide représentant l'architecture du microservice iot-service (HubEauQualiteClient, QualityPoller, SensorOrchestrator, Pydantic v2 schemas). »*
2. *« Rédiger une matrice de troubleshooting de 5 incidents courants pour iot-service avec causes racines et procédures de résolution pas-à-pas. »*
3. *« Formuler un rapport de synthèse BLUF (Bottom Line Up Front) destiné aux décideurs métiers, mettant en avant les bénéfices financiers et l'impact écologique de l'optimisation des requêtes API Hub'Eau (cadence 6h). »*
4. *« Vérifier l'anonymat strict de tous les fichiers Markdown de documentation (suppression des noms, e-mails, identifiants Git et chemins absolus locaux). »*

### 4. Audit Critique & Justification Anti-Hallucination

- **Architecture & Diagrammes Mermaid.js** : Chaque diagramme Mermaid.js généré par l'IA a été vérifié manuellement contre le code source réel (`iot_service/hubeau_qualite_client.py`, `quality_poller.py`, `simulator/orchestrator.py`) pour garantir la correspondance exacte des méthodes, types de retour et flux d'événements Kafka.
- **Sécurité DevSecOps** : Les explications relatives aux outils SAST (Bandit), SCA (Trivy), Secrets (Gitleaks) et SBOM (CycloneDX) s'appuient strictement sur les logs réels d'exécution du pipeline CI/CD (`01_pipeline.yml`).
- **Anonymisation** : L'IA a parfois tendance à laisser des exemples de chemins locaux (`C:\Users\...`). Un scan de validation par expressions régulières a été effectué pour forcer l'usage exclusif de chemins relatifs.
- **Cadence d'ingestion** : L'IA proposait initialement un poll Hub'Eau toutes les 5 minutes. Après vérification métier du fonctionnement de l'API Hub'Eau (analyses de laboratoire espacées de plusieurs heures), la fréquence a été fixée à 6 heures (`QUALITY_POLL_INTERVAL_SECONDS=21600`), réduisant considérablement la charge réseau et l'empreinte carbone.

---

## Conformité et Anonymat Strict

- **Nom / Prénom** : Aucun nom individuel ne figure dans les documents source de cette archive.
- **E-mails & Git IDs** : Aucune donnée d'identification personnelle.
- **Chemins** : 100 % de chemins d'accès relatifs.
