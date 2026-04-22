from unittest.mock import MagicMock, patch
import pytest
import docker.errors

import pokebenchmark_platform.orchestrator.container_manager as cm_module
from pokebenchmark_platform.orchestrator.container_manager import ContainerManager


@pytest.fixture
def mock_docker():
    with patch("pokebenchmark_platform.orchestrator.container_manager.docker") as mock:
        mock_client = MagicMock()
        mock.from_env.return_value = mock_client
        mock.errors.NotFound = docker.errors.NotFound
        yield mock, mock_client


def test_init(mock_docker):
    _, mock_client = mock_docker
    manager = ContainerManager(image_name="myimage:v1")
    assert manager.image_name == "myimage:v1"
    assert manager.client is mock_client


def test_launch_session(mock_docker):
    _, mock_client = mock_docker
    mock_container = MagicMock()
    mock_container.id = "abc123"
    mock_client.containers.run.return_value = mock_container

    manager = ContainerManager()
    result = manager.launch_session(
        run_id="run1",
        game="pokemon_red",
        rom_path="/roms/red.gba",
        model_provider="openai",
        model_name="gpt-4",
        api_key="sk-test",
        orchestrator_url="http://localhost:8000",
        extra_env={"EXTRA": "value"},
    )

    mock_client.containers.run.assert_called_once_with(
        manager.image_name,
        name="pokebenchmark-run1",
        environment={
            "GAME": "pokemon_red",
            "MODEL_PROVIDER": "openai",
            "MODEL_NAME": "gpt-4",
            "INPUT_MODE": "vision",
            "RUN_ID": "run1",
            "API_KEY": "sk-test",
            "ORCHESTRATOR_URL": "http://localhost:8000",
            "EXTRA": "value",
        },
        volumes={"/roms/red.gba": {"bind": "/app/rom.gba", "mode": "ro"}},
        detach=True,
        auto_remove=False,
    )
    assert result == "abc123"


def test_stop_session(mock_docker):
    _, mock_client = mock_docker
    mock_container = MagicMock()
    mock_client.containers.get.return_value = mock_container

    manager = ContainerManager()
    manager.stop_session("abc123")

    mock_client.containers.get.assert_called_once_with("abc123")
    mock_container.stop.assert_called_once_with(timeout=10)


def test_get_session_status_running(mock_docker):
    _, mock_client = mock_docker
    mock_container = MagicMock()
    mock_container.status = "running"
    mock_client.containers.get.return_value = mock_container

    manager = ContainerManager()
    status = manager.get_session_status("abc123")

    assert status == "running"


def test_get_session_status_not_found(mock_docker):
    _, mock_client = mock_docker
    mock_client.containers.get.side_effect = docker.errors.NotFound("not found")

    manager = ContainerManager()
    status = manager.get_session_status("missing")

    assert status == "not_found"


def test_list_sessions(mock_docker):
    _, mock_client = mock_docker
    c1 = MagicMock()
    c1.id = "id1"
    c1.name = "pokebenchmark-run1"
    c1.status = "running"
    c2 = MagicMock()
    c2.id = "id2"
    c2.name = "pokebenchmark-run2"
    c2.status = "exited"
    mock_client.containers.list.return_value = [c1, c2]

    manager = ContainerManager()
    sessions = manager.list_sessions()

    mock_client.containers.list.assert_called_once_with(all=True, filters={"name": "pokebenchmark-"})
    assert sessions == [
        {"id": "id1", "name": "pokebenchmark-run1", "status": "running"},
        {"id": "id2", "name": "pokebenchmark-run2", "status": "exited"},
    ]
