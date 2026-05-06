# Kafka local avec Docker

Ce fichier documente la partie Kafka de la branche `hans-kafka`.

L'objectif est de préparer un vrai broker Kafka local pour UrbanHub sans prendre en charge les regles metier des autres services. Cette branche fournit l'infrastructure, les topics cibles et un smoke test Python qui prouve qu'un evenement capteur peut etre publie puis consomme.

## Role de Kafka

Kafka sert de broker asynchrone entre les services UrbanHub.

Flux cible du livrable :

```text
Capteur IoT -> Kafka -> Service qualite eau -> Service alertes -> Kafka -> Service notifications
```

Notre perimetre actuel :

```text
Producer Python -> topic mesure.qualite.eau -> Consumer Python
```

Les services ingestion, alertes et notifications pourront ensuite remplacer ces scripts de test.

## Services Docker

Le fichier `docker-compose.yml` lance :

| Service | Port hote | Role |
| --- | --- | --- |
| `kafka` | `9094` | Broker Kafka local |
| `kafka-ui` | `8080` | Interface web pour inspecter topics et messages |

Kafka ecoute sur deux adresses :

| Adresse | Usage |
| --- | --- |
| `kafka:9092` | Communication entre conteneurs Docker |
| `localhost:9094` | Communication depuis Python sur la machine hote |

## Topics prevus

| Topic | Role |
| --- | --- |
| `mesure.qualite.eau` | Evenements publies par les capteurs ou le service ingestion |
| `mesure.qualite.eau.dlq` | Dead Letter Queue pour messages non traitables |
| `alerte.pollution.detectee` | Evenements d'alerte publies apres detection |

Le topic principal est partitionne par cle Kafka `capteur_id`. Cela permettra de conserver l'ordre des mesures pour un meme capteur.

## Lancer Kafka

```bash
docker compose up -d
```

Verifier les conteneurs :

```bash
docker compose ps
```

Kafka UI est disponible ici :

```text
http://localhost:8080
```

## Installer les dependances Python

Le projet utilise `uv`.

```bash
uv sync
```

## Publier un evenement de test

```bash
uv run python scripts/kafka_producer.py
```

Le producer publie un JSON sur `mesure.qualite.eau` avec :

- `event_id`
- `trace_id`
- `capteur_id`
- `timestamp`
- `localisation`
- `mesures`

Le `capteur_id` est utilise comme cle Kafka.

## Lire un evenement de test

Dans un autre terminal :

```bash
uv run python scripts/kafka_consumer.py
```

Le consumer lit un message depuis `mesure.qualite.eau`, affiche les headers et le payload, puis commit l'offset.

## Variables d'environnement

Les valeurs par defaut sont dans `src/kafka_settings.py`.

| Variable | Defaut |
| --- | --- |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9094` |
| `WATER_QUALITY_TOPIC` | `mesure.qualite.eau` |
| `KAFKA_CONSUMER_GROUP` | `urbanhub-water-quality-local` |
| `KAFKA_CONSUMER_TIMEOUT_SECONDS` | `30` |

Si le consumer ne lit rien, verifier le groupe de consommation. Un groupe Kafka qui a deja consomme tous les messages ne relit pas les memes offsets. Pour un smoke test qui relit depuis le debut, utiliser un nouveau groupe :

```bash
KAFKA_CONSUMER_GROUP=urbanhub-smoke-1 uv run python scripts/kafka_consumer.py
```

## Integration avec les autres branches

Quand les autres developpeurs auront termine :

- le service ingestion publiera sur `mesure.qualite.eau`
- le service qualite eau consommera ce topic
- le service alertes exposera `POST /alertes`
- le service alertes pourra publier `alerte.pollution.detectee`
- le service notifications consommera `alerte.pollution.detectee`

Cette branche ne fige pas les regles metier. Elle prepare uniquement le transport Kafka et les conventions communes.

## Arret

```bash
docker compose down
```

Pour supprimer aussi les donnees Kafka locales :

```bash
docker compose down -v
```
