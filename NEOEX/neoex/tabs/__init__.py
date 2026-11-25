"""Tab builders for the NEOEX Gradio interface."""
from .properties_tab import build_properties_tab
from .algebra_tab import build_algebra_tab
from .graphs_tab import build_graphs_tab
from .exercises_tab import build_exercises_tab

__all__ = [
    "build_properties_tab",
    "build_algebra_tab",
    "build_graphs_tab",
    "build_exercises_tab",
]
