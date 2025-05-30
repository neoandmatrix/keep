import asyncio
import importlib
import sys
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.fixtures.client import client, setup_api_key, test_app  # noqa

# Mock data for workflows
MOCK_WORKFLOW_ID = "123e4567-e89b-12d3-a456-426614174000"
MOCK_PROVISIONED_WORKFLOW = {
    "id": MOCK_WORKFLOW_ID,
    "name": "Test Workflow",
    "description": "A provisioned test workflow",
    "provisioned": True,
}


# Test for deleting a provisioned workflow
@pytest.mark.parametrize(
    "test_app",
    [
        {
            "AUTH_TYPE": "NOAUTH",
            "KEEP_WORKFLOWS_DIRECTORY": "./tests/provision/workflows_1",
        },
    ],
    indirect=True,
)
def test_provisioned_workflows(db_session, client, test_app):
    response = client.get("/workflows", headers={"x-api-key": "someapikey"})
    assert response.status_code == 200
    # 3 workflows and 3 provisioned workflows
    workflows = response.json()
    provisioned_workflows = [w for w in workflows if w.get("provisioned")]
    assert len(provisioned_workflows) == 3


# Test for deleting a provisioned workflow
@pytest.mark.parametrize(
    "test_app",
    [
        {
            "AUTH_TYPE": "NOAUTH",
            "KEEP_WORKFLOWS_DIRECTORY": "./tests/provision/workflows_2",
        },
    ],
    indirect=True,
)
def test_provisioned_workflows_2(db_session, client, test_app):
    response = client.get("/workflows", headers={"x-api-key": "someapikey"})
    assert response.status_code == 200
    # 3 workflows and 3 provisioned workflows
    workflows = response.json()
    provisioned_workflows = [w for w in workflows if w.get("provisioned")]
    assert len(provisioned_workflows) == 2


# Test for deleting a provisioned workflow
@pytest.mark.parametrize(
    "test_app",
    [
        {
            "AUTH_TYPE": "NOAUTH",
            "KEEP_WORKFLOWS_DIRECTORY": "./tests/provision/workflows_1",
        },
    ],
    indirect=True,
)
def test_delete_provisioned_workflow(db_session, client, test_app):
    response = client.get("/workflows", headers={"x-api-key": "someapikey"})
    assert response.status_code == 200
    # 3 workflows and 3 provisioned workflows
    workflows = response.json()
    provisioned_workflows = [w for w in workflows if w.get("provisioned")]
    workflow_id = provisioned_workflows[0].get("id")
    response = client.delete(
        f"/workflows/{workflow_id}", headers={"x-api-key": "someapikey"}
    )
    # can't delete a provisioned workflow
    assert response.status_code == 403
    assert response.json() == {"detail": "Cannot delete a provisioned workflow"}


@pytest.mark.parametrize(
    "test_app",
    [
        {
            "AUTH_TYPE": "NOAUTH",
            "KEEP_WORKFLOWS_DIRECTORY": "./tests/provision/workflows_1",
        },
    ],
    indirect=True,
)
def test_update_provisioned_workflow(db_session, client, test_app):
    response = client.get("/workflows", headers={"x-api-key": "someapikey"})
    assert response.status_code == 200
    # 3 workflows and 3 provisioned workflows
    workflows = response.json()
    provisioned_workflows = [w for w in workflows if w.get("provisioned")]
    workflow_id = provisioned_workflows[0].get("id")
    response = client.put(
        f"/workflows/{workflow_id}", headers={"x-api-key": "someapikey"}
    )
    # can't delete a provisioned workflow
    assert response.status_code == 403
    assert response.json() == {"detail": "Cannot update a provisioned workflow"}


