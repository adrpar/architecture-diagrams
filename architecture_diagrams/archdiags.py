import click

from architecture_diagrams.cli.dump import dump
from architecture_diagrams.cli import generate as generate_cmd
from architecture_diagrams.cli.list_views import list_views
from architecture_diagrams.cli.list_modules import list_modules

# Create the CLI group explicitly to keep type checkers happy
cli = click.Group(help="Architecture diagram CLI (C4 -> Structurizr DSL)")

# Core commands
cli.add_command(dump)
cli.add_command(generate_cmd.generate)
cli.add_command(list_views)
cli.add_command(list_modules)

# Lazily import optional commands that pull heavy or optional deps (e.g., docker)
try:
    from architecture_diagrams.cli.lite import lite as lite_cmd  # type: ignore
except Exception:
    lite_cmd = None  # type: ignore[assignment]

# Only register 'lite' if its optional dependency is available
if lite_cmd is not None:
    cli.add_command(lite_cmd)

if __name__ == "__main__":
    cli()
