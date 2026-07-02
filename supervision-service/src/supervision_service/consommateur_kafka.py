"""Consumer Kafka pour ingestion d'événements OCPP."""

import json
import asyncio
from typing import Callable, Optional
from kafka import KafkaConsumer
from .contrats import EvenementBorne, BorneRecharge, SessionCharge, EtatBorne, EtatSession


class ConsommateurEvenementsBorne:
    """Consomme les événements OCPP du topic Kafka et met à jour l'état."""
    
    def __init__(
        self,
        serveurs_kafka: list,
        gestionnaire_etat,
        groupe_consumer: str = "supervision-service"
    ):
        """
        Initialise le consommateur Kafka.
        
        Args:
            serveurs_kafka: Liste de serveurs Kafka, ex: ['localhost:9092']
            gestionnaire_etat: Instance de GestionnaireEtat
            groupe_consumer: Groupe de consumer Kafka
        """
        self.gestionnaire_etat = gestionnaire_etat
        self.groupe_consumer = groupe_consumer
        self.serveurs_kafka = serveurs_kafka
        self.consumer = None
        self.running = False
        self.topic_source = "charge.station.events"
    
    def demarrer(self) -> None:
        """Démarre le consommateur Kafka."""
        try:
            self.consumer = KafkaConsumer(
                self.topic_source,
                bootstrap_servers=self.serveurs_kafka,
                group_id=self.groupe_consumer,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                max_poll_records=100,
            )
            self.running = True
            print(f"Consumer Kafka démarré sur le topic: {self.topic_source}")
        except Exception as e:
            print(f"Erreur lors du démarrage du consumer: {e}")
            raise
    
    def arreter(self) -> None:
        """Arrête le consommateur Kafka."""
        self.running = False
        if self.consumer:
            self.consumer.close()
            print("Consumer Kafka arrêté")
    
    def consommer_boucle(self) -> None:
        """Boucle infinie de consommation d'événements."""
        if not self.consumer:
            raise RuntimeError("Consumer non démarré. Appelez demarrer() d'abord.")
        
        while self.running:
            try:
                messages = self.consumer.poll(timeout_ms=1000, max_records=10)
                for partition, records in messages.items():
                    for record in records:
                        self.traiter_message(record.value)
            except Exception as e:
                print(f"Erreur dans la boucle de consommation: {e}")
                # Continuer plutôt que de crash
    
    def traiter_message(self, donnees_message: dict) -> None:
        """
        Traite un message reçu du topic Kafka.
        
        Exemple de message:
        {
            "type_evenement": "borne_status_changed",
            "borne_id": "FR-SOLAGNE-0001",
            "connecteur_id": "CONN-001",
            "nouvel_etat": "charging",
            "ancien_etat": "available",
            "timestamp": "2025-01-20T14:23:45Z",
            "session_id": "SESSION-12345"
        }
        """
        try:
            type_evt = donnees_message.get("type_evenement")
            borne_id = donnees_message.get("borne_id")
            
            if type_evt == "borne_status_changed":
                self._traiter_changement_etat_borne(donnees_message)
            elif type_evt == "session_started":
                self._traiter_debut_session(donnees_message)
            elif type_evt == "session_ended":
                self._traiter_fin_session(donnees_message)
            elif type_evt == "borne_health_degraded":
                self._traiter_sante_degradee(donnees_message)
            else:
                print(f"Type d'événement inconnu: {type_evt}")
        except Exception as e:
            print(f"Erreur lors du traitement du message: {e}")
    
    def _traiter_changement_etat_borne(self, donnees: dict) -> None:
        """Traite un changement d'état de borne."""
        borne_id = donnees.get("borne_id")
        nouvel_etat = donnees.get("nouvel_etat")
        
        borne = self.gestionnaire_etat.obtenir_borne(borne_id)
        if not borne:
            # Créer une borne vide si elle n'existe pas (sera enrichie plus tard)
            borne = BorneRecharge(
                id=borne_id,
                nom=f"Borne {borne_id}",
                adresse="À déterminer",
                latitude=0.0,
                longitude=0.0,
                nombre_connecteurs=1
            )
            self.gestionnaire_etat.ajouter_borne(borne)
        
        self.gestionnaire_etat.mettre_a_jour_etat_borne(borne_id, nouvel_etat)
        print(f"Borne {borne_id}: changement d'état vers {nouvel_etat}")
    
    def _traiter_debut_session(self, donnees: dict) -> None:
        """Traite le début d'une session de charge."""
        session_id = donnees.get("session_id")
        borne_id = donnees.get("borne_id")
        utilisateur_id = donnees.get("user_id", "ANONYME")
        
        session = SessionCharge(
            id=session_id,
            borne_id=borne_id,
            connecteur_id=donnees.get("connecteur_id", "CONN-001"),
            utilisateur_id=utilisateur_id,
            etat=EtatSession.EN_COURS,
            date_debut=donnees.get("start_time")
        )
        
        self.gestionnaire_etat.ajouter_session(session)
        self.gestionnaire_etat.mettre_a_jour_etat_borne(borne_id, EtatBorne.EN_CHARGE)
        print(f"Session {session_id} démarrée sur borne {borne_id}")
    
    def _traiter_fin_session(self, donnees: dict) -> None:
        """Traite la fin d'une session de charge."""
        session_id = donnees.get("session_id")
        borne_id = donnees.get("borne_id")
        
        self.gestionnaire_etat.terminer_session(session_id)
        self.gestionnaire_etat.mettre_a_jour_etat_borne(borne_id, EtatBorne.DISPONIBLE)
        print(f"Session {session_id} terminée")
    
    def _traiter_sante_degradee(self, donnees: dict) -> None:
        """Traite une dégradation de santé d'une borne."""
        borne_id = donnees.get("borne_id")
        raison = donnees.get("raison", "Santé dégradée")
        
        borne = self.gestionnaire_etat.obtenir_borne(borne_id)
        if borne:
            borne.sante = "degrade"
            print(f"Santé dégradée pour borne {borne_id}: {raison}")
