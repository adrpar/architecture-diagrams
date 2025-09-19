import click

from arch_diagrams.orchestrator.loader import discover_view_specs
from pathlib import Path


@click.command()
@click.option("--project", default="banking", help="Project key under projects/* (default: banking)")
@click.option("--filter-tag", "filter_tag", default=None, help="Filter by tag (optional)")
def list_views(project: str, filter_tag: str | None) -> None:
    """List discovered views and their tags."""
    root = Path(__file__).resolve().parents[2]
    specs = discover_view_specs(root, project=project)
    for spec in specs:
        if filter_tag and filter_tag not in spec.tags:
            continue
        tags = ",".join(sorted(spec.tags)) if spec.tags else "-"
        subj = f" subject={spec.subject}" if spec.subject else ""
        smart = " smart" if getattr(spec, "smart", False) else ""
        click.echo(f"{spec.key} [{spec.view_type}{smart}]{subj} :: {spec.name} :: tags={tags}")
