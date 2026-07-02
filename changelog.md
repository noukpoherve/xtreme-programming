# Changelog

Toutes les modifications notables de ce projet sont documentees dans ce fichier.

Le format s'inspire de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) et applique le versioning semantique.

## [0.1.1] - YYYY-MM-DD

### Added
- Endpoint WebSocket `/ws/supervision/direct` pour des mises a jour temps reel du dashboard.

### Changed
- Reorganisation de la gestion WebSocket dans une section dediee de `api.py`.
- Amelioration de l'endpoint `/tableau-de-bord/carte` avec des informations plus detaillees pour chaque borne.

### Fixed
- Ajout de la gestion d'erreurs et de logs pour les connexions WebSocket.

## [0.1.0] - YYYY-MM-DD

### Added
- Version initiale du service de supervision.
- Creation de `main.py` comme point d'entree principal.
- Mise en place des endpoints de gestion des bornes, sessions et incidents.
- Ajout de l'endpoint de sante `/sante`.
- Integration d'un consommateur Kafka pour le traitement des evenements en temps reel.
