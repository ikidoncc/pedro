"""Tab 03: Interactive 2D Canvas graph laboratory and exponential parameters."""
from __future__ import annotations

import base64
from functools import lru_cache
import html
import json

import gradio as gr

from ..domain import real_domain_latex
from ..graphs import X, analyze_function, build_graph_spec, to_javascript
from ..latex_plain import latex_fragment_to_plain_text
from ..parser import ExpressionError, format_math_latex, parse_math

GRAPH_HTML_JS_ON_LOAD = r"""
if(window.NEOEX_attachGraphHost) window.NEOEX_attachGraphHost(element);
else window.addEventListener('neoex-runtime-ready', function(){ window.NEOEX_attachGraphHost && window.NEOEX_attachGraphHost(element); }, {once:true});
"""


def _analysis_markdown(rows, point=None, point_x=None):
    """Render graph-analysis formulas as readable Unicode, never raw TeX."""
    prose_fields = {"Crescimento / decrescimento", "Continuidade", "Comportamento"}
    wide_fields = {
        "Comportamento nos extremos",
        "Crescimento / decrescimento", "Continuidade",
    }
    cells = []
    for name, value in rows:
        name_html = html.escape(str(name))
        value_str = str(value)
        is_prose = name in prose_fields or (
            name == "Assíntotas" and not any(token in value_str for token in ("\\", "=", "^", "_"))
        )
        card_class = "analysis-item analysis-wide" if name in wide_fields else "analysis-item"
        if is_prose:
            if name == "Assíntotas" and value_str.startswith(r"\text{") and value_str.endswith("}"):
                value_str = value_str[len(r"\text{"):-1]
            value_html = f"<div class='analysis-text'>{html.escape(value_str)}</div>"
        else:
            readable = latex_fragment_to_plain_text(value_str)
            value_html = f"<div class='analysis-value analysis-math-text'>{html.escape(readable)}</div>"
        cells.append(f"<div class='{card_class}'><div class='analysis-name'>{name_html}</div>{value_html}</div>")
    if point is not None:
        value = f"{point:.6g}"
        cells.append(
            "<div class='analysis-item'><div class='analysis-name'>Ponto selecionado</div>"
            f"<div class='analysis-text'>x = {point_x:.4g}; g(x) = {value}</div></div>"
        )
    return "<div class='analysis-grid'>" + "".join(cells) + "</div>"


@lru_cache(maxsize=128)
def _graph_preview(text):
    """Live graph preview in Unicode math; never expose TeX source in this tab."""
    try:
        expr = parse_math(text, preserve_division=True, preserve_structure=True)
        rendered = format_math_latex(text)
        function_display = html.escape(latex_fragment_to_plain_text(r"g(x) = " + rendered))
        domain_formula, domain_explanation = real_domain_latex(expr)
        domain_display = html.escape(latex_fragment_to_plain_text(domain_formula))
        explanation_display = html.escape(domain_explanation)
        return (
            "<div class='preview-card graph-preview-card'>"
            "<div class='math-preview-title'>FUNÇÃO FORMATADA</div>"
            f"<div class='math-preview-formula neoex-plain-math'>{function_display}</div>"
            "<div class='domain-preview'>"
            "<div class='domain-preview-label'>DOMÍNIO REAL</div>"
            f"<div class='domain-preview-formula neoex-plain-math'>{domain_display}</div>"
            f"<div class='domain-preview-note'>{explanation_display}</div>"
            "</div></div>"
        )
    except Exception as exc:
        return f"<div class='preview-card' style='color:#ff9aaa'>Função ainda incompleta: {html.escape(str(exc))}</div>"


def _pt_number(value):
    rounded = f"{float(value):.3f}".rstrip("0").rstrip(".")
    return rounded.replace(".", ",") if rounded else "0"


def _safe_payload_json(spec):
    """Encode only JSON-compatible graph instructions, never raw executable input."""
    payload = {
        "function_js": spec["function_js"],
        "expression_plain": spec.get("expression_plain", spec.get("expression", "g(x)")),
        "domain_plain": latex_fragment_to_plain_text(spec.get("domain_tex", "")),
        "constant_function": bool(spec.get("constant_function", False)),
        "constant_value": spec.get("constant_value"),
        "x_min": float(spec["x_min"]),
        "x_max": float(spec["x_max"]),
        "x_point": float(spec["x_point"]),
        "roots": [float(value) for value in spec.get("roots", [])],
        "critical_points": [float(value) for value in spec.get("critical_points", [])],
        "excluded_points": [float(value) for value in spec.get("excluded_points", [])],
        "roots_all": bool(spec.get("roots_all", False)),
        "compare": spec.get("compare", []),
        "line_y": float(spec.get("line_y", 0.0)),
    }
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return base64.b64encode(encoded).decode("ascii")


