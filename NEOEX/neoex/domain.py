"""Real-domain analysis shared by the algebra and graph laboratories."""
from __future__ import annotations

import sympy as sp
from functools import lru_cache
from sympy.calculus.util import continuous_domain


def _multivariable_conditions(expr: sp.Expr):
    """Conservative symbolic restrictions for real expressions in >1 variable."""
    conditions = []
    for node in sp.preorder_traversal(expr):
        if isinstance(node, sp.Pow):
            base, exponent = node.base, node.exp
            if exponent == 0 or exponent.is_negative:
                conditions.append(sp.Ne(base, 0))
            if exponent.is_Rational:
                denominator = int(exponent.q)
                if denominator % 2 == 0:
                    conditions.append(sp.Gt(base, 0) if exponent.is_negative else sp.Ge(base, 0))
            elif exponent.is_real is True and exponent.is_integer is not True:
                conditions.append(sp.Gt(base, 0) if exponent.is_negative else sp.Ge(base, 0))
            elif exponent.free_symbols:
                conditions.append(sp.Gt(base, 0))
        if node.func is sp.log and node.args:
            conditions.append(sp.Gt(node.args[0], 0))
        if node.func is sp.tan and node.args:
            conditions.append(sp.Ne(sp.cos(node.args[0]), 0))

    # Remove exact duplicates and simplify the resulting conjunction.
    unique = []
    for condition in conditions:
        simplified = sp.simplify(condition)
        if simplified is sp.true:
            continue
        if simplified not in unique:
            unique.append(simplified)
    return unique


@lru_cache(maxsize=256)
def real_domain(expr: sp.Expr):
    """Return (variable, real domain, message) for a univariate expression.

    The original, unevaluated expression should be passed so removable
    discontinuities and denominator exclusions remain part of the domain.
    For several free variables, the caller should use the conservative
    symbolic restrictions returned by :func:`real_domain_latex`.
    """
    symbols = sorted(expr.free_symbols, key=lambda s: s.name)
    if not symbols:
        return None, sp.S.Reals, "A expressão não contém variável. Como expressão numérica, está definida; interpretada como função constante, seu domínio é ℝ."
    if len(symbols) > 1:
        return None, None, "O domínio foi descrito por condições reais para as variáveis presentes."
    variable = symbols[0]
    try:
        domain = continuous_domain(expr, variable, sp.S.Reals)
        # SymPy may simplify x**0 to 1. When the original tree is preserved,
        # keep the conventional base != 0 condition for a zero exponent.
        for node in sp.preorder_traversal(expr):
            if not isinstance(node, sp.Pow):
                continue
            if node.exp == 0:
                try:
                    zeros = sp.solveset(sp.Eq(node.base, 0), variable, domain=sp.S.Reals)
                    if zeros != sp.EmptySet:
                        domain = sp.Complement(domain, zeros)
                except Exception:
                    pass
            # A variable exponent over a variable base is real-valued on the
            # usual real branch only when the base is strictly positive.
            # Example: x^x has domain (0,+infinity), not [0,+infinity).
            if node.exp.free_symbols and node.base.has(variable):
                try:
                    positive_base = sp.solve_univariate_inequality(
                        sp.Gt(node.base, 0), variable, relational=False
                    )
                    domain = sp.Intersection(domain, positive_base)
                except Exception:
                    # If the positivity set cannot be established safely,
                    # keep the domain conservative rather than enlarging it.
                    pass
        return variable, domain, "Domínio real calculado a partir da expressão original, preservando denominadores, raízes, logaritmos e potências de base variável."
    except Exception:
        return variable, None, "O motor simbólico não conseguiu determinar o domínio real desta expressão com segurança."


def real_domain_latex(expr: sp.Expr) -> tuple[str, str]:
    """Return a presentation formula and explanation for the real domain."""
    variable, domain, message = real_domain(expr)
    symbols = sorted(expr.free_symbols, key=lambda s: s.name)
    if len(symbols) > 1:
        conditions = _multivariable_conditions(expr)
        tuple_symbols = ",".join(sp.latex(symbol) for symbol in symbols)
        ambient = rf"\mathbb{{R}}^{{{len(symbols)}}}"
        if not conditions:
            formula = rf"D={ambient}"
        else:
            condition_text = r"\;\text{ e }\;".join(sp.latex(item) for item in conditions)
            formula = rf"D=\left\{{({tuple_symbols})\in {ambient}\;\middle|\;{condition_text}\right\}}"
        return formula, "Domínio real descrito por condições sobre todas as variáveis."
    if domain is None:
        if variable is None:
            return r"D=\text{não determinado automaticamente}", message
        return rf"D_{{{sp.latex(variable)}}}=\text{{não determinado automaticamente}}", message
    if variable is None:
        return r"D=\mathbb{R}", message
    if domain == sp.S.Reals:
        formula = rf"D_{{{sp.latex(variable)}}}=\mathbb{{R}}"
    else:
        try:
            excluded = sp.Complement(sp.S.Reals, domain)
        except Exception:
            excluded = None
        if isinstance(excluded, sp.FiniteSet):
            excluded_items = ",".join(sp.latex(v) for v in sorted(excluded, key=sp.default_sort_key))
            formula = rf"D_{{{sp.latex(variable)}}}=\mathbb{{R}}\setminus\{{{excluded_items}\}}"
        else:
            formula = rf"D_{{{sp.latex(variable)}}}={sp.latex(domain)}"
    return formula, message
