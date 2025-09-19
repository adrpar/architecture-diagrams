import click
from pathlib import Path

from arch_diagrams.orchestrator.loader import discover_view_specs


@click.command()
@click.option("--project", default="banking", help="Project key under projects/* (default: banking)")
def list_modules(project: str) -> None:
    """List available module keys inferred from view subjects (SYSTEM_KEY)."""
    root = Path(__file__).resolve().parents[2]
    specs = discover_view_specs(root, project=project)
    modules: set[str] = set()
    for spec in specs:
        if spec.subject:
            modules.add(spec.subject.split("/", 1)[0])
    for m in sorted(modules):
        click.echo(m)