def _live_graph_html(spec):
    """Build a light, dependency-free Canvas graph with GeoGebra-like tools."""
    point_min = float(spec["x_min"])
    point_max = float(spec["x_max"])
    x_point = float(spec["x_point"])
    point_y = spec.get("y_point")
    encoded = _safe_payload_json(spec)
    readout_y = "fora do domínio real" if point_y is None else _pt_number(point_y)
    readout_x = _pt_number(x_point)
    expression_tex = spec["expression_tex"]
    domain_tex = spec.get("domain_tex", r"D_x=\text{não determinado automaticamente}")
    function_display = html.escape(latex_fragment_to_plain_text(r"g(x) = " + expression_tex))
    domain_display = html.escape(latex_fragment_to_plain_text(domain_tex))
    return f"""
    <div class="neoex-canvas-shell" data-neoex-graph="1" data-config="{encoded}">
      <div class="neoex-canvas-top">
        <div class="neoex-canvas-function">
          <span class="neoex-canvas-label">FUNÇÃO REPRESENTADA</span>
          <div class="neoex-canvas-math neoex-plain-math">{function_display}</div>
          <div class="neoex-canvas-domain">Domínio real: <span class="neoex-canvas-domain-math neoex-plain-math">{domain_display}</span></div>
        </div>
        <div class="neoex-canvas-readout">
          <span class="neoex-canvas-label">PONTO EM TEMPO REAL</span>
          <div class="readout-x" data-role="readout-x">x = {html.escape(readout_x)}</div>
          <div class="readout-y" data-role="readout-y">g({html.escape(readout_x)}) = {html.escape(readout_y)}</div>
        </div>
      </div>

      <div class="neoex-canvas-wrap">
        <canvas data-role="graph-canvas" tabindex="0" aria-label="Plano cartesiano interativo. Arraste o ponto verde, a reta horizontal ou o plano. Use o scroll para zoom."></canvas>
      </div>

      <div class="neoex-canvas-output">
        <div><strong>RAÍZES NO INTERVALO</strong><span data-role="roots-output">Calculando raízes…</span></div>
        <div><strong>INTERSEÇÕES COM A RETA HORIZONTAL</strong><span data-role="intersections-output">Movimente a reta para encontrar pontos com a mesma imagem.</span></div>
      </div>

      <div class="neoex-canvas-controls">
        <div class="neoex-canvas-card">
          <div class="neoex-canvas-card-title">PONTO MÓVEL · INTERVALO DE x</div>
          <div class="control-row">
            <label>mínimo</label><input data-role="point-min" type="number" step="any" value="{point_min:g}">
            <label>máximo</label><input data-role="point-max" type="number" step="any" value="{point_max:g}">
            <button type="button" data-role="apply-point-range">Aplicar</button>
          </div>
          <div class="control-row" style="margin-top:10px">
            <input data-role="point-slider" type="range" min="{point_min:g}" max="{point_max:g}" value="{x_point:g}" step="0.001">
          </div>
          <div class="control-row">
            <label class="green-x">x = <input data-role="current-x" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" aria-label="Digite a coordenada x do ponto móvel" value="{html.escape(readout_x, quote=True)}"></label>
            <span class="neoex-canvas-status" data-role="graph-status">Arraste o ponto verde, use a barra ou digite o valor de x.</span>
          </div>
        </div>

        <div class="neoex-canvas-card">
          <div class="neoex-canvas-card-title">RETA HORIZONTAL · y = c</div>
          <div class="control-row">
            <label><input data-role="line-toggle" type="checkbox" checked> mostrar reta</label>
            <label><input data-role="roots-toggle" type="checkbox" checked> mostrar raízes</label>
          </div>
          <div class="control-row">
            <label>valor de y</label><input data-role="line-y" type="text" inputmode="decimal" value="{float(spec.get('line_y', 0.0)):g}">
          </div>
          <div class="control-row">
            <input data-role="line-slider" type="range" min="-10" max="10" step="0.01" value="{float(spec.get('line_y', 0.0)):g}">
          </div>
          <div class="neoex-canvas-status">Arraste a linha violeta para cima ou para baixo. Os pontos A, B, C… mostram as interseções.</div>
        </div>

        <div class="neoex-canvas-card">
          <div class="neoex-canvas-card-title">ENQUADRAMENTO DOS EIXOS</div>
          <div class="control-row">
            <label>x mín.</label><input data-role="axis-xmin" type="number" step="any" value="{point_min:g}">
            <label>x máx.</label><input data-role="axis-xmax" type="number" step="any" value="{point_max:g}">
          </div>
          <div class="control-row">
            <label>y mín.</label><input data-role="axis-ymin" type="number" step="any" placeholder="auto">
            <label>y máx.</label><input data-role="axis-ymax" type="number" step="any" placeholder="auto">
          </div>
          <div class="control-row">
            <label><input data-role="grid-toggle" type="checkbox" checked> grade</label>
            <button type="button" data-role="apply-axes">Aplicar eixos</button>
            <button type="button" data-role="reset-view">Reenquadrar</button>
          </div>
          <div class="neoex-canvas-status">Scroll: zoom · Arrastar vazio: deslocar plano · Duplo clique: reenquadrar.</div>
        </div>
      </div>
    </div>
    """


