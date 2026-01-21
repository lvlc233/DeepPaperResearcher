from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from base.pg.entity import User
from controller.api.app import app
from controller.api.auth.router import get_current_user
from controller.api.settings.settings_router import get_setting_service
from controller.api.settings.schema import (
    AISearchSettingsRequest,
    AISearchSettingsResponse,
    SystemSettingsRequest,
    SystemSettingsResponse,
)
from service.setting.setting_service import SettingService

from service.setting.schema import Settings, SystemSettings

@pytest.mark.asyncio
async def test_setting_service_update_system_settings():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    mock_user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="pw",
        settings=Settings(system_settings=SystemSettings(system_colour="light")),
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    session.execute = AsyncMock(return_value=mock_result)

    service = SettingService(session)
    result = await service.update_system_settings(
        mock_user.id,
        SystemSettingsRequest(system_colour="dark"),
    )

    assert result.system_colour == "dark"
    assert mock_user.settings.system_settings.system_colour == "dark"
    session.add.assert_called()
    session.commit.assert_called()


@pytest.fixture
def mock_user_obj():
    return User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="pw",
        settings=Settings(),
    )


@pytest.fixture
def client(mock_user_obj):
    async def mock_get_current_user():
        return mock_user_obj

    async def mock_get_setting_service():
        mock_service = MagicMock(spec=SettingService)
        mock_service.get_system_settings = AsyncMock(
            return_value=SystemSettingsResponse(system_colour="light")
        )
        mock_service.update_system_settings = AsyncMock(
            return_value=SystemSettingsResponse(system_colour="dark")
        )
        mock_service.get_ai_search_settings = AsyncMock(
            return_value=AISearchSettingsResponse(
                llm_name="gpt",
                provider="openai",
                api_key="****",
                base_url="https://api.test",
                search_limit=10,
                search_loop=3,
                ai_summary_enable=True,
                search_deep="standard",
                search_preferences="mixed",
                search_date_max=date.today(),
                search_date_min=date.today(),
            )
        )
        mock_service.update_ai_search_settings = AsyncMock(
            return_value=mock_service.get_ai_search_settings.return_value
        )
        return mock_service

    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_setting_service] = mock_get_setting_service

    yield TestClient(app)

    app.dependency_overrides.clear()


def test_get_system_settings_api(client):
    response = client.get("/api/v1/settings/system")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["system_colour"] == "light"


def test_update_system_settings_api(client):
    response = client.put(
        "/api/v1/settings/system",
        json={"system_colour": "dark"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["system_colour"] == "dark"


def test_update_ai_search_settings_api(client):
    payload = AISearchSettingsRequest(
        llm_name="gpt",
        provider="openai",
        api_key="sk-test",
        base_url="https://api.test",
        search_limit=10,
        search_loop=3,
        ai_summary_enable=True,
        search_deep="standard",
        search_preferences="mixed",
        search_date_max=date.today(),
        search_date_min=date.today(),
    ).model_dump(mode="json")

    response = client.put("/api/v1/settings/search/ai", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["provider"] == "openai"
