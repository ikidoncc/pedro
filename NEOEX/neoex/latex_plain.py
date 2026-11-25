"""Conversion from TeX math fragments to safe Unicode plain text."""
from __future__ import annotations

import re

_SUPERSCRIPT_CHARS = str.maketrans({
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
    "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
    "+": "⁺", "-": "⁻", "=": "⁼", "(": "⁽", ")": "⁾",
    "n": "ⁿ", "i": "ⁱ", "x": "ˣ", "y": "ʸ", "m": "ᵐ",
})
_SUBSCRIPT_CHARS = str.maketrans({
    "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄",
    "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉",
    "+": "₊", "-": "₋", "i": "ᵢ", "n": "ₙ", "x": "ₓ",
})


def superscript_unicode(value: str) -> str:
    """Translate ASCII exponent characters into Unicode superscripts."""
    return value.translate(_SUPERSCRIPT_CHARS)


def latex_fragment_to_plain_text(value: str) -> str:
    """Convert common TeX fragments into readable Unicode for graph cards and fallbacks."""
    text = str(value).replace(r"\(", "").replace(r"\)", "")
    text = text.replace(r"\[", "").replace(r"\]", "")
    text = text.replace(r"\left", "").replace(r"\right", "")
    text = text.replace(r"\big", "").replace(r"\Big", "")
    text = text.replace(r"\,", " ").replace(r"\;", " ").replace(r"\quad", " ").replace(r"\qquad", " ")
    text = text.replace(r"\!", "")

    macro_map = {
        r"\Longrightarrow": "⇒", r"\longrightarrow": "→", r"\Rightarrow": "⇒", r"\rightarrow": "→",
        r"\cdot": "·", r"\times": "×", r"\div": "÷", r"\neq": "≠", r"\ne": "≠",
        r"\geq": "≥", r"\ge": "≥", r"\leq": "≤", r"\le": "≤", r"\approx": "≈",
        r"\infty": "∞", r"\pi": "π", r"\mathbb{R}": "ℝ", r"\mathbb{Z}": "ℤ",
        r"\mathbb{N}": "ℕ", r"\emptyset": "∅", r"\varnothing": "∅", r"\setminus": "∖",
        r"\notin": "∉", r"\in": "∈", r"\land": " e ", r"\lor": " ou ",
    }
    for source, target in sorted(macro_map.items(), key=lambda item: len(item[0]), reverse=True):
        text = text.replace(source, target)

    # Preserve escaped set braces while removing TeX's grouping braces later.
    text = text.replace(r"\{", "\uE000").replace(r"\}", "\uE001")
    text = re.sub(r"\\(?:text|mathrm|operatorname)\{([^{}]*)\}", r"\1", text)

    def read_tex_group(source: str, start: int):
        if start >= len(source) or source[start] != "{":
            return None, start
        depth = 0
        for cursor in range(start, len(source)):
            if source[cursor] == "{":
                depth += 1
            elif source[cursor] == "}":
                depth -= 1
                if depth == 0:
                    return source[start + 1:cursor], cursor + 1
        return None, start

    def convert_nested_fractions(source: str) -> str:
        output = []
        cursor = 0
        while cursor < len(source):
            token = None
            for candidate in (r"\dfrac", r"\tfrac", r"\frac"):
                if source.startswith(candidate + "{", cursor):
                    token = candidate
                    break
            if token is None:
                output.append(source[cursor])
                cursor += 1
                continue
            numerator, after_num = read_tex_group(source, cursor + len(token))
            denominator, after_den = read_tex_group(source, after_num) if numerator is not None else (None, after_num)
            if numerator is None or denominator is None:
                output.append(source[cursor])
                cursor += 1
                continue
            num = convert_nested_fractions(numerator)
            den = convert_nested_fractions(denominator)
            output.append(f"({num})/({den})")
            cursor = after_den
        return "".join(output)

    text = convert_nested_fractions(text)

    text = re.sub(r"\\sqrt\[([^\]]+)\]\{([^{}]+)\}", lambda m: f"raiz {m.group(1)} de ({m.group(2)})", text)
    text = re.sub(r"\\sqrt\{([^{}]+)\}", lambda m: f"√({m.group(1)})", text)

    def superscript(match):
        body = match.group(1)
        mapped = body.translate(_SUPERSCRIPT_CHARS)
        return mapped if all(ch in "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱˣʸᵐ,." for ch in mapped) else f"^({body})"

    def subscript(match):
        body = match.group(1)
        mapped = body.translate(_SUBSCRIPT_CHARS)
        return mapped if all(ch in "₀₁₂₃₄₅₆₇₈₉₊₋ᵢₙₓ" for ch in mapped) else f"_({body})"

    text = re.sub(r"\^\{([^{}]+)\}", superscript, text)
    text = re.sub(r"\^([+-]?\d+|[A-Za-z])", lambda m: m.group(1).translate(_SUPERSCRIPT_CHARS), text)
    text = re.sub(r"_\{([^{}]+)\}", subscript, text)
    text = re.sub(r"_([A-Za-z0-9])", lambda m: m.group(1).translate(_SUBSCRIPT_CHARS), text)

    text = re.sub(r"\{([^{}]*)\}", r"\1", text)
    text = text.replace("\uE000", "{").replace("\uE001", "}")
    text = re.sub(r"\\([A-Za-z]+)", r"\1", text)
    text = text.replace("\\", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text
