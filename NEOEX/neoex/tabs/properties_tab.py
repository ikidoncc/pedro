"""Tab 01: Interactive exponent laws demonstrations."""
from __future__ import annotations

import html
import re

import gradio as gr

from ..latex_plain import latex_fragment_to_plain_text
from ..properties import PROPERTIES, PROPERTY_ORDER


def _animate_formula_markup(formula: str) -> str:
    """Color every superscript and reveal individual mathematical tokens."""
    palette = ("blue", "red", "cyan", "pink", "gold", "purple")
    exponent_index = 0
    sup_pattern = re.compile(r"<sup(?P<attrs>[^>]*)>(?P<body>.*?)</sup>", re.I | re.S)

    def color_sup(match):
        nonlocal exponent_index
        attrs = match.group("attrs") or ""
        classes = re.search(r"class=['\"]([^'\"]*)['\"]", attrs)
        existing = classes.group(1) if classes else ""
        color = palette[exponent_index % len(palette)]
        exponent_index += 1
        if not re.search(r"exp-(purple|red|pink|blue|cyan|gold)", existing):
            if classes:
                attrs = attrs[:classes.start(1)] + existing + " exp-" + color + attrs[classes.end(1):]
            else:
                attrs += f" class='exp-{color}'"
        body = match.group("body")
        if not re.search(r"class=['\"][^'\"]*exp-(purple|red|pink|blue|cyan|gold)", body):
            token_pattern = re.compile(r"(?<![A-Za-z0-9])([+−-]?\s*(?:\d+(?:/\d+)?|[A-Za-z]+))(?![A-Za-z0-9])")
            body_parts = []
            last = 0
            inner_index = 0
            for token_match in token_pattern.finditer(body):
                body_parts.append(body[last:token_match.start()])
                inner_color = palette[inner_index % len(palette)]
                body_parts.append(f"<span class='exp-{inner_color}'>{token_match.group(1)}</span>")
                inner_index += 1
                last = token_match.end()
            body_parts.append(body[last:])
            body = "".join(body_parts)
        return f"<sup{attrs}>{body}</sup>"

    superscript_translation = {
        "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
        "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
        "⁻": "-", "⁺": "+", "⁽": "(", "⁾": ")",
        "ⁿ": "n", "ᵐ": "m", "ˣ": "x", "ʸ": "y",
    }
    superscript_chars = "".join(superscript_translation)
    unicode_sup = re.compile(rf"(?<=[A-Za-z0-9)])([{re.escape(superscript_chars)}]+)")
    formula = unicode_sup.sub(
        lambda match: "<sup>" + "".join(superscript_translation[ch] for ch in match.group(1)) + "</sup>",
        formula,
    )
    formula = sup_pattern.sub(color_sup, formula)
    parts = re.split(r"(<[^>]+>)", formula)
    token_index = 0
    for i, part in enumerate(parts):
        if not part or part.startswith("<"):
            continue
        tokens = re.split(r"(\s+|[=+−\-·/*()])", part)
        decorated = []
        for token in tokens:
            if not token or token.isspace():
                decorated.append(token)
            elif token in {"·", "*", "/", "+", "−", "-", "=", "(", ")"}:
                symbol = "·" if token == "*" else token
                decorated.append(f"<span class='equation-operator' style='--reveal-delay:{token_index*.055:.3f}s'>{symbol}</span>")
                token_index += 1
            else:
                decorated.append(f"<span class='equation-token' style='--reveal-delay:{token_index*.055:.3f}s'>{token}</span>")
                token_index += 1
        parts[i] = "".join(decorated)
    return "".join(parts)


