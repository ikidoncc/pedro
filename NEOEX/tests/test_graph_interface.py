import base64
import json
import re
import unittest
from pathlib import Path

from neoex.graphs import build_graph_spec
from neoex.ui import MATHJAX_HEAD, _render_graph, _render_parameter_graph, build_app

ROOT = Path(__file__).resolve().parents[1]


class NeoexGraphInterfaceTests(unittest.TestCase):
    def test_canvas_is_lazy_and_loaded_from_component(self):
        app = build_app()
        config = app.get_config_file()
        components = [
            item for item in config["components"]
            if item.get("props", {}).get("elem_id") == "neoex-graph-output"
        ]
        self.assertEqual(len(components), 1)
        props = components[0]["props"]
        self.assertIn("NEOEX_attachGraphHost", props.get("js_on_load", ""))
        self.assertIn("neoex-graph-placeholder", props.get("value", ""))
        self.assertNotIn("data-neoex-graph", props.get("value", ""))

    def test_mathjax_is_bundled_locally_and_graph_uses_safe_unicode(self):
        from neoex.ui import MATHJAX_ASSET_DIR, MATHJAX_BUNDLE
        self.assertTrue(MATHJAX_BUNDLE.is_file())
        self.assertIn("/gradio_api/file=", MATHJAX_HEAD)
        self.assertNotIn("cdn.jsdelivr.net", MATHJAX_HEAD)
        self.assertIn("neoex-mathjax-ready", MATHJAX_HEAD)
        self.assertIn("data-neoex-tex-fallback", MATHJAX_HEAD)
        self.assertTrue(MATHJAX_ASSET_DIR.is_dir())
        markup, analysis, _ = _render_graph("2^x + 8x^2", "")
        self.assertIn("neoex-canvas-math", markup)
        self.assertIn("neoex-canvas-domain-math", markup)
        self.assertIn("g(x) =", markup)
        self.assertIn("Dₓ=ℝ", markup)
        self.assertIn("g(x) = 2ˣ + 8 x²", analysis)
        self.assertIn("ℝ", analysis)
        self.assertNotIn(r"\(", markup)
        self.assertNotIn(r"\)", markup)
        self.assertNotIn(r"\(", analysis)
        self.assertNotIn(r"\frac", analysis)

    def test_graph_runtime_reinitializes_changed_config_and_cleans_listeners(self):
        runtime = (ROOT / "neoex" / "graph_runtime.js").read_text(encoding="utf-8")
        self.assertIn("current.configText === configText", runtime)
        self.assertIn("attributeFilter: ['data-config']", runtime)
        self.assertIn("subtree: true", runtime)
        self.assertIn("listenerController.abort()", runtime)
        self.assertIn("configText,", runtime)

    def test_graph_contains_geogebra_like_controls(self):
        markup, analysis, state = _render_graph("x^2-4", "", 1.5, -8, 8)
        for role in (
            "graph-canvas", "point-slider", "current-x", "line-slider", "line-y",
            "roots-toggle", "line-toggle", "axis-xmin", "axis-xmax", "apply-axes",
        ):
            self.assertIn(f'data-role="{role}"', markup)
        self.assertIn("RAÍZES NO INTERVALO", markup)
        self.assertIn("INTERSEÇÕES COM A RETA HORIZONTAL", markup)
        self.assertIn("analysis-grid", analysis)
        self.assertEqual(state["x_point"], 1.5)

    def test_safe_payload_never_contains_raw_function_as_executable_code(self):
        markup, _, _ = _render_graph("(2^2x + 3x^x)/4x^2", "", 1.2, -8, 8)
        match = re.search(r'data-config="([^"]+)"', markup)
        self.assertIsNotNone(match)
        payload = json.loads(base64.b64decode(match.group(1)).decode("utf-8"))
        self.assertIn("function_js", payload)
        self.assertNotIn("(2^2x + 3x^x)/4x^2", payload["function_js"])
        self.assertIn("Math.pow(x, x)", payload["function_js"])
        self.assertEqual(payload["expression_plain"], "(2^2x + 3x^x)/4x^2")
        self.assertFalse(payload["constant_function"])
        json.dumps(payload, allow_nan=False)

    def test_canvas_runtime_has_no_plotly_or_busy_polling(self):
        runtime = (ROOT / "neoex" / "graph_runtime.js").read_text(encoding="utf-8")
        self.assertNotIn("Plotly", runtime)
        self.assertNotIn("setInterval", runtime)
        self.assertIn("requestAnimationFrame", runtime)
        self.assertIn("ResizeObserver", runtime)
        self.assertIn("computeIntersections", runtime)
        self.assertIn("pointerdown", runtime)
        self.assertIn("listen(canvas, 'wheel'", runtime)
        self.assertIn("state.resamplePending = true", runtime)
        self.assertIn("requestAnimationFrame(() => {", runtime)
        self.assertIn("(?<![A-Za-z])x(?![A-Za-z])", runtime)

    def test_no_plotly_dependency_or_large_vendor_bundle(self):
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
        self.assertNotIn("plotly", requirements)
        self.assertFalse((ROOT / "assets" / "plotly.min.js").exists())
        self.assertNotIn("plotly", MATHJAX_HEAD.lower())

    def test_graph_functions_and_roots(self):
        cases = [
            ("x^2-4", 2),
            ("x^3-x", 3),
            ("1/x", 0),
            ("sqrt(x)", 0),
            ("log(x)", 1),
            ("x^x", 0),
            ("(2^2x + 3x^x)/4x^2", 0),
        ]
        for expression, expected_min_roots in cases:
            with self.subTest(expression=expression):
                spec = build_graph_spec(expression)
                self.assertIn("function_js", spec)
                self.assertIsInstance(spec["roots"], list)
                if expression in ("x^2-4", "x^3-x"):
                    self.assertEqual(len(spec["roots"]), expected_min_roots)

    def test_graph_display_never_exposes_raw_tex(self):
        expressions = ["2^x+8x^2", "x^2-4", "(x^2+1)/(x-1)", "sqrt(x)", "log(x)"]
        for expression in expressions:
            with self.subTest(expression=expression):
                markup, analysis, _ = _render_graph(expression, "")
                self.assertNotIn(r"\(", markup)
                self.assertNotIn(r"\)", markup)
                self.assertNotIn(r"\frac", markup)
                self.assertNotIn(r"\mathbb", markup)
                self.assertNotIn(r"\(", analysis)
                self.assertNotIn(r"\)", analysis)
                self.assertIn("neoex-plain-math", markup)
                self.assertIn("analysis-math-text", analysis)
                from neoex.ui import _graph_preview
                preview = _graph_preview(expression)
                self.assertNotIn(r"\(", preview)
                self.assertNotIn(r"\frac", preview)

    def test_graph_runtime_observes_new_gradio_html_shells(self):
        runtime = (ROOT / "neoex" / "graph_runtime.js").read_text(encoding="utf-8")
        self.assertIn("startGlobalGraphObserver", runtime)
        self.assertIn("window.__NEOEX_GRAPH_OBSERVER__", runtime)
        self.assertIn("shellsWithin(document.body).forEach(initialize)", runtime)
        self.assertIn("record.addedNodes.forEach", runtime)
        self.assertIn("attributeFilter: ['data-config']", runtime)
        self.assertIn("window.dispatchEvent(new Event('neoex-runtime-ready'))", runtime)

    def test_graph_expression_change_and_submit_events_are_registered(self):
        app = build_app()
        dependencies = app.get_config_file()["dependencies"]
        triggers = [dep.get("targets", [None])[0] for dep in dependencies]
        # At least one textbox input-change handler and one textbox submit handler
        # must be present; the generate button remains a separate explicit action.
        event_targets = {event for dep in dependencies for _component, event in dep.get("targets", [])}
        self.assertIn("change", event_targets)
        self.assertIn("submit", event_targets)
        self.assertIn("click", event_targets)
        graph_input_component = next(
            item for item in app.get_config_file()["components"]
            if item.get("props", {}).get("label") == "g(x) ="
        )
        graph_input_id = graph_input_component["id"]
        self.assertTrue(any(dep.get("targets") == [(graph_input_id, "change")] for dep in dependencies))
        self.assertTrue(any(dep.get("targets") == [(graph_input_id, "submit")] for dep in dependencies))

    def test_constant_function_reports_coincident_horizontal_line(self):
        markup, _, _ = _render_graph("5", "", 2.0, -8, 8)
        payload_match = re.search(r'data-config="([^"]+)"', markup)
        payload = json.loads(base64.b64decode(payload_match.group(1)).decode("utf-8"))
        self.assertTrue(payload["constant_function"])
        self.assertEqual(payload["constant_value"], 5.0)
        runtime = (ROOT / "neoex" / "graph_runtime.js").read_text(encoding="utf-8")
        self.assertIn("intersectionAll", runtime)
        self.assertIn("infinitos pontos de interseção", runtime)


    def test_canvas_keeps_responsive_width_after_hidden_tab_reopens(self):
        runtime = (ROOT / "neoex" / "graph_runtime.js").read_text(encoding="utf-8")
        # The backing bitmap may change, but the CSS layout width must remain 100%.
        self.assertIn("canvas.style.removeProperty('width')", runtime)
        self.assertIn("canvas.style.removeProperty('height')", runtime)
        self.assertNotIn("canvas.style.width = w + 'px'", runtime)
        self.assertNotIn("canvas.style.height = h + 'px'", runtime)
        self.assertIn("const w = Math.floor(rect.width)", runtime)
        self.assertIn("state.waitingForLayout = true", runtime)
        self.assertIn("new ResizeObserver(resizeCanvas)", runtime)
        self.assertIn("new IntersectionObserver", runtime)
        self.assertIn("resizeObserver.observe(shell)", runtime)
        self.assertIn("listen(window, 'resize', resizeCanvas", runtime)
        self.assertIn("state.intersectionObserver.disconnect()", runtime)


    def test_live_exponent_substitution_uses_semantic_superscript_elements(self):
        runtime = (ROOT / "neoex" / "graph_runtime.js").read_text(encoding="utf-8")
        from neoex.ui import CSS, _latex_fragment_to_plain_text
        self.assertIn("function appendSubstitutedExpression(target, value)", runtime)
        self.assertIn("document.createElement('sup')", runtime)
        self.assertIn("sup.textContent = exponent", runtime)
        self.assertIn("readoutY.replaceChildren()", runtime)
        self.assertIn(".neoex-canvas-readout .readout-y sup", CSS)
        # A symbolic x exponent remains a genuine raised x in the function card.
        self.assertEqual(_latex_fragment_to_plain_text(r"4^{x}"), "4ˣ")

    def test_decimal_exponents_use_semantic_superscripts_in_live_readout(self):
        runtime = (ROOT / "neoex" / "graph_runtime.js").read_text(encoding="utf-8")
        self.assertIn("source.slice(nextIndex + 1, end)", runtime)
        self.assertIn("sup.textContent = exponent", runtime)
        self.assertIn("source.replace(/(?<![A-Za-z])x(?![A-Za-z])/g, xValue)", runtime)
        self.assertIn("(4,429)", runtime) if "(4,429)" in runtime else self.assertIn("fmt(value)", runtime)

    def test_parameter_graph_uses_canvas(self):
        markup, analysis, state = _render_parameter_graph(1, 2, 0, 0, 2)
        self.assertIn("neoex-canvas-shell", markup)
        self.assertIn('data-role="graph-canvas"', markup)
        self.assertIn("Assíntota horizontal", analysis)
        self.assertEqual(state["mode"], "parameter")


if __name__ == "__main__":
    unittest.main()
