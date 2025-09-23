"""Orchestrator public API.

This package provides utilities to compose models, discover independent view specs,
select by names/tags, and build a complete workspace DSL.
"""

from .build import build_workspace_dsl
from .loader import discover_model_builders, discover_view_specs
from .select import select_views
from .specs import Selector, ViewSpec

__all__ = [
    "build_workspace_dsl",
    "discover_model_builders",
    "discover_view_specs",
    "select_views",
    "ViewSpec",
    "Selector",
]
