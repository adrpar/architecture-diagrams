from pathlib import Path

import click

from architecture_diagrams.orchestrator.loader import discover_view_specs


@click.command()
@click.option(
    "--project", default="banking", help="Project key under projects/* (default: banking)"
)
@click.option(
    "--project-path",
    default=None,
    help="Path to an external project directory or a 'projects' folder (optional)",
)
def list_modules(project: str, project_path: str | None) -> None:
    """List available module keys inferred from view subjects (SYSTEM_KEY)."""
    root = Path(__file__).resolve().parents[2]
    extra_dirs: list[Path] = []
    if project_path:
        pp = Path(project_path).resolve()
        if (pp / "views").exists():
            extra_dirs.append(pp / "views")
        elif project and (pp / project / "views").exists():
            extra_dirs.append(pp / project / "views")
        elif project and (pp / "projects" / project / "views").exists():
            extra_dirs.append(pp / "projects" / project / "views")
        else:
            candidates: list[Path] = []
            if pp.name == "projects" and pp.is_dir():
                for sub in pp.iterdir():
                    v = sub / "views"
                    if v.exists():
                        candidates.append(v)
            proj_root = pp / "projects"
            if not candidates and proj_root.exists() and proj_root.is_dir():
                for sub in proj_root.iterdir():
                    v = sub / "views"
                    if v.exists():
                        candidates.append(v)
            if candidates:
                extra_dirs.extend(candidates)
    if extra_dirs:
        specs = discover_view_specs(root, extra_dirs=extra_dirs)
    else:
        specs = discover_view_specs(root, project=project)
    modules: set[str] = set()
    for spec in specs:
        if spec.subject:
            modules.add(spec.subject.split("/", 1)[0])
    for m in sorted(modules):
        click.echo(m)