@pytest.mark.parametrize(
    "test_app",
    [
        {
            "AUTH_TYPE": "NOAUTH",
            "KEEP_WORKFLOWS_DIRECTORY": "./tests/provision/workflows_1",
        },
    ],
    indirect=True,
)
def test_reprovision_workflow(monkeypatch, db_session, client, test_app):
    response = client.get("/workflows", headers={"x-api-key": "someapikey"})
    assert response.status_code == 200
    # 3 workflows and 3 provisioned workflows
    workflows = response.json()
    provisioned_workflows = [w for w in workflows if w.get("provisioned")]
    assert len(provisioned_workflows) == 3

    # Step 2: Change environment variables (simulating new provisioning)
    monkeypatch.setenv("KEEP_WORKFLOWS_DIRECTORY", "./tests/provision/workflows_2")

    # Reload the app to apply the new environment changes
    importlib.reload(sys.modules["keep.api.api"])

    # Reinitialize the TestClient with the new app instance
    from keep.api.api import get_app

    app = get_app()

    # Manually trigger the startup event
    for event_handler in app.router.on_startup:
        asyncio.run(event_handler())

    # manually trigger the provision resources
    from keep.api.config import provision_resources

    provision_resources()

    client = TestClient(get_app())

    response = client.get("/workflows", headers={"x-api-key": "someapikey"})
    assert response.status_code == 200
    # 2 workflows and 2 provisioned workflows
    workflows = response.json()
    provisioned_workflows = [w for w in workflows if w.get("provisioned")]
    assert len(provisioned_workflows) == 2


VICTORIA_METRICS_PROVIDER = {
    "type": "victoriametrics",
    "authentication": {"VMAlertHost": "http://localhost", "VMAlertPort": 1234},
}

CLICKHOUSE_PROVIDER = {
    "type": "clickhouse",
    "authentication": {
        "host": "http://localhost",
        "port": 1234,
        "username": "keep",
        "password": "keep",
        "database": "keep-db",
    },
}

PROMETHEUS_PROVIDER = {
    "type": "prometheus",
    "authentication": {"url": "http://localhost", "port": 9090},
}

AIRFLOW_PROVIDER = {
    "type": "airflow",
}


@pytest.mark.parametrize(
    "test_app",
    [
        {
            "AUTH_TYPE": "NOAUTH",
            "KEEP_PROVIDERS": json.dumps(
                {
                    "keepVictoriaMetrics": VICTORIA_METRICS_PROVIDER,
                    "keepClickhouse1": CLICKHOUSE_PROVIDER,
                    "keepAirflow": AIRFLOW_PROVIDER,
                }
            ),
        },
    ],
    indirect=True,
)
def test_provision_provider(db_session, client, test_app):
    response = client.get("/providers", headers={"x-api-key": "someapikey"})
    assert response.status_code == 200
    providers = response.json()
    provisioned_providers = [
        p for p in providers.get("installed_providers") if p.get("provisioned")
    ]
    assert len(provisioned_providers) == 3


@pytest.mark.parametrize(
    "test_app",
    [
        {
            "AUTH_TYPE": "NOAUTH",
            "KEEP_PROVIDERS": json.dumps(
                {
                    "keepVictoriaMetrics": VICTORIA_METRICS_PROVIDER,
                    "keepClickhouse1": CLICKHOUSE_PROVIDER,
                }
            ),
        },
    ],
    indirect=True,
)
def test_reprovision_provider(monkeypatch, db_session, client, test_app):
    response = client.get("/providers", headers={"x-api-key": "someapikey"})
    assert response.status_code == 200
    # 3 workflows and 3 provisioned workflows
    providers = response.json()
    provisioned_providers = [
        p for p in providers.get("installed_providers") if p.get("provisioned")
    ]
    assert len(provisioned_providers) == 2

    # Step 2: Change environment variables (simulating new provisioning)
    monkeypatch.setenv(
        "KEEP_PROVIDERS",
        json.dumps(
            {
                "keepPrometheus": PROMETHEUS_PROVIDER,
            }
        ),
    )

    # Reload the app to apply the new environment changes
    importlib.reload(sys.modules["keep.api.api"])

    # Reinitialize the TestClient with the new app instance
    from keep.api.api import get_app

    app = get_app()

    # Manually trigger the startup event
    for event_handler in app.router.on_startup:
        asyncio.run(event_handler())

    # manually trigger the provision resources
    from keep.api.config import provision_resources

    provision_resources()

    client = TestClient(app)

    # Step 3: Verify if the new provider is provisioned after reloading
    response = client.get("/providers", headers={"x-api-key": "someapikey"})
    assert response.status_code == 200
    providers = response.json()
    provisioned_providers = [
        p for p in providers.get("installed_providers") if p.get("provisioned")
    ]
    assert len(provisioned_providers) == 1
    assert provisioned_providers[0]["type"] == "prometheus"