def _power_of_power_visual(index: int) -> str:
    def blue(delay=0):
        return f"<span class='power-factor power-blue' style='--delay:{delay:.2f}s'>5</span>"
    dot = "<span class='power-dot'>·</span>"
    if index == 0:
        return "<div class='power-visual'><div class='power-equation'><span class='power-red'>(</span><span class='power-base'>5<sup class='power-blue'>2</sup></span><span class='power-red'>)</span><sup class='power-red'>3</sup></div><div class='power-inner-note'>AZUL: 2 FATORES POR BLOCO · VERMELHO: 3 BLOCOS</div></div>"
    if index == 1:
        blocks = "".join(f"<div class='power-block' style='--delay:{i*.14:.2f}s'><div class='power-block-label'>BLOCO {i+1} / 3</div><div class='power-block-math'><span class='power-red'>(</span><span class='power-base'>5<sup class='power-blue'>2</sup></span><span class='power-red'>)</span></div></div>" for i in range(3))
        return f"<div class='power-visual'><div class='power-equivalence'><span class='power-red'>(</span><span class='power-base'>5<sup class='power-blue'>2</sup></span><span class='power-red'>)</span><sup class='power-red'>3</sup> → três cópias</div><div class='power-block-grid'>{blocks}</div><div class='power-inner-note'>O EXPOENTE EXTERNO 3 CRIA TRÊS BLOCOS IGUAIS</div></div>"
    if index == 2:
        blocks = "".join(f"<div class='power-block' style='--delay:{i*.18:.2f}s'><div class='power-block-label'>BLOCO {i+1} / 3</div><div class='power-factor-row'>{blue(i*.12)}{dot}{blue((i+.5)*.12)}</div><div class='power-group-label'>2 fatores azuis</div></div>" for i in range(3))
        return f"<div class='power-visual'><div class='power-inner-note'>ABRIMOS CADA EXPOENTE 2: CADA BLOCO VIRA 5 · 5</div><div class='power-block-grid'>{blocks}</div></div>"
    if index == 3:
        blocks = "".join(f"<div class='power-block' style='--delay:{i*.14:.2f}s'><div class='power-block-label'>GRUPO {i+1} · ORIGEM EXTERNA 3</div><div class='power-factor-row'>{blue(i*.08)}{dot}{blue((i+.5)*.08)}</div><div class='power-group-label'>2 fatores</div></div>" for i in range(3))
        return f"<div class='power-visual'><div class='power-block-grid'>{blocks}</div><div class='power-equivalence'><span class='power-blue'>2 fatores por bloco</span> × <span class='power-red'>3 blocos</span></div></div>"
    if index == 4:
        factors = "".join(blue(i*.09) + (dot if i < 5 else "") for i in range(6))
        return f"<div class='power-visual'><div class='power-inner-note'>OS PARÊNTESES SE ABREM; AS SEIS BASES PERMANECEM AZUIS</div><div class='power-equation' style='width:100%'><div class='power-factor-row'>{factors}</div></div></div>"
    if index == 5:
        return "<div class='power-visual'><div class='power-count-grid'><div class='power-count-card'><span class='power-count-number power-blue'>2</span><span class='power-count-caption'>fatores por bloco</span></div><div class='power-count-card'><span class='power-count-number power-red'>3</span><span class='power-count-caption'>blocos iguais</span></div></div><div class='power-equivalence'>2 + 2 + 2 = 6</div><div class='power-equivalence'><span class='power-blue'>2</span> · <span class='power-red'>3</span> = <span class='power-gold'>6</span></div></div>"
    if index == 6:
        return "<div class='power-visual'><div class='power-equation'>5<sup><span class='power-blue'>2</span><span class='power-red'> · 3</span></sup> = 5<sup class='power-gold'>6</sup></div><div class='power-inner-note'>EXPOENTE INTERNO × EXPOENTE EXTERNO = EXPOENTE TOTAL</div></div>"
    return "<div class='power-visual'><div class='power-equation'>5<sup class='power-gold'>6</sup> = <span style='color:#70f4a0;text-shadow:0 0 14px #45ff99'>15 625</span></div><div class='power-inner-note'>TRÊS BLOCOS DE DOIS FATORES = SEIS FATORES</div></div>"


