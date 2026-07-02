"""Service de gestion des états et cache en mémoire."""

from typing import Dict, List, Optional
from datetime import datetime
from .contrats import BorneRecharge, SessionCharge, EvenementBorne, Incident, EtatBorne, EtatSession


class GestionnaireEtat:
    """Gestionnaire centralisant l'état en temps réel du réseau de bornes."""
    
    def __init__(self):
        """Initialise le gestionnaire d'état."""
        self.bornes: Dict[str, BorneRecharge] = {}
        self.sessions: Dict[str, SessionCharge] = {}
        self.incidents: Dict[str, Incident] = {}
        self._listeners = []
    
    # ========================================================================
    # Gestion des bornes
    # ========================================================================
    
    def ajouter_borne(self, borne: BorneRecharge) -> None:
        """Ajoute ou met à jour une borne."""
        self.bornes[borne.id] = borne
        self._notifier("borne_ajoutee", borne)
    
    def obtenir_borne(self, borne_id: str) -> Optional[BorneRecharge]:
        """Récupère une borne par son ID."""
        return self.bornes.get(borne_id)
    
    def obtenir_toutes_bornes(self) -> List[BorneRecharge]:
        """Récupère toutes les bornes."""
        return list(self.bornes.values())
    
    def mettre_a_jour_etat_borne(
        self, borne_id: str, nouvel_etat: EtatBorne | str
    ) -> Optional[BorneRecharge]:
        """Met à jour l'état d'une borne."""
        borne = self.bornes.get(borne_id)
        if borne:
            ancien_etat = borne.etat
            if isinstance(nouvel_etat, str):
                nouvel_etat = EtatBorne(nouvel_etat)
            borne.etat = nouvel_etat
            borne.date_dernier_maj = datetime.utcnow()
            self._notifier("etat_borne_change", {
                "borne_id": borne_id,
                "ancien_etat": ancien_etat,
                "nouvel_etat": nouvel_etat
            })
            return borne
        return None
    
    # ========================================================================
    # Gestion des sessions
    # ========================================================================
    
    def ajouter_session(self, session: SessionCharge) -> None:
        """Ajoute une nouvelle session de charge."""
        self.sessions[session.id] = session
        borne = self.bornes.get(session.borne_id)
        if borne and session.id not in borne.sessions_actives:
            borne.sessions_actives.append(session.id)
        self._notifier("session_ajoutee", session)
    
    def obtenir_session(self, session_id: str) -> Optional[SessionCharge]:
        """Récupère une session par son ID."""
        return self.sessions.get(session_id)
    
    def obtenir_sessions_actives(self) -> List[SessionCharge]:
        """Récupère toutes les sessions en cours."""
        return [s for s in self.sessions.values() if s.etat == EtatSession.EN_COURS]
    
    def terminer_session(self, session_id: str) -> Optional[SessionCharge]:
        """Termine une session de charge."""
        session = self.sessions.get(session_id)
        if session:
            session.etat = EtatSession.TERMINEE
            session.date_fin = datetime.utcnow()
            
            borne = self.bornes.get(session.borne_id)
            if borne and session_id in borne.sessions_actives:
                borne.sessions_actives.remove(session_id)
            
            self._notifier("session_terminee", session)
            return session
        return None
    
    # ========================================================================
    # Gestion des incidents
    # ========================================================================
    
    def ajouter_incident(self, incident: Incident) -> None:
        """Enregistre un nouvel incident."""
        self.incidents[incident.id] = incident
        self._notifier("incident_detecte", incident)
    
    def obtenir_incidents_non_resolus(self) -> List[Incident]:
        """Récupère tous les incidents non résolus."""
        return [i for i in self.incidents.values() if not i.resolu]
    
    def resoudre_incident(self, incident_id: str) -> Optional[Incident]:
        """Marque un incident comme résolu."""
        incident = self.incidents.get(incident_id)
        if incident:
            incident.resolu = True
            incident.date_resolution = datetime.utcnow()
            self._notifier("incident_resolu", incident)
            return incident
        return None
    
    # ========================================================================
    # Métriques et statistiques
    # ========================================================================
    
    def obtenir_statistiques_reseau(self) -> dict:
        """Génère les statistiques actuelles du réseau."""
        bornes = self.obtenir_toutes_bornes()
        sessions_actives = self.obtenir_sessions_actives()
        incidents_non_resolus = self.obtenir_incidents_non_resolus()
        
        etat_count = {}
        for borne in bornes:
            etat = borne.etat
            etat_count[etat] = etat_count.get(etat, 0) + 1
        
        energie_total = sum(s.energie_kwh for s in sessions_actives)
        chiffre_affaires = sum(s.cout_eur for s in sessions_actives)
        
        return {
            "nombre_bornes_total": len(bornes),
            "bornes_par_etat": etat_count,
            "sessions_actives": len(sessions_actives),
            "energie_total_kwh": energie_total,
            "chiffre_affaires_eur": chiffre_affaires,
            "incidents_non_resolus": len(incidents_non_resolus),
            "sante_reseau": self._calculer_sante_reseau(bornes),
        }
    
    def _calculer_sante_reseau(self, bornes: List[BorneRecharge]) -> float:
        """Calcule un score de santé global du réseau (0-100)."""
        if not bornes:
            return 100.0
        
        bornes_ok = sum(1 for b in bornes if b.sante.value == "ok")
        return (bornes_ok / len(bornes)) * 100
    
    # ========================================================================
    # Observateurs (listeners)
    # ========================================================================
    
    def subscribe(self, callback):
        """S'abonne aux changements d'état."""
        self._listeners.append(callback)
    
    def unsubscribe(self, callback):
        """Se désabonne des changements d'état."""
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def _notifier(self, type_changement: str, donnees: any) -> None:
        """Notifie tous les listeners des changements."""
        for listener in self._listeners:
            try:
                listener(type_changement, donnees)
            except Exception as e:
                print(f"Erreur lors de la notification: {e}")
