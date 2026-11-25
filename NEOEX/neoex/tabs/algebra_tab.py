"""Tab 02: Symbolic algebra transformations and step-by-step explanations."""
from __future__ import annotations

import html

import gradio as gr

from ..algebra import build_algebra_steps
from ..domain import real_domain_latex
from ..latex_plain import latex_fragment_to_plain_text
from ..parser import format_math_latex, parse_math


def _explanation_html(explanation: str) -> str:
    return html.escape(latex_fragment_to_plain_text(explanation))


def _steps_markdown(steps, index):
    title, formula, explanation = steps[index]
    formula = formula or r"\text{Transformação em andamento}"
    formula = formula.replace(r"\frac", r"\dfrac")
    safe_title = html.escape(title)
    safe_explanation = _explanation_html(explanation)
    fallback_formula = html.escape(latex_fragment_to_plain_text(formula), quote=True)
    return (
        f"<div class='algebra-step-card'>"
        f"<div class='algebra-step-top'>NEOEX · ETAPA {index+1:02d} / {len(steps):02d}</div>"
        f"<div class='algebra-step-title'>{safe_title}</div>"
        f"<div class='algebra-equation' data-neoex-tex-fallback='{fallback_formula}'>\\[\\displaystyle {formula}\\]</div>"
        f"<div class='algebra-explanation'>{safe_explanation}</div>"
        f"</div>"
    )


def _steps_stack_html(steps):
    """Render every algebra transformation as an exercise-style vertical card."""
    if not steps:
        return "<div class='algebra-step-card'>Nenhuma etapa disponível.</div>"
    cards = []
    total = len(steps)
    for index, (title, formula, explanation) in enumerate(steps, start=1):
        safe_title = html.escape(title)
        safe_explanation = _explanation_html(explanation)
        formula = formula or r"\text{Transformação em andamento}"
        formula = formula.replace(r"\frac", r"\dfrac")
        fallback_formula = html.escape(latex_fragment_to_plain_text(formula), quote=True)
        cards.append(
            "<div class='algebra-step-card'>"
            f"<div class='algebra-step-top'>NEOEX · ETAPA {index:02d} / {total:02d}</div>"
            f"<div class='algebra-step-title'>{safe_title}</div>"
            f"<div class='algebra-equation' data-neoex-tex-fallback='{fallback_formula}'>\\[\\displaystyle {formula}\\]</div>"
            f"<div class='algebra-explanation'>{safe_explanation}</div>"
            "</div>"
        )
    return "<div class='algebra-step-stack'>" + "".join(cards) + "</div>"


def _domain_preview_html(expr):
    formula, explanation = real_domain_latex(expr)
    fallback_domain = html.escape(latex_fragment_to_plain_text(formula), quote=True)
    return (
        "<div class='domain-preview'>"
        "<div class='domain-preview-label'>DOMÍNIO REAL</div>"
        f"<div class='domain-preview-formula' data-neoex-tex-fallback='{fallback_domain}'>\\({formula}\\)</div>"
        f"<div class='domain-preview-note'>{html.escape(explanation)}</div>"
        "</div>"
    )


def _algebra_preview(text):
    try:
        expr = parse_math(text, preserve_division=True, preserve_structure=True)
        rendered = format_math_latex(text)
        fallback_rendered = html.escape(latex_fragment_to_plain_text(rendered), quote=True)
        return (
            "<div class='preview-card'>"
            "<div class='math-preview-title'>EXPRESSÃO MATEMÁTICA FORMATADA</div>"
            f"<div class='math-preview-formula' data-neoex-tex-fallback='{fallback_rendered}'>\\[{rendered}\\]</div>"
            f"{_domain_preview_html(expr)}"
            "</div>",
            "Expressão reconhecida. A notação matemática e o domínio real são atualizados a partir do que está no campo.",
        )
    except Exception as exc:
        return (
            "<div class='preview-card' style='color:#ff9aaa'>A pré-visualização aparecerá quando a expressão estiver sintaticamente completa.</div>",
            html.escape(str(exc)),
        )


