"""Tests unitaires du gestionnaire d'etat supervision."""

from datetime import datetime

from supervision_service.contrats import (
    BorneRecharge,
    Connecteur,
    EtatBorne,
    EtatConnecteur,
    EtatSession,
    Incident,
    NiveauSante,
    SessionCharge,
    TypeConnecteur,
)
from supervision_service.gestion_etat import GestionnaireEtat


def _borne(borne_id: str = "FR-SOLAGNE-0001") -> BorneRecharge:
    return BorneRecharge(
        id=borne_id,
        nom="Place Republique",
        adresse="1 Place Republique",
        latitude=48.867,
        longitude=2.363,
        etat=EtatBorne.DISPONIBLE,
        sante=NiveauSante.OK,
        connecteurs=[
            Connecteur(
                id="CONN-001",
                type=TypeConnecteur.TYPE2,
                etat=EtatConnecteur.LIBRE,
                puissance_kw=22.0,
            )
        ],
        nombre_connecteurs=1,
    )


def test_ajouter_et_recuperer_borne():
    gestionnaire = GestionnaireEtat()
    gestionnaire.ajouter_borne(_borne())
    borne = gestionnaire.obtenir_borne("FR-SOLAGNE-0001")
    assert borne is not None
    assert borne.nom == "Place Republique"


def test_mise_a_jour_etat_borne():
    gestionnaire = GestionnaireEtat()
    gestionnaire.ajouter_borne(_borne())
    updated = gestionnaire.mettre_a_jour_etat_borne("FR-SOLAGNE-0001", EtatBorne.EN_CHARGE)
    assert updated is not None
    assert updated.etat == EtatBorne.EN_CHARGE


def test_sessions_actives_et_terminaison():
    gestionnaire = GestionnaireEtat()
    gestionnaire.ajouter_borne(_borne())
    session = SessionCharge(
        id="SESSION-001",
        borne_id="FR-SOLAGNE-0001",
        connecteur_id="CONN-001",
        utilisateur_id="USER-001",
        etat=EtatSession.EN_COURS,
        date_debut=datetime.utcnow(),
        energie_kwh=12.5,
        cout_eur=4.2,
    )
    gestionnaire.ajouter_session(session)
    assert len(gestionnaire.obtenir_sessions_actives()) == 1

    gestionnaire.terminer_session("SESSION-001")
    assert len(gestionnaire.obtenir_sessions_actives()) == 0


def test_incident_non_resolu():
    gestionnaire = GestionnaireEtat()
    gestionnaire.ajouter_incident(
        Incident(
            id="INC-001",
            borne_id="FR-SOLAGNE-0001",
            type="deconnexion",
            severite="majeure",
            description="Borne hors ligne",
        )
    )
    assert len(gestionnaire.obtenir_incidents_non_resolus()) == 1


def test_observer_notifie_les_listeners():
    gestionnaire = GestionnaireEtat()
    events = []

    gestionnaire.subscribe(lambda event_type, data: events.append(event_type))
    gestionnaire.ajouter_borne(_borne())
    assert "borne_ajoutee" in events
