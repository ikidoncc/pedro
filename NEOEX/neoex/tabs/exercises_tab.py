"""Tab 04: Randomized practice exercises with step-by-step solutions."""
from __future__ import annotations

import html
import re

import gradio as gr

from ..exercises import make_question
from ..latex_plain import latex_fragment_to_plain_text, superscript_unicode


def _pretty_exercise_text(value: str) -> str:
    safe = html.escape(str(value))
    safe = re.sub(r"\^\(([^)]*)\)", lambda m: f"<sup>{html.escape(m.group(1))}</sup>", safe)
    safe = re.sub(r"\^([+-]?\d+|[A-Za-z])", lambda m: f"<sup>{html.escape(m.group(1))}</sup>", safe)
    safe = safe.replace("*", " · ")
    return safe


def _pretty_exercise_choice(value: str) -> str:
    safe = str(value).replace("*", " · ")
    safe = re.sub(r"\^\(([^)]*)\)", lambda m: superscript_unicode(m.group(1)), safe)
    safe = re.sub(r"\^([+-]?\d+|[A-Za-z])", lambda m: superscript_unicode(m.group(1)), safe)
    return safe


def _exercise_prompt(q):
    return f"<div class='exercise-prompt'>◆ &nbsp; {_pretty_exercise_text(q['prompt'])}</div>"


def _exercise_radio_choices(q):
    letters = "ABCD"
    return [(f"{letters[i]}   ·   {_pretty_exercise_choice(value)}", letters[i]) for i, value in enumerate(q["options"])]


def _exercise_solution_html(q, selected, correct):
    selected_text = q["options"]["ABCD".index(selected)]
    correct_letter = "ABCD"[q["options"].index(q["answer"])]
    if correct:
        verdict = "<span style='color:#70f4a0'>✓ RESPOSTA CORRETA</span>"
    else:
        verdict = (
            "<span style='color:#ff8296'>✕ RESPOSTA INCORRETA</span>"
            f"<div class='exercise-solution-explanation'>Você marcou <b>{html.escape(_pretty_exercise_choice(selected_text))}</b>. "
            f"A alternativa correta é <b>{correct_letter}</b>: <b>{html.escape(_pretty_exercise_choice(q['answer']))}</b>.</div>"
        )
    solution_steps = q.get("solution_steps", [])
    cards = []
    for index, (title, formula, explanation) in enumerate(solution_steps, 1):
        final_class = " exercise-final" if index == len(solution_steps) else ""
        fallback_formula = html.escape(latex_fragment_to_plain_text(formula), quote=True)
        cards.append(
            f"<div class='exercise-solution-step{final_class}'>"
            f"<h4>ETAPA {index:02d} · {html.escape(title)}</h4>"
            f"<div class='exercise-solution-formula' data-neoex-tex-fallback='{fallback_formula}'>\\[{formula}\\]</div>"
            f"<div class='exercise-solution-explanation'>{html.escape(explanation)}</div>"
            "</div>"
        )
    return (
        "<div class='exercise-solution'>"
        f"<div class='exercise-solution-verdict'>{verdict}</div>"
        "<h3 style='color:#eaf5ff;margin:8px 0 12px'>Resolução explicada, etapa por etapa</h3>"
        + "".join(cards)
        + "</div>"
    )


def build_exercises_tab():
    """Render the practice exercises tab inside a Blocks context."""
    initial_question = make_question("Básico")
    with gr.Tab("04 · EXERCÍCIOS"):
        gr.Markdown("<div class='section-title'>EXERCÍCIOS</div><div class='section-sub'>Escolha o nível, marque uma alternativa e acompanhe a resolução comentada.</div>")
        exercise_level = gr.Radio(choices=["Básico", "Intermediário", "Difícil"], value="Básico", label="NÍVEL DE DIFICULDADE", interactive=True, elem_classes=["exercise-level"])
        exercise_new = gr.Button("SORTEAR NOVA QUESTÃO", variant="primary")
        exercise_prompt = gr.HTML(_exercise_prompt(initial_question))
        exercise_options = gr.Radio(choices=_exercise_radio_choices(initial_question), value=None, label="ALTERNATIVAS · SELECIONE UMA RESPOSTA", interactive=True, elem_classes=["exercise-options"])
        exercise_check = gr.Button("CORRIGIR RESPOSTA", variant="primary")
        exercise_feedback = gr.HTML("<div class='exercise-solution'>Escolha uma alternativa e clique em corrigir para ver a resolução completa.</div>")
        exercise_state = gr.State(initial_question)

        def new_exercise(level):
            q = make_question(level)
            return q, _exercise_prompt(q), gr.update(choices=_exercise_radio_choices(q), value=None), "Nova questão carregada. Marque uma alternativa."

        exercise_new.click(new_exercise, exercise_level, [exercise_state, exercise_prompt, exercise_options, exercise_feedback])
        exercise_level.change(new_exercise, exercise_level, [exercise_state, exercise_prompt, exercise_options, exercise_feedback])

        def check_exercise(q, choice):
            if not choice:
                return "<div class='exercise-solution'>Selecione uma alternativa antes de corrigir.</div>"
            selected = q["options"]["ABCD".index(choice)]
            return _exercise_solution_html(q, choice, selected == q["answer"])

        exercise_check.click(check_exercise, [exercise_state, exercise_options], [exercise_feedback])
