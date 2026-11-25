"""Gradio interface compositor for NEOEX.

Presentation assets live in neoex/assets/ and each laboratory tab resides in
neoex/tabs/. Helper symbols are re-exported here for backwards compatibility.
"""
from __future__ import annotations

import html
from pathlib import Path
from urllib.parse import quote as _url_quote

import gradio as gr

from . import __version__
from .latex_plain import latex_fragment_to_plain_text as _latex_fragment_to_plain_text
from .tabs import (
    build_algebra_tab,
    build_exercises_tab,
    build_graphs_tab,
    build_properties_tab,
)
from .tabs.algebra_tab import (
    _algebra_preview,
    _domain_preview_html,
    _explanation_html,
    _steps_markdown,
    _steps_stack_html,
)
from .tabs.exercises_tab import (
    _exercise_prompt,
    _exercise_radio_choices,
    _exercise_solution_html,
    _pretty_exercise_choice,
    _pretty_exercise_text,
)
from .tabs.graphs_tab import (
    GRAPH_HTML_JS_ON_LOAD,
    _analysis_markdown,
    _graph_preview,
    _live_graph_html,
    _pt_number,
    _render_graph,
    _render_parameter_graph,
    _safe_payload_json,
)
from .tabs.properties_tab import (
    _animate_formula_markup,
    _power_of_power_visual,
    _prop_stage_html,
    _prop_text,
    _property_header,
)

_PACKAGE_DIR = Path(__file__).resolve().parent
_ASSETS_DIR = _PACKAGE_DIR / "assets"

CSS = (_ASSETS_DIR / "styles.css").read_text(encoding="utf-8")

MATHJAX_BUNDLE = _ASSETS_DIR / "mathjax" / "tex-svg-full.js"
MATHJAX_ASSET_DIR = MATHJAX_BUNDLE.parent.resolve()
MATHJAX_SCRIPT_URL = "/gradio_api/file=" + _url_quote(str(MATHJAX_BUNDLE.resolve()), safe="/:")

_MATHJAX_LOADER_JS = (_ASSETS_DIR / "mathjax_loader.js").read_text(encoding="utf-8")
_GRAPH_RUNTIME_JS = (_PACKAGE_DIR / "graph_runtime.js").read_text(encoding="utf-8")

MATHJAX_HEAD = f"""
<script>
window.MathJax = {{
  tex: {{ inlineMath: [['\\\\(','\\\\)'], ['$','$']], displayMath: [['\\\\[','\\\\]'], ['$$','$$']] }},
  options: {{ skipHtmlTags: ['script','noscript','style','textarea','pre','code'], enableMenu: false }},
  svg: {{ fontCache: 'global' }},
  startup: {{
    typeset: false,
    ready: function () {{
      MathJax.startup.defaultReady();
      window.__NEOEX_MATHJAX_READY__ = true;
      window.dispatchEvent(new Event('neoex-mathjax-ready'));
    }}
  }}
}};
</script>
<script defer src="{MATHJAX_SCRIPT_URL}" onerror="window.dispatchEvent(new Event('neoex-mathjax-failed'))"></script>
<script>
{_MATHJAX_LOADER_JS}
</script>
<script>
{_GRAPH_RUNTIME_JS}
</script>
"""


def build_app():
    """Assemble the complete NEOEX Gradio Blocks application."""
    with gr.Blocks(title="NEOEX — EXPONENCIAL LAB") as demo:
        gr.HTML("""<div id='neoex-header'><div class='neoex-kicker'>Laboratório matemático interativo</div><div class='neoex-logo'>NEO<span>EX</span></div><div class='neoex-sub'>EXPONENCIAL LAB</div><div class='neoex-by'>DESENVOLVIDO POR PH - Δ</div></div>""")
        with gr.Tabs():
            build_properties_tab()
            build_algebra_tab()
            build_graphs_tab()
            build_exercises_tab()
        gr.HTML(f"<div class='footer-neoex'>LABORATÓRIO INTERATIVO DE MATEMÁTICA · VERSÃO {html.escape(__version__)} · DESENVOLVIDO POR PH - Δ</div>")
    # Bound concurrency so multiple expensive graph requests cannot saturate
    # the Colab runtime or freeze the whole application queue.
    demo.queue(max_size=8, default_concurrency_limit=1)
    return demo


__all__ = [
    "CSS",
    "GRAPH_HTML_JS_ON_LOAD",
    "MATHJAX_ASSET_DIR",
    "MATHJAX_BUNDLE",
    "MATHJAX_HEAD",
    "_algebra_preview",
    "_analysis_markdown",
    "_animate_formula_markup",
    "_domain_preview_html",
    "_exercise_prompt",
    "_exercise_radio_choices",
    "_exercise_solution_html",
    "_explanation_html",
    "_graph_preview",
    "_latex_fragment_to_plain_text",
    "_live_graph_html",
    "_power_of_power_visual",
    "_pretty_exercise_choice",
    "_pretty_exercise_text",
    "_prop_stage_html",
    "_prop_text",
    "_property_header",
    "_pt_number",
    "_render_graph",
    "_render_parameter_graph",
    "_safe_payload_json",
    "_steps_markdown",
    "_steps_stack_html",
    "build_app",
]