def _prop_stage_html(prop_key: str, example_label: str, index: int) -> str:
    example = next(e for e in PROPERTIES[prop_key].examples if e.label == example_label)
    step = example.steps[index]
    total = len(example.steps)
    visual = step.visual
    formula = step.formula
    canonical = prop_key == "mult" and example_label == "3³ · 3⁵"
    nested_power = prop_key == "power" and example_label == "(5²)³"
    factor = lambda color, delay: f"<span class='factor {color}' style='animation-delay:{delay:.2f}s'>3</span>"
    if nested_power:
        display = _power_of_power_visual(index)
    elif canonical and visual == "grouped":
        purple_factors = "<span class='equation-operator'>·</span>".join(factor("purple", i * .12) for i in range(3))
        red_factors = "<span class='equation-operator'>·</span>".join(factor("red", i * .12) for i in range(5))
        display = f"""
        <div class='grouped-stage'>
          <div class='factor-group' style='color:#b58cff'><div class='factor-row'>{purple_factors}</div><div class='brace'></div><div class='group-label'>3</div><div class='micro-label'>fatores · origem roxa</div></div>
          <div class='factor-group' style='color:#ff657e'><div class='factor-row'>{red_factors}</div><div class='brace'></div><div class='group-label'>5</div><div class='micro-label'>fatores · origem vermelha</div></div>
        </div>"""
    elif canonical and visual == "first_factors":
        display = "<div class='math-display animated-equation'>" + " <span class='equation-operator'>·</span> ".join(factor("purple", i * .12) for i in range(3)) + "</div>"
    elif canonical and visual == "second_factors":
        display = "<div class='math-display animated-equation'>" + " <span class='equation-operator'>·</span> ".join(factor("red", i * .12) for i in range(5)) + "</div>"
    elif canonical and visual == "joined":
        display = "<div class='math-display animated-equation'>" + " <span class='equation-operator'>·</span> ".join([factor("purple", i * .12) for i in range(3)] + [factor("red", (i + 3) * .12) for i in range(5)]) + "</div>"
    else:
        decorated = _animate_formula_markup(formula or "\\text{Observe os grupos de fatores}")
        display = f"<div class='math-display animated-equation'><div class='formula-plate'>{decorated}</div></div>"
    safe_title = html.escape(step.title)
    if prop_key == "power":
        legend = "<div class='stage-legend'><span><i class='legend-dot' style='background:#63aaff;color:#63aaff'></i> expoente interno · fatores</span><span><i class='legend-dot red-dot'></i> expoente externo · blocos</span><span><i class='legend-dot' style='background:#ffd36b;color:#ffd36b'></i> resultado</span></div>"
    elif prop_key == "mult":
        legend = "<div class='stage-legend'><span><i class='legend-dot' style='background:#b58cff;color:#b58cff'></i> primeira potência</span><span><i class='legend-dot red-dot'></i> segunda potência</span><span><i class='legend-dot' style='background:#67f79a;color:#67f79a'></i> fatores reunidos</span></div>"
    elif prop_key == "div":
        legend = "<div class='stage-legend'><span><i class='legend-dot' style='background:#ff657e;color:#ff657e'></i> numerador</span><span><i class='legend-dot' style='background:#63aaff;color:#63aaff'></i> denominador</span><span><i class='legend-dot' style='background:#67f79a;color:#67f79a'></i> fatores restantes</span></div>"
    else:
        legend = "<div class='stage-legend'><span><i class='legend-dot' style='background:#63aaff;color:#63aaff'></i> expoente / fator de origem</span><span><i class='legend-dot red-dot'></i> segundo grupo</span><span><i class='legend-dot' style='background:#ffd36b;color:#ffd36b'></i> transformação final</span></div>"
    return f"""<div class='stage-shell'>
      <div class='stage-top'><span class='stage-number'>NEOEX / LABORATÓRIO DE POTÊNCIAS</span><span>{index+1:02d} / {total:02d}</span></div>
      <div class='micro-label' style='text-align:center;margin-bottom:22px'>{safe_title}</div>
      {display}
      {legend}
    </div>"""


def _prop_text(prop_key, example_label, index):
    example = next(e for e in PROPERTIES[prop_key].examples if e.label == example_label)
    step = example.steps[index]
    return step.explanation, f"ETAPA {index+1} DE {len(example.steps)} · {step.title}"


def _property_header(prop_key):
    item = PROPERTIES[prop_key]
    rule_math = {
        "mult": r"a^m\cdot a^n=a^{m+n}",
        "div": r"\frac{a^m}{a^n}=a^{m-n},\quad a\ne0",
        "power": r"(a^m)^n=a^{mn}",
        "product": r"(ab)^n=a^n b^n",
        "quotient": r"\left(\frac{a}{b}\right)^n=\frac{a^n}{b^n},\quad b\ne0",
        "zero": r"a^0=1,\quad a\ne0",
        "negative": r"a^{-n}=\frac{1}{a^n},\quad a\ne0",
        "fractional": r"a^{m/n}=\sqrt[n]{a^m}",
    }[prop_key]
    rule_fallback = html.escape(latex_fragment_to_plain_text(rule_math), quote=True)
    return (
        "<div class='property-info'>"
        f"<strong>{html.escape(item.label)}</strong>"
        f"<div class='rule-line'><span>Regra:</span> <span data-neoex-tex-fallback='{rule_fallback}'>\\({rule_math}\\)</span></div>"
        f"<p>{html.escape(item.note)}</p>"
        "</div>"
    )