@pytest.mark.parametrize(
    "test_app",
    [
        {
            "AUTH_TYPE": "NOAUTH",
            "KEEP_DASHBOARDS": '[{"dashboard_name":"My Dashboard","dashboard_config":{"layout":[{"i":"w-1728223503577","x":0,"y":0,"w":3,"h":3,"minW":2,"minH":2,"static":false}],"widget_data":[{"i":"w-1728223503577","x":0,"y":0,"w":3,"h":3,"minW":2,"minH":2,"static":false,"thresholds":[{"value":0,"color":"#22c55e"},{"value":20,"color":"#ef4444"}],"preset":{"id":"11111111-1111-1111-1111-111111111111","name":"feed","options":[{"label":"CEL","value":"(!deleted && !dismissed)"},{"label":"SQL","value":{"sql":"(deleted=false AND dismissed=false)","params":{}}}],"created_by":null,"is_private":false,"is_noisy":false,"should_do_noise_now":false,"alerts_count":98,"static":true,"tags":[]},"name":"Test"}]}}]',
        },
    ],
    indirect=True,
)
def test_provision_dashboard(monkeypatch, db_session, client, test_app):
    response = client.get("/dashboard", headers={"x-api-key": "someapikey"})
    assert response.status_code == 200
    dashboards = response.json()
    assert len(dashboards) == 1
    assert dashboards[0]["dashboard_name"] == "My Dashboard"


@pytest.mark.parametrize(
    "test_app",
    [
        {
            "AUTH_TYPE": "NOAUTH",
            "KEEP_DASHBOARDS": '{"dashboard_name": "a"}]',
        },
    ],
    indirect=True,
)
def test_provision_dashboard_invalid_json(monkeypatch, db_session, client, test_app):
    response = client.get("/dashboard", headers={"x-api-key": "someapikey"})
    assert response.status_code == 200
    dashboards = response.json()
    assert len(dashboards) == 0