def build_algebra_tab():
    """Render the algebraic laboratory tab inside a Blocks context."""
    with gr.Tab("02 · ÁLGEBRA"):
        gr.Markdown("<div class='section-title'>LABORATÓRIO ALGÉBRICO</div><div class='section-sub'>Insira uma expressão, acompanhe a pré-visualização e examine as transformações.</div>")
        with gr.Row():
            with gr.Column(scale=3):
                alg_examples = gr.Dropdown(
                    choices=["(x² − x³)/(x³ + x⁵)", "x³ + x²", "(x + 2)³", "(x³ + 2x²)/(x + 2)", "2²ˣ − 5·2ˣ + 4", "Expressão personalizada"],
                    value="(x² − x³)/(x³ + x⁵)", label="EXEMPLOS PREPARADOS",
                )
                alg_input = gr.Textbox(
                    value="(x^2-x^3)/(x^3+x^5)", label="EXPRESSÃO MATEMÁTICA", lines=4,
                    elem_id="neoex-algebra-input", placeholder="Ex.: (x^2-x^3)/(x^3+x^5)",
                    info="Use ^ para expoentes. Parênteses, colchetes e chaves são fechados automaticamente; veja a expressão formatada logo abaixo.",
                )
                alg_preview = gr.HTML(r"<div class='preview-card'>\(\frac{x^2-x^3}{x^3+x^5}\)</div>")
                alg_status = gr.Markdown("Sintaxe reconhecida")
                alg_operation = gr.Dropdown(
                    choices=["Simplificar", "Fatorar", "Desenvolver", "Colocar em evidência", "Simplificar fração", "Resolver equação", "Resolver inequação"],
                    value="Simplificar", label="OPERAÇÃO",
                )
                alg_run = gr.Button("EXECUTAR TRANSFORMAÇÃO", variant="primary")
            with gr.Column(scale=2):
                gr.HTML("""<div class='syntax-card'><div class='panel-title'>GUIA DE SINTAXE</div><div class='syntax-line'><b>Expoente</b> <code>2^3</code> <span>→</span> <strong>2³</strong></div><div class='syntax-line'><b>Multiplicação</b> <code>2*3</code> <span>→</span> <strong>2 · 3</strong></div><div class='syntax-line'><b>Divisão</b> <code>(x^2+1)/(x+1)</code> <span>→</span> <strong class='syntax-frac'><i>x² + 1</i><i>x + 1</i></strong></div><div class='syntax-line'><b>Raiz</b> <code>sqrt(16)</code> <span>→</span> <strong>√16</strong></div><div class='syntax-line'><b>Parênteses</b> <code>(x+2)^3</code> <span>→</span> <strong>(x+2)³</strong></div><div class='syntax-line'><b>Funções</b> <code>sin(x)</code> <span>→</span> <strong>sin(x)</strong></div><div class='syntax-foot'>Use * para multiplicar e explicite a multiplicação: <code>2*x</code>. Variáveis podem ser letras como x, y, a ou b. A entrada é interpretada por um analisador matemático restrito; não executa código Python.</div></div>""")
        gr.Markdown("### Resolução explicada, etapa por etapa")
        alg_step = gr.HTML("<div class='algebra-step-card'>As transformações aparecerão aqui após executar a operação.</div>")
        alg_count = gr.Markdown("Aguardando expressão", elem_classes=["counter"])

        def algebra_input_changed(source):
            preview, status = _algebra_preview(source)
            return preview, status, gr.update(value="Expressão personalizada")

        alg_input.input(algebra_input_changed, [alg_input], [alg_preview, alg_status, alg_examples], trigger_mode="always_last")

        def choose_alg_example(label):
            if label == "Expressão personalizada":
                return gr.skip(), gr.skip(), gr.skip()
            mapping = {
                "(x² − x³)/(x³ + x⁵)": "(x^2-x^3)/(x^3+x^5)",
                "x³ + x²": "x^3+x^2",
                "(x + 2)³": "(x+2)^3",
                "(x³ + 2x²)/(x + 2)": "(x^3+2*x^2)/(x+2)",
                "2²ˣ − 5·2ˣ + 4": "2^(2x)-5*2^x+4",
            }
            value = mapping[label]
            preview, status = _algebra_preview(value)
            return value, preview, status

        alg_examples.change(choose_alg_example, alg_examples, [alg_input, alg_preview, alg_status])

        def run_alg(source, operation):
            try:
                steps, result, _restrictions = build_algebra_steps(source, operation)
                count = rf"{len(steps)} etapas apresentadas · resultado: \({result}\)"
                return _steps_stack_html(steps), count
            except Exception as exc:
                message = html.escape(str(exc))
                return f"<div class='algebra-step-card' style='border-color:#ff7188'>Não foi possível executar: {message}</div>", "Verifique a entrada. A expressão não foi transformada."

        alg_run.click(run_alg, [alg_input, alg_operation], [alg_step, alg_count])
