import click
from pathlib import Path

from arch_diagrams.orchestrator.build import build_workspace_dsl


@click.command()
@click.option("--output", default="workspace.dsl", help="Output DSL filename [default=workspace.dsl]")
@click.option("--project", default="banking", help="Project key under projects/* (default: banking)")
@click.option("--project-path", default=None, help="Path to an external project directory containing 'models' and 'views' folders (overrides --project)")
@click.option("--views", default=None, help="Comma-separated view keys/names to include")
@click.option("--tags", "tags_", default=None, help="Comma-separated view tags to include")
@click.option("--modules", "modules_", default=None, help="Comma-separated module keys (e.g., care-journeys, assess) derived from view subjects")
@click.option("--prune-to-views", is_flag=True, default=False, help="Prune model to elements reachable from selected views")
def generate(output: str, project: str | None, project_path: str | None, views: str | None, tags_: str | None, modules_: str | None, prune_to_views: bool) -> None:
    """Generate a workspace.dsl from composed models and independent views."""
    names = [v.strip() for v in views.split(",")] if views else []
    tags = [t.strip() for t in tags_.split(",")] if tags_ else []
    modules = [m.strip() for m in modules_.split(",")] if modules_ else []
    # Workspace name defaults to project key; override via project manifest if present
    workspace_name = project if project else "banking"
    pp = Path(project_path) if project_path else None
    dsl = build_workspace_dsl(project=project,
                              project_path=pp,
                              workspace_name=workspace_name,
                              select_names=names,
                              select_tags=tags,
                              select_modules=modules,
                              prune_to_views=prune_to_views)
    out_path = Path(output)
    # Create parent directory if using a nested output path
    if out_path.parent and str(out_path.parent) not in ("", "."):
        out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as fh:
        fh.write(dsl)
    click.echo(f"Wrote {output}")
