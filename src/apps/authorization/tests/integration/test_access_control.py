"""
Voir la note de tests/integration/test_role_assignment.py concernant la DB de
test requise. Ce fichier valide le comportement bout-en-bout des policies
combinées à l'API réelle (pas juste la logique pure déjà testée dans
tests/unit/test_policies.py).
"""

import pytest
from httpx import AsyncClient, ASGITransport

from src.fastapi_app.main import app


@pytest.mark.skip(reason="Nécessite tests/conftest.py avec DB de test + 2 coordinateurs de test")
@pytest.mark.asyncio
async def test_coordinator_cannot_update_another_coordinators_master(
    coordinator_a_auth_headers,  # fixtures à définir dans conftest.py
    master_owned_by_coordinator_b_pubkey,
):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            f"/api/v1/masters/{master_owned_by_coordinator_b_pubkey}",
            headers=coordinator_a_auth_headers,
            json={"nom": "Tentative de modification non autorisée"},
        )

        assert response.status_code == 403


@pytest.mark.skip(reason="Nécessite tests/conftest.py avec DB de test + un master en BROUILLON")
@pytest.mark.asyncio
async def test_draft_master_not_visible_to_anonymous(draft_master_pubkey):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/masters/{draft_master_pubkey}")

        assert response.status_code in (403, 404)