def build_properties_tab():
    """Render the exponent properties demonstration tab inside a Blocks context."""
    prop_keys = [(PROPERTIES[k].label, k) for k in PROPERTY_ORDER]
    first_prop = PROPERTY_ORDER[0]
    first_example = PROPERTIES[first_prop].examples[0].label
    first_step = _prop_stage_html(first_prop, first_example, 0)
    first_text, first_counter = _prop_text(first_prop, first_example, 0)

    with gr.Tab("01 · PROPRIEDADES"):
        gr.Markdown("<div class='section-title'>PROPRIEDADES DA POTENCIAÇÃO</div><div class='section-sub'>Observe os fatores surgirem, serem agrupados e transformados. Avance no seu próprio ritmo.</div>")
        with gr.Row():
            prop_choice = gr.Dropdown(choices=prop_keys, value=first_prop, label="PROPRIEDADE", scale=2)
            prop_example = gr.Dropdown(choices=[e.label for e in PROPERTIES[first_prop].examples], value=first_example, label="EXEMPLO", scale=2)
        prop_rule = gr.HTML(_property_header(first_prop))
        prop_stage = gr.HTML(first_step)
        prop_explain = gr.Markdown(first_text, elem_classes=["explain"])
        prop_counter = gr.Markdown(first_counter, elem_classes=["counter"])
        with gr.Row():
            prop_start = gr.Button("INICIAR DEMONSTRAÇÃO", variant="primary")
            prop_prev = gr.Button("← PASSO ANTERIOR")
            prop_next = gr.Button("PRÓXIMO PASSO →", variant="primary")
            prop_reset = gr.Button("REINICIAR")
        with gr.Row():
            prop_play = gr.Button("▶ REPRODUZIR", variant="secondary")
            prop_pause = gr.Button("Ⅱ PAUSAR", variant="secondary")
            prop_speed = gr.Dropdown(
                choices=[("Muito rápido · 0,6 s", 0.6), ("Rápido · 1,0 s", 1.0), ("Normal · 1,5 s", 1.5), ("Lento · 2,0 s", 2.0), ("Muito lento · 3,0 s", 3.0)],
                value=1.5, label="INTERVALO ENTRE ETAPAS", interactive=True,
            )
        prop_idx = gr.State(0)
        timer = gr.Timer(value=1.5, active=False)

        def prop_select(pk, ex=None):
            exs = [e.label for e in PROPERTIES[pk].examples]
            chosen = ex if ex in exs else exs[0]
            return gr.Dropdown(choices=exs, value=chosen), _property_header(pk), 0, _prop_stage_html(pk, chosen, 0), *_prop_text(pk, chosen, 0)

        def prop_example_select(pk, ex):
            return 0, _prop_stage_html(pk, ex, 0), *_prop_text(pk, ex, 0)

        def prop_move(pk, ex, idx, delta):
            example = next(e for e in PROPERTIES[pk].examples if e.label == ex)
            new = max(0, min(len(example.steps) - 1, idx + delta))
            return new, _prop_stage_html(pk, ex, new), *_prop_text(pk, ex, new)

        prop_choice.change(prop_select, [prop_choice, prop_example], [prop_example, prop_rule, prop_idx, prop_stage, prop_explain, prop_counter])
        prop_example.change(prop_example_select, [prop_choice, prop_example], [prop_idx, prop_stage, prop_explain, prop_counter])
        prop_start.click(lambda pk, ex: (0, _prop_stage_html(pk, ex, 0), *_prop_text(pk, ex, 0), gr.Timer(active=False)), [prop_choice, prop_example], [prop_idx, prop_stage, prop_explain, prop_counter, timer])
        prop_prev.click(lambda pk, ex, i: (*prop_move(pk, ex, i, -1), gr.Timer(active=False)), [prop_choice, prop_example, prop_idx], [prop_idx, prop_stage, prop_explain, prop_counter, timer])
        prop_next.click(lambda pk, ex, i: (*prop_move(pk, ex, i, 1), gr.Timer(active=False)), [prop_choice, prop_example, prop_idx], [prop_idx, prop_stage, prop_explain, prop_counter, timer])
        prop_reset.click(lambda pk, ex: (0, _prop_stage_html(pk, ex, 0), *_prop_text(pk, ex, 0), gr.Timer(active=False)), [prop_choice, prop_example], [prop_idx, prop_stage, prop_explain, prop_counter, timer])
        prop_play.click(lambda speed: gr.Timer(value=float(speed), active=True), prop_speed, timer)
        prop_pause.click(lambda: gr.Timer(active=False), None, timer)
        prop_speed.change(lambda speed: gr.Timer(value=float(speed), active=False), prop_speed, timer)

        def tick(pk, ex, idx, speed):
            example = next(e for e in PROPERTIES[pk].examples if e.label == ex)
            new = min(len(example.steps) - 1, idx + 1)
            active = new < len(example.steps) - 1
            return new, _prop_stage_html(pk, ex, new), *_prop_text(pk, ex, new), gr.Timer(value=float(speed), active=active)

        timer.tick(tick, [prop_choice, prop_example, prop_idx, prop_speed], [prop_idx, prop_stage, prop_explain, prop_counter, timer])