def _render_graph(expression, compare, x_point=2.0, point_min=-8.0, point_max=8.0):
    spec = build_graph_spec(expression, point_min, point_max, x_point)
    compare_specs = []
    for index, item in enumerate((compare or "").split(";")):
        item = item.strip()
        if not item:
            continue
        comp = parse_math(item)
        if len(comp.free_symbols - {X}) > 0:
            raise ExpressionError("As funções de comparação também devem usar apenas x.")
        compare_specs.append({"label": f"h{index+1}(x)", "function_js": to_javascript(comp)})
    spec["compare"] = compare_specs
    rows = analyze_function(expression, point_min, point_max)
    graph_html = _live_graph_html(spec)
    analysis = _analysis_markdown(rows)
    state = {
        "mode": "normal", "expression": expression, "compare": compare,
        "x_point": spec["x_point"], "point_min": point_min, "point_max": point_max,
    }
    return graph_html, analysis, state


def _render_parameter_graph(a, b, h, k, x_point=2.0, point_min=-8.0, point_max=8.0):
    a, b, h, k = map(float, (a, b, h, k))
    if b <= 0 or abs(b - 1) < 1e-9:
        raise ExpressionError("Para a função exponencial real usual, b deve ser positivo e diferente de 1.")

    def n(value):
        return format(float(value), ".15g")

    source = f"({n(a)})*({n(b)})^(x-({n(h)}))+({n(k)})"
    spec = build_graph_spec(source, point_min, point_max, x_point)
    spec["line_y"] = k
    rows = [
        ("Modelo", rf"g(x)={n(a)}\cdot {n(b)}^{{x-({n(h)})}}+({n(k)})"),
        ("Domínio", r"\mathbb R"),
        ("Imagem", f"({k:g}, +∞)" if a > 0 else f"(−∞, {k:g})" if a < 0 else f"{{{k:g}}}"),
        ("Assíntota horizontal", rf"y={n(k)}"),
        ("Comportamento", "crescente" if (b > 1 and a > 0) or (0 < b < 1 and a < 0) else "decrescente" if (b > 1 and a < 0) or (0 < b < 1 and a > 0) else "constante"),
    ]
    return _live_graph_html(spec), _analysis_markdown(rows), {
        "mode": "parameter", "a": a, "b": b, "h": h, "k": k,
        "expression": source, "compare": "", "x_point": spec["x_point"],
        "point_min": point_min, "point_max": point_max,
    }


