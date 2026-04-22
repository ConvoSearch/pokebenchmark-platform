import docker
import docker.errors

class ContainerManager:
    def __init__(self, image_name: str = "pokebenchmark:latest"):
        self.image_name = image_name
        self.client = docker.from_env()

    def launch_session(self, run_id, game, rom_path, model_provider, model_name,
                       api_key=None, input_mode="vision", save_state_path=None,
                       skill_files=None, orchestrator_url=None, extra_env=None) -> str:
        env = {"GAME": game, "MODEL_PROVIDER": model_provider, "MODEL_NAME": model_name,
               "INPUT_MODE": input_mode, "RUN_ID": run_id}
        if api_key: env["API_KEY"] = api_key
        if save_state_path: env["SAVE_STATE_PATH"] = save_state_path
        if orchestrator_url: env["ORCHESTRATOR_URL"] = orchestrator_url
        if extra_env: env.update(extra_env)
        volumes = {rom_path: {"bind": "/app/rom.gba", "mode": "ro"}}
        container = self.client.containers.run(self.image_name, name=f"pokebenchmark-{run_id}",
                                                environment=env, volumes=volumes, detach=True, auto_remove=False)
        return container.id

    def stop_session(self, container_id):
        self.client.containers.get(container_id).stop(timeout=10)

    def get_session_status(self, container_id) -> str:
        try:
            return self.client.containers.get(container_id).status
        except docker.errors.NotFound:
            return "not_found"

    def list_sessions(self) -> list[dict]:
        containers = self.client.containers.list(all=True, filters={"name": "pokebenchmark-"})
        return [{"id": c.id, "name": c.name, "status": c.status} for c in containers]

    def remove_session(self, container_id):
        try:
            self.client.containers.get(container_id).remove(force=True)
        except docker.errors.NotFound:
            pass
