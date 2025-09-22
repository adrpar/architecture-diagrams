import click
import docker
import requests
import os
import time
import webbrowser

from typing import Any, Optional

from architecture_diagrams.orchestrator.build import build_workspace_dsl


_STRUCTURIZR_LITE_IMAGE_NAME = "structurizr/lite"
_CONTAINER_NAME = "structurizr-lite-architecture-diagrams"


@click.group()
def lite() -> None:
    """Niceties around Structurizr lite"""
    pass


@lite.command()
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--filename",
    default="workspace.dsl",
    help="Workspace Filename [default=workspace.dsl]",
)
@click.option(
    "--port",
    default=8080,
    help="Port to bind structurizr lite to [default=8080]",
)
@click.option(
    "--views",
    default=None,
    help="Comma-separated view keys/names to include (optional)",
)
@click.option(
    "--tags",
    "tags_",
    default=None,
    help="Comma-separated view tags to include (optional)",
)
@click.option(
    "--modules",
    "modules_",
    default=None,
    help="Comma-separated module keys (e.g., care-journeys, assess) derived from view subjects (optional)",
)
def start(path: click.Path, filename: str, port: int, views: Optional[str], tags_: Optional[str], modules_: Optional[str]) -> None:
    """Starts structurizr lite. If --views/--tags are provided, generate DSL on the fly."""
    absolute_path = os.path.abspath(str(path))
    if views or tags_ or modules_:
        names = [v.strip() for v in (views.split(",") if views else []) if v.strip()]
        tag_list = [t.strip() for t in (tags_.split(",") if tags_ else []) if t.strip()]
        module_list = [m.strip() for m in (modules_.split(",") if modules_ else []) if m.strip()]
        # IMPORTANT: On macOS, Docker Desktop cannot mount temporary system paths like /var/folders.
        # So we materialize the generated DSL into a project-local directory that Docker can mount.
        generated_dir = os.path.join(absolute_path, ".structurizr")
        os.makedirs(generated_dir, exist_ok=True)
        dsl = build_workspace_dsl(select_names=names, select_tags=tag_list, select_modules=module_list)
        out_file = os.path.join(generated_dir, filename)
        with open(out_file, "w") as fh:
            fh.write(dsl)
        print(
            f"Starting structurizr lite with generated workspace '{out_file}' (mounted from '{generated_dir}') ..."
        )
        start_structurizr_lite(generated_dir, port)
        if wait_for_container_url(f"http://localhost:{port}"):
            webbrowser.open(f"http://localhost:{port}")
        else:
            print("Structurizr lite seems to have failed on start.")
        return
    print(f"Starting structurizr lite with workspace '{absolute_path}' ...")
    start_structurizr_lite(absolute_path, port)

    if wait_for_container_url(f"http://localhost:{port}"):
        webbrowser.open(f"http://localhost:{port}")
    else:
        print("Structurizr lite seems to have failed on start.")


@lite.command()
def stop() -> None:
    """Stops this structurizr lite instance."""
    client = docker.from_env()

    print("Shutting down structurizr lite started with this CLI ...")
    clear_existing_container(client, _CONTAINER_NAME)


def start_structurizr_lite(file_path: str, port: int = 8080) -> None:
    """
    Starts the Structurizr Lite Docker container with the given file path and port.

    This function runs a `structurizr/lite` Docker container, mounts the specified
    file path as a volume, and binds the container's default port to the specified
    port on the host machine.

    :param file_path: The absolute path on the host to be mounted in the container.
                      This should point to the directory containing Structurizr files.
    :param port: The port on the host machine to map to the container's port 8080.
                 Defaults to 8080.
    :return: None
    """
    client = docker.from_env()

    clear_existing_container(client, _CONTAINER_NAME)

    try:
        client.containers.run(
            image=_STRUCTURIZR_LITE_IMAGE_NAME,
            name=_CONTAINER_NAME,
            ports={"8080/tcp": port},
            volumes={
                file_path: {
                    "bind": "/usr/local/structurizr",
                    "mode": "rw",
                }
            },
            detach=True,
        )
        print(f"Structurizr lite is running on port {port}")
    except docker.errors.DockerException as e:
        print(f"Docker error: {e}")


def clear_existing_container(client: Any, container_name: str) -> None:
    """
    Stops and removes an existing Docker container with the specified name, if it exists.

    This function checks if a container with the given name is running or stopped,
    and ensures it is removed before starting a new container. If the container does
    not exist, no action is taken.

    :param client: The Docker client object (typically created with `docker.from_env()`).
    :param container_name: The name of the container to stop and remove.
    :raises docker.errors.APIError: If there is an error stopping or removing the container.
    :return: None
    """
    try:
        existing_container = client.containers.get(container_name)
        print(f"Stopping and removing existing container: {container_name}")
        existing_container.stop()
        existing_container.remove()
    except docker.errors.NotFound:
        pass
    except docker.errors.APIError as exception:
        print(f"Error handling existing container: {exception}")


def wait_for_container_url(url: str, timeout: int = 60, interval: int = 2) -> bool:
    """
    Polls the given URL until it is reachable or timeout occurs.

    :param url: The URL to poll.
    :param timeout: Maximum time to wait (in seconds).
    :param interval: Time interval between each poll (in seconds).
    :return: True if the URL is reachable, False if timeout occurs.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print(f"URL '{url}' is reachable.")
                return True
        except requests.ConnectionError:
            print(f"URL '{url}' not reachable yet, retrying in {interval}s...")
        time.sleep(interval)

    print(f"Timeout reached. URL '{url}' is still not reachable.")
    return False
