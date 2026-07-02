"""Contrats d'API et modèles de données pour le Service de Supervision."""

from enum import Enum
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Énumérations (états)
# ============================================================================

class EtatBorne(str, Enum):
    """État d'une borne de recharge."""
    DISPONIBLE = "disponible"
    RESERVEE = "reservee"
    EN_CHARGE = "en_charge"
    MAINTENANCE = "maintenance"
    HORS_SERVICE = "hors_service"


class TypeConnecteur(str, Enum):
    """Type de connecteur de charge."""
    TYPE2 = "type2"
    CHADEMO = "chademo"
    CCS = "ccs"
    AC = "ac"


class EtatConnecteur(str, Enum):
    """État d'un connecteur."""
    LIBRE = "libre"
    OCCUPE = "occupe"
    RESERVE = "reserve"
    MAINTENANCE = "maintenance"


class EtatSession(str, Enum):
    """État d'une session de charge."""
    INITIEE = "initiee"
    AUTHENTIFIEE = "authentifiee"
    EN_COURS = "en_cours"
    TERMINEE = "terminee"
    FACTUREE = "facturee"
    ECHEC = "echec"


class EtatPaiement(str, Enum):
    """État du paiement d'une session."""
    EN_ATTENTE = "en_attente"
    AUTORISEE = "autorisee"
    FACTUREE = "facturee"
    ECHEC = "echec"


class NiveauSante(str, Enum):
    """État de santé d'une borne."""
    OK = "ok"
    DEGRADE = "degrade"
    DEFAILLANCE = "defaillance"


# ============================================================================
# Modèles de données (contrats API)
# ============================================================================

class Connecteur(BaseModel):
    """Représentation d'un connecteur de charge."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(..., description="Identifiant unique du connecteur, ex: CONN-001")
    type: TypeConnecteur = Field(..., description="Type de connecteur (Type2, CCS, CHAdeMO, AC)")
    etat: EtatConnecteur = Field(..., description="État actuel du connecteur")
    puissance_kw: float = Field(..., description="Puissance disponible en kW", gt=0)
    session_id: Optional[str] = Field(None, description="ID de session en cours, si occupé")
    date_dernier_maj: datetime = Field(default_factory=datetime.utcnow)


class BorneRecharge(BaseModel):
    """Représentation d'une borne de recharge."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(..., description="Identifiant unique, ex: FR-SOLAGNE-0001")
    nom: str = Field(..., description="Nom du lieu, ex: Square République")
    adresse: str = Field(..., description="Adresse complète")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    
    etat: EtatBorne = Field(default=EtatBorne.DISPONIBLE)
    sante: NiveauSante = Field(default=NiveauSante.OK)
    
    connecteurs: List[Connecteur] = Field(default_factory=list)
    nombre_connecteurs: int = Field(..., gt=0, description="Nombre total de connecteurs")
    
    sessions_actives: List[str] = Field(default_factory=list, description="IDs des sessions en cours")
    
    date_dernier_maj: datetime = Field(default_factory=datetime.utcnow)
    date_maintenance: Optional[datetime] = None


class SessionCharge(BaseModel):
    """Représentation d'une session de charge."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(..., description="ID unique de session, généré par OCPP")
    borne_id: str = Field(..., description="ID de la borne utilisée")
    connecteur_id: str = Field(..., description="ID du connecteur utilisé")
    utilisateur_id: str = Field(..., description="ID de l'utilisateur/conducteur")
    
    etat: EtatSession = Field(default=EtatSession.INITIEE)
    etat_paiement: EtatPaiement = Field(default=EtatPaiement.EN_ATTENTE)
    
    date_debut: datetime = Field(..., description="Date/heure de début")
    date_fin: Optional[datetime] = None
    
    energie_kwh: float = Field(default=0.0, ge=0)
    duree_minutes: int = Field(default=0, ge=0)
    cout_eur: float = Field(default=0.0, ge=0)


class EvenementBorne(BaseModel):
    """Événement OCPP reçu d'une borne."""
    model_config = ConfigDict(from_attributes=True)
    
    type_evenement: str = Field(..., description="Type: 'statut_change', 'session_debut', 'session_fin'")
    borne_id: str
    connecteur_id: Optional[str] = None
    session_id: Optional[str] = None
    
    nouvel_etat: Optional[str] = None
    ancien_etat: Optional[str] = None
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    donnees_brutes: dict = Field(default_factory=dict, description="Données OCPP brutes")


class ResumeDashboard(BaseModel):
    """Résumé en temps réel de l'état du réseau de bornes."""
    model_config = ConfigDict(from_attributes=True)
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    nombre_bornes_total: int = 0
    bornes_disponibles: int = 0
    bornes_reservees: int = 0
    bornes_en_charge: int = 0
    bornes_maintenance: int = 0
    
    sessions_actives: int = 0
    energie_total_kwh: float = 0.0
    chiffre_affaires_eur: float = 0.0
    
    nombre_incidents: int = 0
    sante_reseau: float = Field(default=100.0, ge=0, le=100, description="Score de santé 0-100")


class RéponseListe(BaseModel):
    """Réponse paginée pour les listes."""
    model_config = ConfigDict(from_attributes=True)
    
    total: int
    page: int
    taille_page: int
    resultats: List[dict]


class Incident(BaseModel):
    """Représentation d'un incident détecté."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(..., description="ID unique de l'incident")
    borne_id: str = Field(..., description="ID de la borne concernée")
    type: str = Field(..., description="Type: deconnexion, defaillance, anomalie")
    severite: str = Field(..., description="critique, majeure, mineure")
    description: str
    
    date_detection: datetime = Field(default_factory=datetime.utcnow)
    date_resolution: Optional[datetime] = None
    
    resolu: bool = Field(default=False)
