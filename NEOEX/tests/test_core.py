import unittest
import sympy as sp
import re

from neoex.parser import parse_math, format_math_latex, ExpressionError
from neoex.properties import PROPERTIES
from neoex.algebra import build_algebra_steps
from neoex.graphs import build_graph_spec, analyze_function, to_javascript
from neoex.domain import real_domain_latex
from neoex.exercises import make_question
from neoex.ui import (
    _render_parameter_graph, _prop_stage_html,
    _exercise_prompt, _exercise_radio_choices, _steps_markdown, _steps_stack_html,
    _animate_formula_markup, _analysis_markdown, _render_graph, CSS, MATHJAX_HEAD,
)


class NeoexMathTests(unittest.TestCase):
    def test_required_exponent_products(self):
        self.assertEqual(parse_math("3^3*3^5"), 6561)
        self.assertEqual(parse_math("4^-5*4^3"), sp.Rational(1,16))
        self.assertEqual(parse_math("7^6*7^-4"), 49)
        self.assertEqual(parse_math("2^2*2^-3*2^-4*2^5"), 1)

    def test_algebra_examples(self):
        x=sp.Symbol("x", real=True)
        self.assertEqual(sp.factor(parse_math("x^3+x^2")), x**2*(x+1))
        steps, result, restrictions = build_algebra_steps("(x^2-x^3)/(x^3+x^5)", "Simplificar")
        self.assertEqual(len(steps), 7)  # six transformations plus the real domain
        self.assertEqual(restrictions, ["x ≠ 0"])
        self.assertEqual(steps[-1][0], "Domínio real da expressão")
        self.assertIn(r"\frac{1-x}{x+x^3}", result)

    def test_algebra_preview_format_and_grouping_delimiters(self):
        source = "(2^(n+2) + 2^(n+1) + 3 * 2^n) / (2^(n-1) - 5 * 2^n)"
        preview = format_math_latex(source)
        self.assertIn(r"\frac{2^{n + 2} + 2^{n + 1} + 3 \cdot 2^{n}}{2^{n - 1} - 5 \cdot 2^{n}}", preview)
        self.assertEqual(format_math_latex("2x+1"), "2x + 1")
        self.assertIn(r"\frac{x^{2} + 2x}{x + 1}", format_math_latex("[x^2 + 2x] / {x+1}"))
        with self.assertRaises(ExpressionError):
            format_math_latex("(x+1]")

    def test_unicode_exponents_are_neon_colored(self):
        rendered = _animate_formula_markup("3⁶ / 2⁶ = 729")
        self.assertIn("exp-blue", rendered)
        self.assertIn("exp-red", rendered)
        self.assertIn("<sup", rendered)

    def test_implicit_multiplication_and_safe_parser(self):
        x=sp.Symbol("x", real=True)
        self.assertEqual(parse_math("2^(2x)-5*2^x+4"), 2**(2*x)-5*2**x+4)
        self.assertEqual(parse_math("2x+1"), 2*x+1)
        with self.assertRaises(ExpressionError):
            parse_math("__import__('os').system('whoami')")
        with self.assertRaises(ExpressionError):
            parse_math("1/0", preserve_division=True)

    def test_each_property_has_four_prepared_examples(self):
        self.assertEqual(len(PROPERTIES), 8)
        for item in PROPERTIES.values():
            self.assertEqual(len(item.examples), 4)
            for example in item.examples:
                self.assertGreaterEqual(len(example.steps), 3)
        power = next(e for e in PROPERTIES["power"].examples if e.label == "(5²)³")
        self.assertGreaterEqual(len(power.steps), 8)
        self.assertTrue(any("2 · 3 = 6" in step.formula for step in power.steps))

    def test_graph_build_and_analysis(self):
        spec = build_graph_spec("2^x", x_point=2)
        self.assertAlmostEqual(spec["y_point"], 4.0)
        self.assertIn("Math.pow", spec["function_js"])
        rows = dict(analyze_function("2^x"))
        self.assertEqual(rows["Imagem"], r"\left(0, \infty\right)")
        spec2 = build_graph_spec("1/x", x_point=2)
        self.assertAlmostEqual(spec2["y_point"], .5)


    def test_equation_and_inequality(self):
        steps, result, _ = build_algebra_steps("2^(2x)-5*2^x+4=0", "Resolver equação")
        self.assertIn(r"\left\{0, 2\right\}", result)
        steps, result, _ = build_algebra_steps("2^x>4", "Resolver inequação")
        self.assertIn("2", result)
        self.assertIn(r"\infty", result)

    def test_exponential_parameter_graph_and_live_controls(self):
        graph_html, analysis_html, state = _render_parameter_graph(1, 2, 0, 0, 2)
        self.assertIn("neoex-canvas-shell", graph_html)
        self.assertIn('data-role="point-slider"', graph_html)
        self.assertIn('data-role="apply-point-range"', graph_html)
        self.assertIn('data-role="apply-axes"', graph_html)
        self.assertIn("FUNÇÃO REPRESENTADA", graph_html)
        self.assertIn("PONTO EM TEMPO REAL", graph_html)
        self.assertAlmostEqual(state["x_point"], 2.0)
        self.assertIn("Assíntota horizontal", analysis_html)

    def test_detailed_algebra_demonstrations(self):
        x = sp.Symbol("x", real=True)
        steps, result, restrictions = build_algebra_steps("(x^2-x^3)/(x^3+x^5)", "Simplificar")
        self.assertEqual(len(steps), 7)
        self.assertIn(r"\frac{1-x}{x+x^3}", result)
        self.assertEqual(steps[-1][0], "Domínio real da expressão")
        self.assertEqual(restrictions, ["x ≠ 0"])
        self.assertIn("Cancele o fator comum", [step[0] for step in steps])

        steps, result, _ = build_algebra_steps("x^3+x^2", "Fatorar")
        self.assertGreaterEqual(len(steps), 4)
        self.assertIn("x^2", result)

        steps, result, _ = build_algebra_steps("(x+2)^3", "Desenvolver")
        self.assertGreaterEqual(len(steps), 5)
        self.assertEqual(sp.expand((x+2)**3), parse_math("x^3+6*x^2+12*x+8"))

        steps, result, restrictions = build_algebra_steps("(x^3+2x^2)/(x+2)", "Simplificar")
        self.assertEqual(result, "x^2")
        self.assertEqual(restrictions, ["x ≠ -2"])

        # Even when a common factor disappears, the original denominator is retained.
        steps, result, restrictions = build_algebra_steps("(x+2)*(x-1)/(x+2)", "Simplificar")
        self.assertEqual(result, "x - 1")
        self.assertEqual(restrictions, ["x ≠ -2"])
        steps, result, restrictions = build_algebra_steps("1/(x^2-4)", "Simplificar")
        self.assertEqual(restrictions, ["x ≠ -2", "x ≠ 2"])

    def test_numeric_fractional_powers_and_domain(self):
        source = "(1/4)^(-1/2) + 81^(3/4) - 2^(-1) + 5^0"
        steps, result, restrictions = build_algebra_steps(source, "Simplificar")
        self.assertEqual(parse_math(source), sp.Rational(59, 2))
        self.assertEqual(restrictions, [])
        titles = [step[0] for step in steps]
        self.assertIn("Calcule a potência com expoente negativo", titles)
        self.assertIn("Calcule a potência com expoente fracionário", titles)
        self.assertIn("Interprete o expoente zero", titles)
        self.assertEqual(titles[-1], "Domínio real da expressão")

        x = sp.Symbol("x", real=True)
        cases = {
            "sqrt(x)": r"D_{x}=\left[0, \infty\right)",
            "log(x)": r"D_{x}=\left(0, \infty\right)",
            "x^(-1/2)": r"D_{x}=\left(0, \infty\right)",
            "1/(x^2-4)": r"D_{x}=\mathbb{R}\setminus\{-2,2\}",
        }
        for source, expected in cases.items():
            expr = parse_math(source, preserve_division=True)
            formula, _ = real_domain_latex(expr)
            self.assertEqual(formula, expected)

    def test_custom_algebra_preview_includes_domain_and_no_raw_display_code(self):
        from neoex.ui import _algebra_preview, _graph_preview
        custom = "(2^(n+2) + 2^(n+1) + 3 * 2^n) / (2^(n-1) - 5 * 2^n)"
        preview, status = _algebra_preview(custom)
        self.assertIn(r"\frac{2^{n + 2} + 2^{n + 1} + 3 \cdot 2^{n}}{2^{n - 1} - 5 \cdot 2^{n}}", preview)
        self.assertIn("DOMÍNIO REAL", preview)
        self.assertIn(r"D_{n}=\mathbb{R}", preview)
        graph_preview = _graph_preview("sqrt(x)")
        self.assertIn("DOMÍNIO REAL", graph_preview)
        self.assertIn("Dₓ=[0, ∞)", graph_preview)
        self.assertNotIn(r"\(", graph_preview)
        self.assertNotIn(r"\mathbb", graph_preview)

    def test_algebra_resolution_renders_all_steps_as_vertical_cards(self):
        steps, result, _ = build_algebra_steps("(1/4)^(-1/2) + 81^(3/4) - 2^(-1) + 5^0", "Simplificar")
        rendered = _steps_stack_html(steps)
        self.assertIn("ETAPA 01", rendered)
        self.assertIn(f"ETAPA {len(steps):02d}", rendered)
        self.assertIn("Calcule a potência com expoente fracionário", rendered)
        self.assertIn("Domínio real da expressão", rendered)
        self.assertIn(r"\boxed{\dfrac{59}{2}}", rendered)


    def test_zero_exponent_keeps_its_original_domain(self):
        from neoex.domain import real_domain_latex
        for source, excluded, point in (("x^0", 0, 0), ("(x-1)^0", 1, 1)):
            domain_expr = parse_math(source, preserve_division=True, preserve_structure=True)
            formula, _ = real_domain_latex(domain_expr)
            self.assertIn(r"\setminus", formula)
            steps, result, restrictions = build_algebra_steps(source, "Simplificar")
            self.assertEqual(result, "1")
            self.assertIn(f"x ≠ {excluded}", restrictions)
            spec = build_graph_spec(source, x_point=point)
            self.assertIsNone(spec["y_point"])
            self.assertIn(float(point), spec["excluded_points"])
        with self.assertRaises(ExpressionError):
            parse_math("0^0")

    def test_multivariable_expression_domain_conditions(self):
        expr = parse_math("sqrt(x+y)/(x-y)", preserve_division=True, preserve_structure=True)
        formula, note = real_domain_latex(expr)
        self.assertIn(r"\mathbb{R}^{2}", formula)
        self.assertIn(r"x \geq - y", formula)
        self.assertIn(r"x \neq y", formula)
        self.assertIn("condições", note)

    def test_graph_preserves_holes_and_real_domain(self):
        expression = "(x+2)*(x-1)/(x+2)"
        spec = build_graph_spec(expression, x_point=-2)
        self.assertIsNone(spec["y_point"])
        self.assertIn(-2.0, spec["excluded_points"])
        analysis = dict(analyze_function(expression))
        self.assertEqual(analysis["Domínio"], r"\mathbb{R}\setminus\{-2\}")

        sqrt_analysis = dict(analyze_function("sqrt(x)"))
        self.assertEqual(sqrt_analysis["Domínio"], r"\left[0, \infty\right)")

    def test_exponential_fraction_step_by_step(self):
        source = "(2^(n+2) + 2^(n+1) + 3 * 2^n) / (2^(n-1) - 5 * 2^n)"
        steps, result, restrictions = build_algebra_steps(source, "Simplificar")
        self.assertEqual(result, "-2")
        self.assertEqual(restrictions, [])
        self.assertGreaterEqual(len(steps), 9)
        titles = [step[0] for step in steps]
        self.assertIn("Coloque 2ⁿ em evidência no numerador", titles)
        self.assertIn("Cancele o fator comum", titles)

    def test_exponential_inequality_solution_steps(self):
        steps, result, _ = build_algebra_steps("3^x>3^5", "Resolver inequação")
        titles = [step[0] for step in steps]
        self.assertIn("Compare os expoentes", titles)
        self.assertIn(r"x > 5", [step[1] for step in steps])
        self.assertEqual(result, r"\left(5, \infty\right)")

    def test_visual_superscript_colors_and_exercise_controls(self):
        stage = _prop_stage_html("div", "a³ / a²", 0)
        self.assertIn("exp-blue", stage)
        sum_stage = _prop_stage_html("mult", "4⁻⁵ · 4³", 2)
        self.assertIn("exp-blue", sum_stage)
        self.assertIn("exp-red", sum_stage)
        prompt = _exercise_prompt({"prompt": "Resolva em ℝ: 3^x > 3^5"})
        self.assertIn("<sup>x</sup>", prompt)
        choices = _exercise_radio_choices({"options": ["2^3", "x > 5", "1/16", "(1-x)/(x+x^3)"]})
        self.assertEqual([value for _, value in choices], list("ABCD"))
        self.assertIn("2³", choices[0][0])
        self.assertIn("x > 5", choices[1][0])


    def test_algebra_fraction_bar_and_explanations_are_readable(self):
        from neoex.ui import CSS, _explanation_html
        self.assertIn("border-top:2px solid #f0f6ff", CSS)
        self.assertNotIn("border-top:0!important", CSS)
        rendered = _explanation_html(r"Reescrevemos: - x^{3} + x^{2} = - x^{2} \left(x - 1\right).")
        self.assertIn("x³", rendered)
        self.assertIn("x² (x - 1)", rendered)
        self.assertNotIn(r"\left", rendered)
        self.assertNotIn("^{3}", rendered)

    def test_generic_fraction_explanations_never_leak_latex_source(self):
        steps, result, _ = build_algebra_steps("(x^2-x^3)/(x^4+x^5)", "Simplificar")
        rendered = _steps_stack_html(steps)
        self.assertIn("x³", rendered)
        self.assertIn("x⁴", rendered)
        self.assertIn("(x - 1)", rendered)
        import re
        explanations = re.findall(r"<div class='algebra-explanation'>(.*?)</div>", rendered)
        self.assertEqual(len(explanations), len(steps))
        for explanation in explanations:
            for raw_token in (r"\left", r"\right", r"x^{3}", r"\frac"):
                self.assertNotIn(raw_token, explanation)

    def test_canvas_graph_payload_is_safe_and_interactive(self):
        import base64, json, re
        from neoex.ui import _render_graph
        graph_html, _, _ = _render_graph("x^2+x^3", "", 1.5, -5, 5)
        encoded = re.search(r'data-config="([^"]+)"', graph_html).group(1)
        payload = json.loads(base64.b64decode(encoded).decode("utf-8"))
        self.assertIn("function_js", payload)
        self.assertIn("Math.pow", payload["function_js"])
        self.assertEqual(payload["x_min"], -5.0)
        self.assertEqual(payload["x_max"], 5.0)
        self.assertIn('data-role="graph-canvas"', graph_html)
        self.assertIn('data-role="point-slider"', graph_html)
        self.assertIn('data-role="current-x"', graph_html)
        self.assertIn('data-role="line-slider"', graph_html)
        self.assertIn('data-role="roots-toggle"', graph_html)
        self.assertIn('data-role="line-toggle"', graph_html)
        runtime = (__import__('pathlib').Path(__file__).resolve().parents[1] / 'neoex' / 'graph_runtime.js').read_text(encoding='utf-8')
        self.assertIn("pointerdown", runtime)
        self.assertIn("pointermove", runtime)
        self.assertIn("listen(canvas, 'wheel'", runtime)
        self.assertIn("computeIntersections", runtime)
        self.assertNotIn("Plotly", runtime)

    def test_graph_serializer_handles_implicit_products_and_real_fractional_powers(self):
        expr = parse_math("(2^2x + 3x^x)/4x^2")
        js = to_javascript(expr)
        self.assertIn("Math.pow(x, x)", js)
        self.assertIn("Math.pow(Math.abs(x), -2)", js)
        self.assertIn("4 * x", js)
        self.assertIn("Math.pow(Math.abs(-1)", to_javascript(parse_math("(-8)^(2/3)")))
        js_even = to_javascript(parse_math("x^(2/3)"))
        self.assertIn("1 * Math.pow(Math.abs(x)", js_even)
        js_odd = to_javascript(parse_math("x^(1/3)"))
        self.assertIn("Math.sign(x)", js_odd)

    def test_graph_payload_uses_strict_json_and_canvas_for_discontinuous_functions(self):
        import base64, json, re
        from neoex.ui import _render_graph
        for source in ("1/x", "sqrt(x)", "log(x)", "x^x", "(2^2x + 3x^x)/4x^2"):
            with self.subTest(source=source):
                graph_html, analysis_html, state = _render_graph(source, "", 2.0, -8.0, 8.0)
                encoded = re.search(r'data-config="([^"]+)"', graph_html).group(1)
                payload = json.loads(base64.b64decode(encoded).decode("utf-8"))
                json.dumps(payload, allow_nan=False)
                self.assertIn("neoex-canvas-shell", graph_html)
                self.assertIn("analysis-grid", analysis_html)
                self.assertEqual(state["expression"], source)

    def test_graph_renderer_handles_polynomials_and_general_functions(self):
        for source in ("2^x+1/4", "2^x+1/4+5/8", "x^2+x^3", "sin(x)", "sqrt(x)", "1/x", "x^12-3x^5+2", "(2^2x + 3x^x)/4x^2"):
            with self.subTest(source=source):
                graph_html, analysis_html, state = _render_graph(source, "", 2.0)
                self.assertIn("data-config=", graph_html)
                self.assertIn("neoex-canvas-wrap", graph_html)
                self.assertIn("analysis-grid", analysis_html)
                self.assertEqual(state["expression"], source)

    def test_high_multiplicity_polynomials_do_not_create_false_roots(self):
        from neoex.graphs import find_real_roots
        for source in ("x^25", "x^50", "x^250", "(x-1)^20", "(x-1)^50", "(x-1)^101"):
            with self.subTest(source=source):
                roots = find_real_roots(parse_math(source), -8, 8)
                expected = 0.0 if source.startswith("x^") else 1.0
                self.assertEqual(len(roots), 1)
                self.assertAlmostEqual(roots[0], expected, places=5)

    def test_horizontal_level_solver_finds_crossings_and_tangencies(self):
        from neoex.graphs import find_real_roots
        x = sp.Symbol("x", real=True)
        self.assertEqual(find_real_roots(x**2, -3, 3, level=0), [0.0])
        roots = find_real_roots(x**2, -3, 3, level=4)
        self.assertEqual(len(roots), 2)
        self.assertAlmostEqual(roots[0], -2.0, places=6)
        self.assertAlmostEqual(roots[1], 2.0, places=6)
        self.assertEqual(find_real_roots(x**3, -2, 2, level=8), [2.0])

    def test_substitution_expression_preserves_source_for_live_readout(self):
        spec = build_graph_spec("x^2+x^3", x_point=1.5)
        self.assertEqual(spec["expression_plain"], "x^2+x^3")
        spec = build_graph_spec("(2^2x + 3x^x)/4x^2")
        self.assertEqual(spec["expression_plain"], "(2^2x + 3x^x)/4x^2")

    def test_graph_renderer_reports_roots_and_critical_points(self):
        spec = build_graph_spec("x^2-4", -5, 5, 0)
        self.assertEqual(len(spec["roots"]), 2)
        self.assertAlmostEqual(spec["roots"][0], -2, places=6)
        self.assertAlmostEqual(spec["roots"][1], 2, places=6)
        self.assertEqual(len(spec["critical_points"]), 1)
        self.assertAlmostEqual(spec["critical_points"][0], 0, places=6)

    def test_canvas_runtime_has_no_polling_or_plotly_dependency(self):
        from pathlib import Path
        source = (Path(__file__).resolve().parents[1] / 'neoex' / 'graph_runtime.js').read_text(encoding='utf-8')
        self.assertNotIn("setInterval", source)
        self.assertNotIn("Plotly", source)
        self.assertIn("requestAnimationFrame", source)
        self.assertIn("ResizeObserver", source)
        self.assertIn("computeIntersections", source)

    def test_graph_analysis_uses_prose_for_descriptions_and_responsive_cards(self):
        rows = analyze_function("2^x+1/4")
        rendered = _analysis_markdown(rows)
        self.assertIn("analysis-grid", rendered)
        self.assertIn("analysis-wide", rendered)
        self.assertNotIn("<div class='analysis-item analysis-wide'><div class='analysis-name'>Expressão", rendered)
        self.assertNotIn("<div class='analysis-item analysis-wide'><div class='analysis-name'>Derivada", rendered)
        self.assertIn("analysis-text", rendered)
        self.assertIn("crescente em todo o domínio real", rendered)
        self.assertIn("Contínua em todo ponto do domínio real", rendered)
        parameter_analysis = _render_parameter_graph(1, 2, 0, 0)[1]
        self.assertIn("analysis-text", parameter_analysis)
        self.assertIn("crescente", parameter_analysis)
        self.assertNotIn(r"\(O sinal da derivada", rendered)
        self.assertNotIn(r"\(crescente em", rendered)
        self.assertIn("min(100%,270px)", CSS)
        self.assertIn("overflow-x:auto", CSS)

    def test_exercise_options_unique(self):
        for level in ("Básico", "Intermediário", "Difícil"):
            for _ in range(25):
                q=make_question(level)
                self.assertEqual(len(q["options"]), 4)
                self.assertEqual(len(set(q["options"])), 4)
                self.assertIn(q["answer"], q["options"])
                self.assertFalse(any(x in q["options"] for x in ("nenhuma das anteriores", "resultado diferente", "expressão indefinida")))
                self.assertGreaterEqual(len(q["solution_steps"]), 4)


if __name__ == "__main__":
    unittest.main()
