# Kafka local avec Docker

Ce fichier documente la partie Kafka de la branche `master` apres fusion de `hans-kafka`.

Le flux metier est maintenant branche sur Kafka :

```text
IoT Service -> topic mesure.qualite.eau -> Alert Service -> topic alerte.pollution.detectee
```

Le service IoT publie les mesures dans Kafka, et le service Alert consomme ce topic, construit les alertes, les traite via son endpoint interne, puis republie les alertes sur le topic de sortie.

## Role de Kafka

Kafka sert de broker asynchrone entre les services UrbanHub.

Flux cible du livrable :

```text
Capteur IoT -> Kafka -> Service qualite eau -> Service alertes -> Kafka -> Service notifications
```

Perimetre actuel :

```text
Producer Python -> topic mesure.qualite.eau -> Alert Service Kafka bridge -> topic alerte.pollution.detectee
```

Le service notifications n'est pas encore present dans le depot, mais le topic de sortie est deja prepare pour lui.

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
| `mesure.qualite.eau` | Evenements publies par le service IoT |
| `alerte.pollution.detectee` | Evenements d'alerte republies par le service Alert |
| `mesure.qualite.eau.dlq` | Dead Letter Queue reservee pour une evolution future |

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

Les valeurs par defaut sont dans `src/kafka_settings.py` et dans les settings du service Alert.

| Variable | Defaut |
| --- | --- |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9094` |
| `WATER_QUALITY_TOPIC` | `mesure.qualite.eau` |
| `KAFKA_CONSUMER_GROUP` | `urbanhub-water-quality-local` |
| `KAFKA_CONSUMER_TIMEOUT_SECONDS` | `30` |

Pour le service IoT, activer le publish Kafka avec `IOT_ENABLE_KAFKA=true`.

Pour le service Alert, activer le bridge Kafka avec `ALERT_ENABLE_KAFKA_BRIDGE=true`.

Si le consumer ne lit rien, verifier le groupe de consommation. Un groupe Kafka qui a deja consomme tous les messages ne relit pas les memes offsets. Pour un smoke test qui relit depuis le debut, utiliser un nouveau groupe :

```bash
KAFKA_CONSUMER_GROUP=urbanhub-smoke-1 uv run python scripts/kafka_consumer.py
```

## Integration avec les autres branches

Le service `alertes` conserve son endpoint `POST /alertes`, mais son flux reel passe maintenant par Kafka.

## Arret

```bash
docker compose down
```

Pour supprimer aussi les donnees Kafka locales :

```bash
docker compose down -v
```
