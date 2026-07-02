# Changelog

## Version 0.1.1 (YYYY-MM-DD)

- **Added**: WebSocket endpoint `/ws/supervision/direct` for real-time dashboard updates.
- **Refactored**: Moved WebSocket handling to its own section in `api.py`.
- **Updated**: Added error handling and logging for WebSocket connections.
- **Improved**: Enhanced the `/tableau-de-bord/carte` endpoint to include more detailed information about each borne.

## Version 0.1.0 (YYYY-MM-DD)

- **Initial Release**:
  - Created the `main.py` file to serve as the entry point of the Service de Supervision.
  - Implemented endpoints for managing bornes, sessions, and incidents.
  - Added a health check endpoint `/sante`.
  - Integrated Kafka consumer for real-time event processing.