def build_graphs_tab():
    """Render the interactive Canvas graph laboratory tab inside a Blocks context."""
    initial_graph_html = "<div class='neoex-graph-placeholder'>Abra esta aba para inicializar o laboratório gráfico.</div>"
    initial_analysis = "<div class='analysis-grid'><div class='analysis-item analysis-wide'><div class='analysis-name'>ANÁLISE MATEMÁTICA</div><div class='analysis-text'>A análise será calculada quando o primeiro gráfico for carregado.</div></div></div>"

    with gr.Tab("03 · GRÁFICOS") as graph_tab:
        gr.Markdown("<div class='section-title'>GRÁFICOS E COMPORTAMENTO DAS FUNÇÕES</div><div class='section-sub'>Digite uma função de uma variável, mova o ponto verde, investigue as raízes e desloque a reta horizontal para descobrir quais abscissas produzem a mesma imagem.</div>")
        with gr.Row():
            with gr.Column(scale=3):
                graph_examples = gr.Dropdown(
                    choices=[
                        ("2ˣ", "2^x"), ("3ˣ", "3^x"), ("(1/2)ˣ", "(1/2)^x"), ("x²", "x^2"),
                        ("x³", "x^3"), ("x⁴ − 3x² + 2", "x^4-3x^2+2"), ("1/x", "1/x"), ("xˣ", "x^x"),
                        ("(2²x + 3xˣ)/(4x²)", "(2^2x + 3x^x)/4x^2"), ("x² + 2", "x^2+2"), ("2ˣ + 3", "2^x+3"),
                    ],
                    value="2^x", label="FUNÇÕES PREPARADAS",
                )
                graph_input = gr.Textbox(value="2^x", label="g(x) =", lines=2, info="A expressão será convertida para notação matemática na pré-visualização.")
                graph_preview = gr.HTML("<div class='preview-card graph-preview-card'><div class='math-preview-title'>FUNÇÃO FORMATADA</div><div class='math-preview-formula neoex-plain-math'>g(x) = 2ˣ</div></div>")
                graph_compare = gr.Textbox(value="", label="COMPARAR COM (separe por ;)", placeholder="x^2; 3^x")
                graph_button = gr.Button("GERAR GRÁFICO E ANÁLISE", variant="primary")
            with gr.Column(scale=2):
                gr.HTML("""<div class='syntax-card'><div class='panel-title'>SINTAXE DE FUNÇÕES</div><div class='syntax-line'><b>Exponencial</b> <code>2^x</code> <span>→</span> <strong>2ˣ</strong></div><div class='syntax-line'><b>Potência e produto</b> <code>2^2x</code> <span>→</span> <strong>2² · x</strong></div><div class='syntax-line'><b>Expoente variável</b> <code>3x^x</code> <span>→</span> <strong>3 · xˣ</strong></div><div class='syntax-line'><b>Polinômio</b> <code>x^5-3x^2+2</code> <span>→</span> <strong>grau 5</strong></div><div class='syntax-line'><b>Fração monomial</b> <code>a/4x^2</code> <span>→</span> <strong>a/(4x²)</strong></div><div class='syntax-line'><b>Funções</b> <code>sqrt(x), sin(x), log(x)</code> <span>→</span> <strong>√x, sen x, ln x</strong></div><div class='syntax-foot'>Convenção: a multiplicação implícita liga-se antes de ÷. Assim, a/4x² é lido como a/(4x²). Use parênteses para deixar outra agrupação explícita. O gráfico é desenhado em Canvas, sem Plotly ou biblioteca externa de gráficos.</div></div>""")

        graph_plot = gr.HTML(initial_graph_html, js_on_load=GRAPH_HTML_JS_ON_LOAD, elem_id="neoex-graph-output")
        graph_analysis = gr.HTML(initial_analysis)
        graph_state = gr.State(None)
        graph_loaded = gr.State(False)

        graph_input.input(
            _graph_preview, [graph_input], [graph_preview],
            trigger_mode="always_last", show_progress="hidden",
            concurrency_id="neoex-graph-preview", concurrency_limit=1,
        )

        def render_graph_outputs(source, compare):
            try:
                graph_html, analysis_html, state = _render_graph(source, compare)
                return graph_html, analysis_html, state, True
            except Exception as exc:
                message = html.escape(str(exc))
                error_graph = (
                    "<div class='neoex-graph-placeholder' role='alert'>"
                    f"Não foi possível gerar o gráfico: {message}</div>"
                )
                error_analysis = (
                    "<div class='analysis-grid'><div class='analysis-item analysis-wide'>"
                    f"<div class='analysis-name'>ERRO AO CONSTRUIR O GRÁFICO</div><div class='analysis-text'>{message}</div>"
                    "</div></div>"
                )
                return error_graph, error_analysis, None, False

        def render_if_changed(source, compare, state, loaded):
            if loaded and isinstance(state, dict) and state.get("mode") == "normal":
                if state.get("expression") == source and (state.get("compare") or "") == (compare or ""):
                    return gr.skip(), gr.skip(), gr.skip(), True
            return render_graph_outputs(source, compare)

        def choose_graph(label, compare):
            preview = _graph_preview(label)
            graph_outputs = render_graph_outputs(label, compare)
            return (label, preview, *graph_outputs)

        graph_examples.change(
            choose_graph, [graph_examples, graph_compare],
            [graph_input, graph_preview, graph_plot, graph_analysis, graph_state, graph_loaded],
            show_progress="hidden", trigger_mode="always_last",
            concurrency_id="neoex-graph-compute", concurrency_limit=1,
        )
        graph_input.change(
            render_if_changed, [graph_input, graph_compare, graph_state, graph_loaded],
            [graph_plot, graph_analysis, graph_state, graph_loaded],
            show_progress="hidden", trigger_mode="always_last",
            concurrency_id="neoex-graph-compute", concurrency_limit=1,
        )
        graph_input.submit(
            render_graph_outputs, [graph_input, graph_compare],
            [graph_plot, graph_analysis, graph_state, graph_loaded],
            show_progress="hidden", trigger_mode="always_last",
            concurrency_id="neoex-graph-compute", concurrency_limit=1,
        )
        graph_compare.change(
            render_if_changed, [graph_input, graph_compare, graph_state, graph_loaded],
            [graph_plot, graph_analysis, graph_state, graph_loaded],
            show_progress="hidden", trigger_mode="always_last",
            concurrency_id="neoex-graph-compute", concurrency_limit=1,
        )

        def load_graph_on_first_open(already_loaded):
            if already_loaded:
                return gr.skip(), gr.skip(), gr.skip(), True
            return render_graph_outputs("2^x", "")

        graph_tab.select(
            load_graph_on_first_open, [graph_loaded],
            [graph_plot, graph_analysis, graph_state, graph_loaded],
            show_progress="hidden", trigger_mode="once",
            concurrency_id="neoex-graph-compute", concurrency_limit=1,
        )
        graph_button.click(
            render_graph_outputs, [graph_input, graph_compare],
            [graph_plot, graph_analysis, graph_state, graph_loaded],
            show_progress="minimal", trigger_mode="always_last",
            concurrency_id="neoex-graph-compute", concurrency_limit=1,
        )
        with gr.Accordion("LABORATÓRIO DE PARÂMETROS EXPONENCIAIS", open=False):
            gr.Markdown(r"Modelo: \(g(x)=a\cdot b^{(x-h)}+k\). A linha tracejada indica a assíntota horizontal \(y=k\).")
            with gr.Row():
                p_a = gr.Slider(-4, 4, value=1, step=0.1, label="a · escala / reflexão")
                p_b = gr.Slider(0.2, 4, value=2, step=0.1, label="b · base (b ≠ 1)")
            with gr.Row():
                p_h = gr.Slider(-5, 5, value=0, step=0.1, label="h · deslocamento horizontal")
                p_k = gr.Slider(-5, 5, value=0, step=0.1, label="k · deslocamento vertical")
            p_button = gr.Button("APLICAR PARÂMETROS", variant="primary")
            gr.Markdown("Ajuste os controles e clique em APLICAR PARÂMETROS para redesenhar a curva; assim evitamos recálculos a cada movimento do mouse.")

            def safe_parameter(a, b, h, k, state):
                state = state or {}
                xp = float(state.get("x_point", 2.0))
                pmin = float(state.get("point_min", -8.0))
                pmax = float(state.get("point_max", 8.0))
                xp = min(pmax, max(pmin, xp))
                try:
                    graph_html, analysis_html, updated_state = _render_parameter_graph(a, b, h, k, xp, pmin, pmax)
                    return graph_html, analysis_html, updated_state, True
                except Exception as exc:
                    return gr.skip(), f"<div class='analysis-grid'><div class='analysis-item analysis-wide'><div class='analysis-name'>ERRO NOS PARÂMETROS</div><div class='analysis-text'>{html.escape(str(exc))}</div></div></div>", gr.skip(), True

            p_button.click(
                safe_parameter, [p_a, p_b, p_h, p_k, graph_state],
                [graph_plot, graph_analysis, graph_state, graph_loaded],
                show_progress="minimal", trigger_mode="always_last",
                concurrency_id="neoex-graph-compute", concurrency_limit=1,
            )
