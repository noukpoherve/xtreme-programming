# Communication technique vs fonctionnelle

> Ce document illustre la différence de ton, de vocabulaire et de niveau de détail entre une communication destinée à un public **métier / fonctionnel** et une communication destinée à un public **technique / opérationnel**.
>
> Contexte : la plateforme UrbanHub surveille la qualité de l'eau de la Seine. Le capteur `SEINE-VITRY-001` vient de passer de l'état `NORMAL` à l'état `CRITICAL`.

---

## 1. Résumé exécutif métier

| Audience | Objectif |
|---|---|
| Directeur de projet, maître d'ouvrage, équipe UrbanHub côté métier, régulateur environnemental | Comprendre l'impact, la gravité et les actions en cours sans entrer dans les détails techniques. |

---

### 📧 Exemple de message fonctionnel

**Objet :** Alerte qualité de l'eau – station Vitry-sur-Seine (SEINE-VITRY-001)

Bonjour,

La plateforme UrbanHub a détecté une anomalie qualité sur la station **Vitry-sur-Seine** à **10 h 14** ce matin.

- **Station concernée :** Vitry-sur-Seine (identifiant SEINE-VITRY-001)
- **Gravité :** Critique 🔴
- **Mesures déclenchantes :** pH anormalement bas (4,0) et turbidité élevée (60 NTU)
- **Impact :** Données non conformes aux seuils réglementaires ; alerte ouverte dans le système.
- **Action en cours :** L'équipe exploitation est notifiée et va procéder à un prélèvement de contrôle sur site.
- **Disponibilité du suivi :** Le tableau de bord UrbanHub est à jour en temps réel : <http://localhost:5173>

Nous vous tiendrons informés dès réception des résultats du prélèvement.

Cordialement,  
L'équipe UrbanHub

---

## 2. Résumé technique

| Audience | Objectif |
|---|---|
| Équipe de développement, DevOps, SRE, architecte, support technique | Identifier la cause racine, les composants impactés, les logs/trace_id et les actions de remédiation techniques. |

---

### 📧 Exemple de message technique

**Objet :** `[ALERT] state_transition CRITICAL on SEINE-VITRY-001 — trace_id=f47ac10b-58cc-4372-a567-0e02b2c3d479`

Hello team,

Le `alert-service` a enregistré une transition d'état **NORMAL → CRITICAL** pour le capteur `SEINE-VITRY-001` à `2026-07-01T10:14:32Z`.

### Détails de l'alerte

- **trace_id :** `f47ac10b-58cc-4372-a567-0e02b2c3d479`
- **sensor_id :** `SEINE-VITRY-001`
- **event_id :** `demo-1`
- **previous_state :** `NORMAL`
- **new_state :** `CRITICAL`
- **anomaly_count :** `3` (seuil atteint après 3 anomalies consécutives)
- **topic Kafka consommé :** `mesure.qualite.eau`
- **topic Kafka produit :** `alerte.pollution.detectee`

### Mesures reçues

```json
{
  "capteur_id": "SEINE-VITRY-001",
  "timestamp": "2026-07-01T10:14:32Z",
  "mesures": {
    "ph": 4.0,
    "turbidite_ntu": 60.0,
    "temperature_c": 20.0,
    "niveau_m": 1.0,
    "debit_m3s": 250.0,
    "oxygene_dissous_mgl": 5.0
  },
  "data_source": "simulated",
  "firmware_version": "2.4.1"
}
```

### Composants impactés

| Composant | Impact | Action |
|---|---|---|
| `alert-service` | Transition CRITICAL émise et persistée | OK |
| `alerte.pollution.detectee` | Message publié | OK |
| `WebSocketHub` | Broadcast envoyé aux dashboards connectés | OK |
| PostgreSQL / TimescaleDB | Ligne insérée dans `state_transitions` + `alerts` | OK |

### Logs utiles

```bash
# Loki
{container="alert-service"} |= "f47ac10b-58cc-4372-a567-0e02b2c3d479"

# PostgreSQL
SELECT * FROM alerts WHERE trace_id = 'f47ac10b-58cc-4372-a567-0e02b2c3d479';
SELECT * FROM state_transitions WHERE sensor_id = 'SEINE-VITRY-001' ORDER BY transitioned_at DESC LIMIT 10;
```

### Points de vigilance

- La mesure porte `data_source: "simulated"` : si la production utilise encore des données simulées, vérifier que le mapping Hub'Eau est bien actif pour ce capteur.
- `ph=4.0` est en dehors de la plage de validation métier : confirmer que le seuil dans `SensorStreamProcessor` est correct (`ph < 6.0` → anomaly).
- Aucun `retry` n'est prévu sur l'insertion DB : si Postgres avait été indisponible, l'alerte aurait été perdue. Voir ADR-07.

### Prochaines étapes

1. Vérifier la cohérence du payload source sur Kafka.
2. Contrôler l'état du consumer group `alert-service-group` (lag, rebalancing).
3. Si l'alerte est réelle, notifier l'équipe exploitation ; si c'est un test, purger la ligne `alerts` et `state_transitions` associée.

Merci,
L'équipe technique UrbanHub

---

## 3. Tableau comparatif

| Critère | Communication fonctionnelle | Communication technique |
|---|---|---|
| **Audience** | MOA, manager, régulateur, grand public | Développeurs, DevOps, SRE, architectes |
| **Objectif** | Informer de l'impact et des actions | Diagnostiquer et remédier |
| **Vocabulaire** | Anomalie, alerte, station, gravité, conformité | `state_transition`, `trace_id`, `hypertable`, consumer group |
| **Niveau de détail** | Haut niveau, synthétique | Granulaire, avec IDs, payloads, requêtes |
| **Métriques** | pH, turbidité, heure, localisation | JSON, offsets Kafka, requêtes SQL, logs Loki |
| **Actions** | Prélèvement, notification, suivi dashboard | Debug, vérification consumer lag, purge DB |
| **Ton** | Rassurant, orienté conséquence | Factuel, orienté investigation |

---

## 4. Quand utiliser quel type de communication ?

| Situation | Recommandation |
|---|---|
| Comité de pilotage / reporting MOA | **Fonctionnelle** avec un encart technique en annexe si besoin. |
| Incident en production (P1/P2) | Les deux : message fonctionnel rapide pour les parties prenantes + canal technique pour l'équipe d'astreinte. |
| Post-mortem | **Technique** détaillée, avec un résumé fonctionnel en introduction. |
| Documentation utilisateur | **Fonctionnelle**. |
| Runbook / procédure d'exploitation | **Technique**, avec liens vers dashboards et commandes copier-coller. |
