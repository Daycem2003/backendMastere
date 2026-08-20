"""
Voir la note de tests/integration/test_role_assignment.py concernant la DB de
test requise. Ces tests exercent en plus la couche HTTP complète (FastAPI
TestClient + auth JWT réelle), donc nécessitent AUSSI qu'un utilisateur ADMIN
de test existe et qu'on puisse obtenir un token pour lui.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from src.fastapi_app.main import app


@pytest.mark.skip(reason="Nécessite tests/conftest.py avec DB de test + fixture d'un ADMIN authentifié")
@pytest.mark.asyncio
async def test_list_roles_requires_admin_role():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Sans token -> 401 attendu (pas de header Authorization).
        response = await client.get("/api/v1/authorization/roles")
        assert response.status_code == 401


@pytest.mark.skip(reason="Nécessite tests/conftest.py avec DB de test + fixture d'un ADMIN authentifié")
@pytest.mark.asyncio
async def test_admin_can_list_roles(admin_auth_headers):  # fixture à définir dans conftest.py
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/authorization/roles", headers=admin_auth_headers)

        assert response.status_code == 200
        codes = [role["code"] for role in response.json()]
        assert "ADMIN" in codes
        assert "COORDINATOR" in codes
        assert "CANDIDATE" in codes
