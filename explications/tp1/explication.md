# TP 1 — Threat Modeling UrbanHub (STRIDE)

> **Objectif du cours** : avant d’écrire des scans ou un pipeline, comprendre **où** UrbanHub peut être attaqué.
> **Livrables attendus** : DFD niveau 1 · tableau STRIDE · Top 5 risques + contre-mesures.

---

## 1. Quels problèmes essayons-nous de résoudre ?

Sans threat modeling, on sécurise « au hasard ». Les problèmes concrets à résoudre ici :

| # | Problème | Exemple UrbanHub |
|---|---|---|
| P1 | On ne voit pas clairement **qui parle à qui** | Capteur → Kafka → API → Postgres → alertes → dashboard |
| P2 | On ignore les **frontières de confiance** | Capteur terrain (non fiable) vs réseau interne ville |
| P3 | On oublie des familles de menaces | On pense XSS, on oublie le DoS Kafka ou le spoofing capteur |
| P4 | On ne sait pas **quoi traiter en premier** | 30 menaces listées, 0 priorisation vie humaine |
| P5 | La direction SI ne peut pas valider l’archi | Pas de preuve rationnelle avant pré-prod |

En une phrase :
**« Avant de lancer UrbanHub, quels sont les 5 risques sécurité les plus graves sur cette architecture smart-city ? »**

---

## 2. Pourquoi les résoudre ?

| Pourquoi | Explication débutant |
|---|---|
| **Coût** | Une faille trouvée en conception coûte beaucoup moins cher qu’en production |
| **Vie humaine** | Une fausse mesure d’eau / une alerte manquée peut cacher une contamination |
| **Périmètre** | UrbanHub a plusieurs surfaces : IoT, broker, API, DB, dashboard |
| **Décision** | Le DSI doit **valider ou refuser** la pré-prod sur des faits, pas sur l’intuition |
| **Base des TP suivants** | TP2/TP3/TP4 outillent ce que le TP1 a identifié comme critique |

Sans TP1, le TP2 scanne « tout », et le TP4 met des gates sans savoir **pourquoi** elles existent.

---

## 3. Comment on s’y prend pour les résoudre ?

Le cours impose **4 étapes**.

### Étape A — Cartographier les flux (DFD)

Dessiner un **Data Flow Diagram** niveau 1 avec :

- **Sources externes** : capteurs eau, agents municipaux, (optionnel Hub’Eau)
- **Processus** : `iot-service`, `alert-service`, dashboard
- **Stockages** : Postgres/Timescale, topics Kafka
- **Frontières de confiance** : Internet / terrain IoT / réseau interne

Sur ce projet réel, les boîtes correspondent à :

```text
[Capteurs / Hub'Eau] --> [iot-service:8001] --> [Kafka]
                                                    |
                                                    v
                                            [alert-service:8000]
                                               |         |
                                               v         v
                                          [Postgres]  [Dashboard]
```

Outils : papier, draw.io, Excalidraw.

### Étape B — Appliquer STRIDE

Pour **chaque composant**, lister des menaces dans les 6 familles :

| Lettre | Famille | Question simple |
|---|---|---|
| **S** | Spoofing | Quelqu’un peut-il se faire passer pour un capteur / un agent ? |
| **T** | Tampering | Peut-on modifier une mesure d’eau en transit ? |
| **R** | Repudiation | Peut-on nier avoir envoyé / reçu une alerte ? |
| **I** | Information disclosure | Fuite de données / tokens / configs ? |
| **D** | Denial of Service | Peut-on faire tomber Kafka / l’API d’alertes ? |
| **E** | Elevation of privilege | Un user dashboard peut-il devenir admin / accéder à la DB ? |

Exemple (1 ligne de tableau) :

| Composant | Famille | Menace |
|---|---|---|
| Capteur → iot-service | Spoofing | Envoi de fausses mesures avec un faux device_id |
| Kafka | Tampering | Message altéré si pas d’auth / pas de TLS |
| alert-service | DoS | Flood HTTP → alertes pollution stoppées |
| Dashboard | Info disclosure | Endpoint API sans auth expose l’historique |

### Étape C — Coter Vraisemblance × Impact (1–5)

```text
Score = Vraisemblance × Impact
```

Justifier avec la **criticité métier** :

- pollution eau / alertes → **vie humaine** (impact 5)
- reporting mensuel → support (impact plus bas)

### Étape D — Formuler le Top 5

Pour chaque risque du Top 5 :

- contre-mesure
- propriétaire (Dev / Ops / Sec)
- délai proposé

Exemple de Top 5 plausible UrbanHub :

1. Spoofing / tampering des mesures eau
2. DoS sur `alert-service`
3. Fuite secrets / credentials DB dans le dépôt
4. Accès non autorisé au dashboard / API
5. Compromission image Docker / supply-chain

---

## 4. Comment le tester ?

Le TP1 n’est pas un test unitaire. On « teste » la **qualité du raisonnement**.

### Checklist de validation

| Test | Comment vérifier | OK si… |
|---|---|---|
| DFD complet | Relire le schéma | Capteurs, broker, APIs, DB, dashboard, frontières visibles |
| Couverture STRIDE | Compter les familles | Les **6** lettres apparaissent au moins une fois |
| Contexte smart-city | Relire les justifications | L’eau / les alertes sont traitées comme vie humaine |
| Cotation | Vérifier V×I | Chaque menace a V, I, et un score |
| Top 5 actionnable | Lire la fiche | Contre-mesure + owner + délai pour les 5 |
| Restitution | Oral 5 min | On peut défendre pourquoi #1 est #1 |

### Mini auto-test (5 questions)

1. Où est la frontière de confiance entre le terrain IoT et l’API ?
2. Quelle menace STRIDE touche surtout Kafka si le topic est ouvert ?
3. Pourquoi une menace DoS sur les alertes cote plus haut qu’une fuite de rapport mensuel ?
4. Qui (Dev/Ops/Sec) possède la contre-mesure « mTLS capteurs » ?
5. Ton Top 5 contient-il au moins un risque **supply-chain** ou **secret** ?

### Preuve à joindre au rendu

- photo / export du DFD
- tableau STRIDE (CSV ou tableur)
- fiche Top 5

---

## Lien avec la suite

| Après TP1… | Le TP suivant… |
|---|---|
| On a listé les risques | **TP2** : on scanne le code/deps/secrets pour **prouver** des failles |
| On a priorisé vie humaine | **TP3** : on priorise les CVE avec la même logique métier |
| On a proposé des contre-mesures | **TP4** : on les automatise en gates CI/CD |
