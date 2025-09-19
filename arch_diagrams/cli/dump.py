import click
import os

from typing import Optional, Iterable

from arch_diagrams.orchestrator.build import build_workspace_dsl


@click.command()
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--filename",
    default="workspace.dsl",
    help="Workspace Filename [default=workspace.dsl]",
)
@click.option(
    "--views_filter_tag",
    default=None,
    help="Tag to filter the views by ('default', 'td') [default=None]",
)
@click.option(
    "--project",
    default="banking",
    help="Project to generate (default: banking)",
)
def dump(
    path: click.Path,
    filename: str,
    views_filter_tag: Optional[str] = None,
    project: Optional[str] = None,
) -> None:
    """Dumps the architecture diagram DSL using the orchestrator."""
    file_path = os.path.join(os.path.abspath(str(path)), filename)
    print(f"Dumping workspace into: '{file_path}' ...")

    select_tags: Iterable[str] = [views_filter_tag] if views_filter_tag else []
    dsl = build_workspace_dsl(
        project=project,
        select_tags=select_tags,
    )

    with open(file_path, "w") as file:
        file.write(dsl)

    print("Done")