@pytest.mark.parametrize(
    "test_app",
    [
        {
            "AUTH_TYPE": "NOAUTH",
            "KEEP_DASHBOARDS": '[{"dashboard_name":"Initial Dashboard","dashboard_config":{"layout":[{"i":"w-1728223503577","x":0,"y":0,"w":3,"h":3,"minW":2,"minH":2,"static":false}],"widget_data":[{"i":"w-1728223503577","x":0,"y":0,"w":3,"h":3,"minW":2,"minH":2,"static":false,"thresholds":[{"value":0,"color":"#22c55e"},{"value":20,"color":"#ef4444"}],"preset":{"id":"11111111-1111-1111-1111-111111111111","name":"feed","options":[{"label":"CEL","value":"(!deleted && !dismissed)"},{"label":"SQL","value":{"sql":"(deleted=false AND dismissed=false)","params":{}}}],"created_by":null,"is_private":false,"is_noisy":false,"should_do_noise_now":false,"alerts_count":98,"static":true,"tags":[]},"name":"Test"}]}}]',
        },
    ],
    indirect=True,
)
def test_reprovision_dashboard(monkeypatch, db_session, client, test_app):
    response = client.get("/dashboard", headers={"x-api-key": "someapikey"})
    assert response.status_code == 200
    dashboards = response.json()
    assert len(dashboards) == 1
    assert dashboards[0]["dashboard_name"] == "Initial Dashboard"

    # Step 2: Change environment variables (simulating new provisioning)
    monkeypatch.setenv(
        "KEEP_DASHBOARDS",
        '[{"dashboard_name":"New Dashboard","dashboard_config":{"layout":[{"i":"w-1728223503578","x":0,"y":0,"w":3,"h":3,"minW":2,"minH":2,"static":false}],"widget_data":[{"i":"w-1728223503578","x":0,"y":0,"w":3,"h":3,"minW":2,"minH":2,"static":false,"thresholds":[{"value":0,"color":"#22c55e"},{"value":20,"color":"#ef4444"}],"preset":{"id":"11111111-1111-1111-1111-111111111112","name":"feed","options":[{"label":"CEL","value":"(!deleted && !dismissed)"},{"label":"SQL","value":{"sql":"(deleted=false AND dismissed=false)","params":{}}}],"created_by":null,"is_private":false,"is_noisy":false,"should_do_noise_now":false,"alerts_count":98,"static":true,"tags":[]},"name":"Test"}]}}]',
    )

    # Reload the app to apply the new environment changes
    importlib.reload(sys.modules["keep.api.api"])

    # Reinitialize the TestClient with the new app instance
    from keep.api.api import get_app

    app = get_app()

    # Manually trigger the startup event
    for event_handler in app.router.on_startup:
        asyncio.run(event_handler())

    # manually trigger the provision resources
    from keep.api.config import provision_resources

    provision_resources()

    client = TestClient(app)

    # Step 3: Verify if the new dashboard is provisioned after reloading
    response = client.get("/dashboard", headers={"x-api-key": "someapikey"})
    assert response.status_code == 200
    dashboards = response.json()
    assert len(dashboards) == 2
    assert dashboards[1]["dashboard_name"] == "New Dashboard"


@pytest.mark.parametrize(
    "test_app",
    [
        {
            "AUTH_TYPE": "NOAUTH",
            "KEEP_PROVIDERS": json.dumps(
                {
                    "keepVictoriaMetrics": VICTORIA_METRICS_PROVIDER,
                }
            ),
        },
    ],
    indirect=True,
)
def test_provision_provider_with_empty_tenant_table(db_session, client, test_app):
    """Test that provider provisioning fails when tenant table is empty with foreign key constraints enabled"""
    # Delete all entries from tenant table
    db_session.execute(text("DELETE FROM tenant"))
    db_session.commit()

    # Enable SQLite foreign keys
    db_session.execute(text("PRAGMA foreign_keys = ON;"))
    result = db_session.execute(text("PRAGMA foreign_keys;")).fetchone()
    assert result is not None and result[0] == 1, "Foreign keys not enabled"

    # Verify tenant table is empty
    tenant_count = db_session.execute(text("SELECT COUNT(*) FROM tenant")).fetchone()[0]
    assert tenant_count == 0, "Tenant table should be empty"

    # Import ProvidersService
    from keep.api.core.dependencies import SINGLE_TENANT_UUID
    from keep.providers.providers_service import ProvidersService

    # Call install_provider directly instead of provision_providers_from_env
    # This bypasses the exception handling in provision_providers_from_env
    with pytest.raises(Exception) as excinfo:
        ProvidersService.install_provider(
            tenant_id=SINGLE_TENANT_UUID,
            installed_by="system",
            provider_id="victoriametrics123",
            provider_name="keepVictoriaMetrics123",
            provider_type="victoriametrics",
            provider_config={"VMAlertHost": "http://localhost", "VMAlertPort": 1234},
            provisioned=True,
            validate_scopes=False,
        )

    # Verify that the error message is related to foreign key constraint violation
    error_msg = str(excinfo.value).lower()
    assert (
        "foreign key constraint" in error_msg
        or "FOREIGN KEY constraint failed" in str(excinfo.value)
        or "violates foreign key constraint" in error_msg
    )

    db_session.execute(text("PRAGMA foreign_keys = OFF;"))
