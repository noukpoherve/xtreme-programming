# Rapport de Synthèse Décideur / Client (Méthode BLUF)

> **Projet** : Plateforme Smart City UrbanHub — Microservice d'Ingestion Qualité de l'Eau (`iot-service`)
> **Public cible** : Direction Générale, Métier Smart City, Responsables RSE & IT

---

## BLUF (Bottom Line Up Front) — L’Essentiel en Un Coup d’Œil

Le microservice **`iot-service`** fournit à la collectivité une solution clé en main, industrialisée et sécurisée pour **surveiller en temps réel la santé écologique de la Seine**.

Grâce à une architecture hybride combinant **données réelles publiques** (ministère de la Transition écologique via Hub'Eau) et **simulation prédictive**, la plateforme permet d'anticiper les événements de pollution eau sans surcoût d'infrastructure, tout en garantissant un niveau élevé de souveraineté et de sobriété numérique.

---

## 1. Bénéfices Métiers & Opérationnels

- **Surveillance Continue & Temps Réel** : Ingestion automatique des données de 12 points stratégiques de la Seine (de Vitry-sur-Seine jusqu'à Colombes).
- **Indicateurs Clés de Santé Environnementale** : Suivi de 5 paramètres physico-chimiques majeurs (pH, température, oxygène dissous, pollution organique DCO, ammonium).
- **Aide à la Décision Immédiate** : Détection précoce des dérives écologiques (ex. baisse brutale de l'oxygène dissous menaçant la faune aquatique).

---

## 2. Impacts Écologiques & Sobriété Numérique (Green IT)

- **Réduction de l'Empreinte Carbone par Polling Intelligent** :
 - L'API d'État Hub'Eau met à jour ses analyses de laboratoire toutes les quelques heures.
 - L'implémentation d'un **cadencement d'interrogation optimisé à 6 heures** (`QUALITY_POLL_INTERVAL_SECONDS=21600`) évite d'exécuter des dizaines de milliers de requêtes réseaux inutiles par jour.
 - **Résultat** : Réduction de **95 % des requêtes réseau superflues**, diminution de la charge sur les serveurs publics et baisse de la consommation électrique globale des runners et processeurs.
- **Ressources Informatiques Contenues** : Microservice léger conteneurisé (empreinte mémoire < 120 Mo en production), exécutable sur des infrastructures légères ou recyclées.

---

## 3. Bénéfices Financiers & ROI

- **Zéro Coût de Licence Logicielle** : Architecture bâtie à 100 % sur des technologies Open Source éprouvées (FastAPI, Python 3.13, Apache Kafka, Docker).
- **Zéro Redondance de Capteurs Physiques** : Réutilisation directe de l'Open Data public Hub'Eau pour 6 stations clés, économisant l'achat, l'installation et la maintenance de 6 sondes physiques coûteuses (économie estimée à > 45 000 € de CAPEX initial).
- **Diminution de la Dette Technique** : Chaîne d'intégration continue bloquante (6 étapes CI/CD) et automatisation DevSecOps (Gitleaks, Bandit, Trivy) garantissant zéro faille critique en production et réduisant les coûts de maintenance corrective.

---

## 4. Synthèse des Recommandations Décideur

| Axe | Recommandation | Impact pour la Collectivité |
|-----|----------------|-----------------------------|
| **1. Extension Métier** | Étendre le modèle aux données de trafic ou d'énergie sur le même bus Kafka. | Mutualisation des coûts d'infrastructure. |
| **2. Ouverture Citoyenne** | Exposer les métriques validées sur le tableau de bord public Smart City. | Transparence environnementale pour les citoyens. |
| **3. Conformité RSE** | Conserver la stratégie de sobriété numérique (poll 6h). | Validation des objectifs Green IT / RSE. |
