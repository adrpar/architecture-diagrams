import click
import sys

from arch_diagrams.orchestrator.loader import discover_view_specs
from pathlib import Path


@click.command()
@click.option("--project", default="banking", help="Project key under projects/* (default: banking)")
@click.option("--project-path", default=None, help="Path to an external project directory or a 'projects' folder (optional)")
@click.option("--filter-tag", "filter_tag", default=None, help="Filter by tag (optional)")
@click.pass_context
def list_views(ctx: click.Context, project: str, project_path: str | None, filter_tag: str | None) -> None:
    """List discovered views and their tags."""
    root = Path(__file__).resolve().parents[2]
    extra_dirs: list[Path] = []
    if project_path:
        pp = Path(project_path).resolve()
        # Ensure 'projects' package is importable for external trees
        # Case 1: user passed a 'projects' directory => add its parent
        if pp.name == "projects" and str(pp.parent) not in sys.path:
            sys.path.insert(0, str(pp.parent))
        # Case 2: user passed a parent folder that contains 'projects' => add that folder
        elif (pp / "projects").exists() and str(pp) not in sys.path:
            sys.path.insert(0, str(pp))
        # Case 3: user passed a direct project folder => add parent of 'projects'
        elif (pp / "views").exists() and (pp.parent.name == "projects") and str(pp.parent.parent) not in sys.path:
            sys.path.insert(0, str(pp.parent.parent))
        # Direct project with views/
        if (pp / "views").exists():
            extra_dirs.append(pp / "views")
        else:
            # Determine if --project was explicitly provided
            project_explicit = False
            try:
                src = ctx.get_parameter_source("project")
                project_explicit = (str(src).lower().endswith("commandline"))
            except Exception:
                pass
            # If user explicitly provided --project, prefer that specific project's views under the provided path
            if project_explicit and project and (pp / project / "views").exists():
                extra_dirs.append(pp / project / "views")
            elif project_explicit and project and (pp / "projects" / project / "views").exists():
                extra_dirs.append(pp / "projects" / project / "views")
            else:
                # Aggregate across multiple projects under the provided path
                candidates: list[Path] = []
                # Case A: provided path is a 'projects' folder
                if pp.name == "projects" and pp.is_dir():
                    for sub in pp.iterdir():
                        v = sub / "views"
                        if v.exists():
                            candidates.append(v)
                # Case B: provided path has a 'projects' child
                proj_root = pp / "projects"
                if (not candidates) and proj_root.exists() and proj_root.is_dir():
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
    for spec in specs:
        if filter_tag and filter_tag not in spec.tags:
            continue
        tags = ",".join(sorted(spec.tags)) if spec.tags else "-"
        subj = f" subject={spec.subject}" if spec.subject else ""
        smart = " smart" if getattr(spec, "smart", False) else ""
        proj = getattr(spec, "project", None)
        proj_str = f" :: project={proj}" if proj else ""
        click.echo(f"{spec.key} [{spec.view_type}{smart}]{subj} :: {spec.name} :: tags={tags}{proj_str}")
