"""Point d'entrée du Service de Supervision."""

import asyncio
from fastapi import FastAPI
from .gestion_etat import GestionnaireEtat
from .consommateur_kafka import ConsommateurEvenementsBorne
from .api import creer_app


# Gestionnaire d'état global
gestionnaire = GestionnaireEtat()

# Consommateur Kafka
consommateur = None


def creer_service(
    serveurs_kafka: list = None,
    groupe_consumer: str = "supervision-service"
) -> FastAPI:
    """Crée et initialise le service de supervision."""
    global consommateur
    
    if serveurs_kafka is None:
        serveurs_kafka = ["localhost:9092"]
    
    # Créer l'app FastAPI
    app = creer_app(gestionnaire)
    
    # Initialiser le consommateur Kafka
    consommateur = ConsommateurEvenementsBorne(
        serveurs_kafka=serveurs_kafka,
        gestionnaire_etat=gestionnaire,
        groupe_consumer=groupe_consumer
    )
    
    @app.on_event("startup")
    async def startup_event():
        """Appelé au démarrage du service."""
        print("Démarrage du Service de Supervision...")
        consommateur.demarrer()
        
        # Lancer le consumer Kafka dans une tâche de fond
        loop = asyncio.get_event_loop()
        loop.create_task(asyncio.to_thread(consommateur.consommer_boucle))
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Appelé à l'arrêt du service."""
        print("Arrêt du Service de Supervision...")
        consommateur.arreter()
    
    return app


# Créer l'instance de l'app
app = creer_service()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
