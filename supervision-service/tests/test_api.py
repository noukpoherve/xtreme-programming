"""Tests API du service de supervision."""

import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ["DISABLE_KAFKA_CONSUMER"] = "1"

from supervision_service.contrats import (  # noqa: E402
    BorneRecharge,
    Connecteur,
    EtatBorne,
    EtatConnecteur,
    NiveauSante,
    TypeConnecteur,
)
from supervision_service.gestion_etat import GestionnaireEtat  # noqa: E402
from supervision_service.api import creer_app  # noqa: E402


@pytest.fixture
def gestionnaire():
    g = GestionnaireEtat()
    g.ajouter_borne(
        BorneRecharge(
            id="FR-SOLAGNE-0001",
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
    )
    return g


@pytest_asyncio.fixture
async def client(gestionnaire):
    app = creer_app(gestionnaire)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_sante_service(client):
    response = await client.get("/sante")
    assert response.status_code == 200
    assert response.json()["statut"] == "sain"


@pytest.mark.asyncio
async def test_lister_bornes(client):
    response = await client.get("/bornes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "FR-SOLAGNE-0001"


@pytest.mark.asyncio
async def test_obtenir_borne_inconnue_404(client):
    response = await client.get("/bornes/INEXISTANT")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_resume_dashboard(client):
    response = await client.get("/tableau-de-bord/resume")
    assert response.status_code == 200
    data = response.json()
    assert data["nombre_bornes_total"] == 1
    assert data["bornes_disponibles"] == 1
