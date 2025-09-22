import click

from architecture_diagrams.cli.dump import dump
from architecture_diagrams.cli.lite import lite
from architecture_diagrams.cli import generate as generate_cmd
from architecture_diagrams.cli.list_views import list_views
from architecture_diagrams.cli.list_modules import list_modules


@click.group()
def cli() -> None:
    """Architecture diagram CLI (C4 -> Structurizr DSL)"""
    pass


cli.add_command(dump)
cli.add_command(lite)
cli.add_command(generate_cmd.generate)
cli.add_command(list_views)
cli.add_command(list_modules)

if __name__ == "__main__":
    cli()
