import logging
import sys
from pathlib import Path

import click

from architecture_diagrams.orchestrator.build import build_workspace


@click.command()
@click.option(
    "--output", default="workspace.dsl", help="Output DSL filename [default=workspace.dsl]"
)
@click.option(
    "--project", default="banking", help="Project key under projects/* (default: banking)"
)
@click.option(
    "--project-path",
    default=None,
    help="Path to an external project directory containing 'models' and 'views' folders (overrides --project)",
)
@click.option("--views", default=None, help="Comma-separated view keys/names to include")
@click.option("--tags", "tags_", default=None, help="Comma-separated view tags to include")
@click.option(
    "--modules",
    "modules_",
    default=None,
    help="Comma-separated module keys (e.g., care-journeys, assess) derived from view subjects",
)
@click.option(
    "--prune-to-views",
    is_flag=True,
    default=False,
    help="Prune model to elements reachable from selected views",
)
@click.option(
    "--exporter", default="structurizr", help="Exporter to use: structurizr (default) or json"
)
@click.option(
    "--tagging",
    default=None,
    help="Comma-separated tagging strategies to apply (e.g., auto_external)",
)
@click.option(
    "--view-generator",
    default=None,
    help="Name of a view generator plugin to run (e.g., delta_lineage)",
)
@click.option(
    "--view-generator-config", default=None, help="JSON string with config for the view generator"
)
@click.option(
    "--enable-cache/--no-cache", default=False, help="Enable output caching based on inputs"
)
@click.option(
    "--verbose", is_flag=True, default=False, help="Enable verbose logging for troubleshooting"
)
def generate(
    output: str,
    project: str | None,
    project_path: str | None,
    views: str | None,
    tags_: str | None,
    modules_: str | None,
    prune_to_views: bool,
    exporter: str,
    tagging: str | None,
    view_generator: str | None,
    view_generator_config: str | None,
    enable_cache: bool,
    verbose: bool,
) -> None:
    """Generate a workspace.dsl from composed models and independent views."""
    # Setup logging early
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(stream=sys.stderr, level=level, format="%(levelname)s: %(message)s")
    log = logging.getLogger("architecture-diagrams.generate")

    names = [v.strip() for v in views.split(",")] if views else []
    tags = [t.strip() for t in tags_.split(",")] if tags_ else []
    modules = [m.strip() for m in modules_.split(",")] if modules_ else []
    # Workspace name defaults to project key; override via project manifest if present
    workspace_name = project if project else "banking"
    pp = Path(project_path) if project_path else None
    tag_strategies = [t.strip() for t in tagging.split(",")] if tagging else []
    try:
        log.debug(
            "Generating DSL with params: output=%s, project=%s, project_path=%s, views=%s, tags=%s, modules=%s, prune_to_views=%s",
            output,
            project,
            str(pp) if pp else None,
            names,
            tags,
            modules,
            prune_to_views,
        )
        vg_cfg = None
        if view_generator_config:
            import json as _json

            try:
                vg_cfg = _json.loads(view_generator_config)
            except Exception:
                log.warning("Invalid JSON passed to --view-generator-config; ignoring")
        dsl = build_workspace(
            project=project,
            project_path=pp,
            workspace_name=workspace_name,
            select_names=names,
            select_tags=tags,
            select_modules=modules,
            prune_to_views=prune_to_views,
            exporter=exporter,
            tagging=tag_strategies,
            view_generator=view_generator,
            view_generator_config=vg_cfg,
            enable_cache=enable_cache,
        )
    except FileNotFoundError as e:
        log.error("Configuration or project files not found: %s", e)
        sys.exit(2)
    except Exception as e:
        log.error("Generation failed: %s", e)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)
    out_path = Path(output)
    # Create parent directory if using a nested output path
    if out_path.parent and str(out_path.parent) not in ("", "."):
        out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with out_path.open("w") as fh:
            fh.write(dsl)
    except Exception as e:
        log.error("Failed to write output to %s: %s", out_path, e)
        sys.exit(3)
    click.echo(f"Wrote {output} (exporter={exporter})")
