"""API REST et endpoints du Service de Supervision."""

from fastapi import FastAPI, HTTPException, Query, WebSocketDisconnect, WebSocket
from fastapi.responses import JSONResponse
from typing import List, Optional
import json
from datetime import datetime

from .contrats import BorneRecharge, SessionCharge, ResumeDashboard
from .gestion_etat import GestionnaireEtat


def creer_app(gestionnaire_etat: GestionnaireEtat) -> FastAPI:
    """Crée et configure l'application FastAPI."""
    
    app = FastAPI(
        title="Service de Supervision IRVE",
        description="Supervision en temps réel des bornes de recharge électriques",
        version="0.1.0",
    )
    
    # ========================================================================
    # Gestion des WebSocket
    # ========================================================================
    
    clients_websocket = set()
    
    @app.websocket("/ws/supervision/direct")
    async def websocket_supervision(websocket: WebSocket):
        """WebSocket pour les mises à jour en temps réel du tableau de bord."""
        await websocket.accept()
        clients_websocket.add(websocket)
        
        def envoyer_update(type_changement: str, donnees: any):
            """Callback appelé lors d'un changement d'état."""
            try:
                message = {
                    "type": type_changement,
                    "timestamp": datetime.utcnow().isoformat(),
                    "donnees": donnees if isinstance(donnees, dict) else {
                        "type": type(donnees).__name__,
                        "message": str(donnees)
                    }
                }
                # TODO: Utiliser asyncio.create_task() pour envoyer en async
                for client in clients_websocket:
                    try:
                        client.send_text(json.dumps(message))
                    except:
                        pass
            except Exception as e:
                print(f"Erreur envoyer_update: {e}")
        
        gestionnaire_etat.subscribe(envoyer_update)
        
        try:
            while True:
                # Attendre les messages du client (maintient la connection vivante)
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            clients_websocket.discard(websocket)
            gestionnaire_etat.unsubscribe(envoyer_update)
        except Exception as e:
            print(f"Erreur WebSocket: {e}")
            clients_websocket.discard(websocket)
    
    # ========================================================================
    # Endpoints - Bornes
    # ========================================================================
    
    @app.get("/bornes", response_model=List[BorneRecharge])
    async def lister_bornes(
        etat: Optional[str] = Query(None, description="Filtrer par état"),
        limit: int = Query(100, ge=1, le=1000)
    ):
        """Liste toutes les bornes avec filtres optionnels."""
        bornes = gestionnaire_etat.obtenir_toutes_bornes()
        
        if etat:
            bornes = [b for b in bornes if b.etat.value == etat]
        
        return bornes[:limit]
    
    @app.get("/bornes/{borne_id}", response_model=BorneRecharge)
    async def obtenir_borne(borne_id: str):
        """Récupère les détails d'une borne spécifique."""
        borne = gestionnaire_etat.obtenir_borne(borne_id)
        if not borne:
            raise HTTPException(status_code=404, detail=f"Borne {borne_id} non trouvée")
        return borne
    
    # ========================================================================
    # Endpoints - Sessions
    # ========================================================================
    
    @app.get("/sessions", response_model=List[SessionCharge])
    async def lister_sessions(
        etat: Optional[str] = Query(None),
        borne_id: Optional[str] = Query(None),
        limit: int = Query(50, ge=1, le=500)
    ):
        """Liste les sessions de charge avec filtres optionnels."""
        sessions = list(gestionnaire_etat.sessions.values())
        
        if etat:
            sessions = [s for s in sessions if s.etat.value == etat]
        if borne_id:
            sessions = [s for s in sessions if s.borne_id == borne_id]
        
        return sessions[:limit]
    
    @app.get("/sessions/{session_id}", response_model=SessionCharge)
    async def obtenir_session(session_id: str):
        """Récupère les détails d'une session."""
        session = gestionnaire_etat.obtenir_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} non trouvée")
        return session
    
    # ========================================================================
    # Endpoints - Tableau de bord
    # ========================================================================
    
    @app.get("/tableau-de-bord/resume", response_model=ResumeDashboard)
    async def obtenir_resume_dashboard():
        """Récupère le résumé en temps réel du réseau."""
        stats = gestionnaire_etat.obtenir_statistiques_reseau()
        
        return ResumeDashboard(
            timestamp=datetime.utcnow(),
            nombre_bornes_total=stats.get("nombre_bornes_total", 0),
            bornes_disponibles=stats.get("bornes_par_etat", {}).get("disponible", 0),
            bornes_reservees=stats.get("bornes_par_etat", {}).get("reservee", 0),
            bornes_en_charge=stats.get("bornes_par_etat", {}).get("en_charge", 0),
            bornes_maintenance=stats.get("bornes_par_etat", {}).get("maintenance", 0),
            sessions_actives=stats.get("sessions_actives", 0),
            energie_total_kwh=stats.get("energie_total_kwh", 0.0),
            chiffre_affaires_eur=stats.get("chiffre_affaires_eur", 0.0),
            nombre_incidents=stats.get("incidents_non_resolus", 0),
            sante_reseau=stats.get("sante_reseau", 100.0)
        )
    
    @app.get("/tableau-de-bord/carte")
    async def obtenir_carte_bornes():
        """Retourne les positions et états des bornes pour affichage carte."""
        bornes = gestionnaire_etat.obtenir_toutes_bornes()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "bornes": [
                {
                    "id": b.id,
                    "nom": b.nom,
                    "latitude": b.latitude,
                    "longitude": b.longitude,
                    "etat": b.etat.value,
                    "sante": b.sante.value,
                    "connecteurs_total": b.nombre_connecteurs,
                    "connecteurs_libres": len([c for c in b.connecteurs if c.etat.value == "libre"]),
                    "sessions_actives": len(b.sessions_actives)
                }
                for b in bornes
            ]
        }
    
    # ========================================================================
    # Endpoints - Incidents
    # ========================================================================
    
    @app.get("/incidents")
    async def lister_incidents(limit: int = Query(20, ge=1, le=100)):
        """Liste les incidents récents."""
        incidents = sorted(
            gestionnaire_etat.incidents.values(),
            key=lambda i: i.date_detection,
            reverse=True
        )
        return incidents[:limit]
    
    # ========================================================================
    # Endpoints - Santé & Métriques
    # ========================================================================
    
    @app.get("/sante")
    async def sante_service():
        """Endpoint de santé pour les healthchecks."""
        stats = gestionnaire_etat.obtenir_statistiques_reseau()
        return {
            "statut": "sain",
            "timestamp": datetime.utcnow().isoformat(),
            "bornes_chargees": stats.get("nombre_bornes_total", 0) > 0,
            "nombre_bornes": stats.get("nombre_bornes_total", 0)
        }
    
    @app.get("/metriques")
    async def obtenir_metriques():
        """Retourne les métriques du réseau."""
        return gestionnaire_etat.obtenir_statistiques_reseau()
    
    # ========================================================================
    # Gestion des erreurs
    # ========================================================================
    
    @app.exception_handler(HTTPException)
    async def gestionnaire_http_exception(request, exc):
        """Gestionnaire centralisé des erreurs HTTP."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    return app
