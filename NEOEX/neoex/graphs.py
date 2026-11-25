"""Fast symbolic/numeric graph preparation for the NEOEX canvas laboratory.

The browser draws the curve with Canvas (no Plotly dependency). Python only
parses and validates the expression, compiles a safe JS expression from the
SymPy tree, and computes roots/critical points inside the visible interval.
"""
from __future__ import annotations

from functools import lru_cache
import math
import numpy as np
import sympy as sp

from .parser import parse_math, format_math_latex, ExpressionError
from .domain import real_domain, real_domain_latex

X = sp.Symbol("x", real=True)


@lru_cache(maxsize=256)
def _numpy_function(expr: sp.Expr):
    try:
        return sp.lambdify(X, expr, modules=[{"Abs": np.abs}, "numpy"], cse=True)
    except Exception as exc:
        raise ExpressionError("Não foi possível preparar esta expressão para avaliação numérica.") from exc


def evaluate(expr: sp.Expr, value: float) -> float | None:
    try:
        result = _numpy_function(expr)(float(value))
        arr = np.asarray(result)
        if arr.ndim:
            if arr.size != 1:
                return None
            result = arr.reshape(-1)[0]
        value = float(np.real(result))
        return value if math.isfinite(value) and abs(value) < 1e12 else None
    except Exception:
        return None


@lru_cache(maxsize=256)
def _excluded_real_points(expr: sp.Expr, variable: sp.Symbol = X) -> tuple[float, ...]:
    """Find finite excluded points from negative/zero powers, bounded by degree."""
    excluded: set[float] = set()
    for node in sp.preorder_traversal(expr):
        if isinstance(node, sp.Pow) and (node.exp.is_negative or node.exp == 0):
            try:
                poly = sp.Poly(node.base, variable)
                if 0 < poly.degree() <= 8:
                    for root in poly.real_roots():
                        if root.is_real and root.is_number:
                            excluded.add(float(root))
            except Exception:
                continue
    return tuple(sorted(excluded))


def _js_number(value: sp.Expr) -> str:
    if isinstance(value, sp.Integer):
        return str(int(value))
    if isinstance(value, sp.Rational):
        return f"({int(value.p)}/{int(value.q)})"
    if isinstance(value, sp.Float):
        number = float(value)
        if not math.isfinite(number):
            raise ExpressionError("Constante numérica fora do intervalo permitido.")
        return repr(number)
    raise ExpressionError("Constante numérica não suportada no gráfico.")


def to_javascript(expr: sp.Expr) -> str:
    """Serialize a validated SymPy expression to a restricted JS expression.

    No user text is copied into executable code. Only whitelisted SymPy nodes
    are emitted, which keeps the browser evaluator small and predictable.
    """
    if expr == X:
        return "x"
    if expr == sp.pi:
        return "Math.PI"
    if expr == sp.E:
        return "Math.E"
    if expr.is_Number:
        return _js_number(expr)
    if isinstance(expr, sp.Symbol):
        if expr.name == "x":
            return "x"
        raise ExpressionError(f"O gráfico usa x como variável. A variável {expr} não é permitida aqui.")
    if isinstance(expr, sp.Add):
        parts = [to_javascript(arg) for arg in expr.as_ordered_terms()]
        return "(" + " + ".join(parts) + ")"
    if isinstance(expr, sp.Mul):
        parts = [to_javascript(arg) for arg in expr.args]
        return "(" + " * ".join(parts) + ")"
    if isinstance(expr, sp.Pow):
        base, exponent = expr.args
        base_js = to_javascript(base)
        exp_js = to_javascript(exponent)
        # Math.pow(-a, 1/3) is NaN in JS although the real cube root exists.
        if isinstance(exponent, sp.Rational) and int(exponent.q) % 2 == 1:
            sign_factor = f"Math.sign({base_js})" if int(exponent.p) % 2 else "1"
            return f"({sign_factor} * Math.pow(Math.abs({base_js}), {exp_js}))"
        return f"Math.pow({base_js}, {exp_js})"
    function_map = {
        sp.sin: "Math.sin", sp.cos: "Math.cos", sp.tan: "Math.tan",
        sp.exp: "Math.exp", sp.log: "Math.log", sp.Abs: "Math.abs",
        sp.sqrt: "Math.sqrt",
    }
    if expr.func in function_map and len(expr.args) == 1:
        return f"{function_map[expr.func]}({to_javascript(expr.args[0])})"
    raise ExpressionError(
        "Esta expressão usa uma operação que o avaliador gráfico ainda não suporta. "
        "Use polinômios, frações, potências e as funções sqrt, abs, exp, log, sin, cos ou tan."
    )


def _real_poly_roots(expr: sp.Expr, x_min: float, x_max: float, *, max_degree: int = 16) -> list[float] | None:
    """Find distinct real polynomial roots in a bounded interval.

    Square-free reduction is essential for high multiplicities: direct numeric
    roots of (x-a)^m are ill-conditioned and can otherwise appear as many
    nearby, incorrect roots. After removing multiplicities, low-degree roots
    are isolated exactly and higher-degree simple roots use a bounded numeric
    fallback.
    """
    try:
        numerator, _denominator = sp.together(expr).as_numer_denom()
        poly = sp.Poly(numerator, X)
    except (sp.PolynomialError, TypeError, ValueError):
        return None
    if poly.is_zero:
        return []
    if poly.degree() < 0:
        return []
    try:
        square_free = poly.sqf_part()
    except Exception:
        square_free = poly
    degree = square_free.degree()
    if degree <= 0:
        return []
    if degree <= max_degree:
        try:
            intervals = square_free.intervals(eps=sp.Rational(1, 10**10))
            roots = []
            for (left, right), multiplicity in intervals:
                value = float((left + right) / 2)
                if x_min - 1e-8 <= value <= x_max + 1e-8:
                    roots.append(value)
            return _dedupe_sorted(roots, 1e-6)
        except Exception:
            pass
    # Companion-matrix roots are useful for moderate degree after square-free
    # reduction. They are checked against the normalized polynomial residual.
    if degree <= 100:
        try:
            coefficients = np.asarray([float(c) for c in square_free.all_coeffs()], dtype=float)
            scale = np.max(np.abs(coefficients))
            if not np.isfinite(scale) or scale == 0:
                return []
            coefficients = coefficients / scale
            candidates = np.roots(coefficients)
            residual_poly = np.poly1d(coefficients)
            derivative_poly = np.polyder(residual_poly)
            roots = []
            for candidate in candidates:
                real = float(np.real(candidate))
                imag = abs(float(np.imag(candidate)))
                if imag > 2e-5 * max(1.0, abs(real)) or not (x_min - 1e-8 <= real <= x_max + 1e-8):
                    continue
                value = real
                for _ in range(10):
                    fval = float(residual_poly(value))
                    dval = float(derivative_poly(value))
                    if not np.isfinite(fval) or not np.isfinite(dval) or abs(dval) < 1e-14:
                        break
                    step = fval / dval
                    if abs(step) > 0.25 * max(1.0, abs(value)):
                        break
                    value -= step
                    if abs(step) < 1e-12:
                        break
                residual = abs(float(residual_poly(value)))
                magnitude = max(1.0, abs(value)) ** min(degree, 12)
                if residual <= 1e-8 * magnitude and x_min - 1e-8 <= value <= x_max + 1e-8:
                    roots.append(value)
            return _dedupe_sorted(roots, 1e-5)
        except Exception:
            return None
    # For degree >100 the square-free polynomial has only simple roots. A
    # sign-change scan is more stable than a huge companion matrix.
    return None


def _dedupe_sorted(values: list[float], tolerance: float = 1e-6) -> list[float]:
    result: list[float] = []
    for value in sorted(v for v in values if math.isfinite(v)):
        if not result or abs(value - result[-1]) > tolerance * max(1.0, abs(value)):
            result.append(value)
    return result


def _bisect_root(fn, left: float, right: float, level: float = 0.0) -> float | None:
    try:
        fl = fn(left) - level
        fr = fn(right) - level
        if not (math.isfinite(fl) and math.isfinite(fr)) or fl == 0:
            return left if fl == 0 else None
        if fr == 0:
            return right
        if fl * fr > 0:
            return None
        for _ in range(48):
            mid = (left + right) / 2
            fm = fn(mid) - level
            if not math.isfinite(fm):
                return None
            if abs(fm) < 1e-12 or abs(right - left) < 1e-10:
                return mid
            if fl * fm <= 0:
                right, fr = mid, fm
            else:
                left, fl = mid, fm
        return (left + right) / 2
    except Exception:
        return None


@lru_cache(maxsize=256)
def _numeric_roots(expr: sp.Expr, x_min: float, x_max: float, level: float = 0.0, samples: int = 1100) -> list[float]:
    fn = _numpy_function(expr)
    xs = np.linspace(x_min, x_max, samples)
    with np.errstate(all="ignore"):
        try:
            ys = np.asarray(fn(xs))
            if np.iscomplexobj(ys):
                ys = np.where(np.abs(np.imag(ys)) < 1e-10, np.real(ys), np.nan)
            ys = np.asarray(ys, dtype=float)
        except Exception:
            ys = np.array([evaluate(expr, x) if evaluate(expr, x) is not None else np.nan for x in xs], dtype=float)
    if ys.ndim == 0:
        ys = np.full_like(xs, float(ys))
    ys = np.where(np.isfinite(ys) & (np.abs(ys) < 1e12), ys, np.nan) - level
    roots: list[float] = []
    fn_scalar = lambda value: evaluate(expr, value)
    for i in range(len(xs) - 1):
        y0, y1 = ys[i], ys[i + 1]
        if not (np.isfinite(y0) and np.isfinite(y1)):
            continue
        # Only an actual sampled zero is accepted here. A global epsilon
        # wrongly classifies a whole flat neighborhood of x^250 as roots.
        if y0 == 0.0:
            roots.append(float(xs[i]))
        if y0 * y1 < 0:
            root = _bisect_root(fn_scalar, float(xs[i]), float(xs[i + 1]), level)
            if root is not None:
                roots.append(root)
    if np.isfinite(ys[-1]) and ys[-1] == 0.0:
        roots.append(float(xs[-1]))
    return _dedupe_sorted(roots, 2e-5)


@lru_cache(maxsize=256)
def find_real_roots(expr: sp.Expr, x_min: float, x_max: float, *, level: float = 0.0) -> list[float]:
    """Find real intersections with y=level in the requested x window.

    Polynomials use exact real-root isolation (including even-multiplicity
    roots); general functions use bounded numeric scanning and bisection.
    """
    shifted = sp.cancel(expr - sp.Float(level)) if level != 0 else expr
    roots = _real_poly_roots(shifted, x_min, x_max)
    if roots is None:
        roots = _numeric_roots(expr, x_min, x_max, level=level)
        # Tangencies of a non-polynomial function do not change sign. Test
        # stationary points too, using a bounded numerical search.
        try:
            derivative = sp.diff(expr, X)
            stationary = _real_poly_roots(derivative, x_min, x_max)
            if stationary is None:
                stationary = _numeric_roots(derivative, x_min, x_max, level=0.0, samples=900)
            for candidate in stationary:
                value = evaluate(expr, candidate)
                scale = max(abs(value) if value is not None else 0.0, abs(level), 1e-300)
                if value is not None and abs(value - level) <= 1e-8 * scale:
                    roots.append(float(candidate))
        except Exception:
            pass
    # Respect holes and real-domain restrictions of the original expression.
    domain_expr = expr
    try:
        domain = real_domain(domain_expr)[1]
        if domain is not None:
            roots = [r for r in roots if domain.contains(sp.Float(r)) is not sp.false]
    except Exception:
        pass
    return _dedupe_sorted(roots)


@lru_cache(maxsize=256)
def find_critical_points(expr: sp.Expr, x_min: float, x_max: float) -> list[float]:
    try:
        derivative = sp.diff(expr, X)
        roots = _real_poly_roots(derivative, x_min, x_max)
        if roots is None:
            roots = _numeric_roots(derivative, x_min, x_max, level=0.0, samples=900)
        return roots[:100]
    except Exception:
        return []


def build_graph_spec(expression: str, x_min: float = -8.0, x_max: float = 8.0, x_point: float = 2.0) -> dict:
    """Validate a function and prepare the lightweight browser-canvas payload."""
    try:
        x_min, x_max, x_point = float(x_min), float(x_max), float(x_point)
    except (TypeError, ValueError) as exc:
        raise ExpressionError("Os limites do intervalo precisam ser números reais.") from exc
    if not all(math.isfinite(v) for v in (x_min, x_max, x_point)):
        raise ExpressionError("Use apenas valores reais finitos para os limites e o ponto.")
    if x_min >= x_max:
        raise ExpressionError("O limite máximo de x precisa ser maior que o mínimo.")
    if x_max - x_min > 1e6:
        raise ExpressionError("O intervalo é amplo demais. Use uma largura máxima de 1.000.000.")
    if not x_min <= x_point <= x_max:
        x_point = min(x_max, max(x_min, x_point))

    expr = parse_math(expression)
    if X not in expr.free_symbols and expr.free_symbols:
        variables = ", ".join(sorted(str(s) for s in expr.free_symbols))
        raise ExpressionError(f"O gráfico usa x como variável independente. Variáveis encontradas: {variables}.")
    if len(expr.free_symbols) > 1:
        raise ExpressionError("O gráfico aceita uma variável independente: x.")

    # Preserve the source tree for domain restrictions such as removable holes.
    domain_expr = parse_math(expression, preserve_division=True, preserve_structure=True)
    function_js = to_javascript(expr)
    function_tex = format_math_latex(expression)
    try:
        domain_tex, domain_message = real_domain_latex(domain_expr)
    except Exception:
        domain_tex, domain_message = r"D_x=\text{não determinado automaticamente}", "O domínio não pôde ser determinado simbolicamente."
    try:
        root_expr = expr
        roots = find_real_roots(root_expr, x_min, x_max)
    except Exception:
        roots = []
    try:
        critical_points = find_critical_points(expr, x_min, x_max)
    except Exception:
        critical_points = []
    try:
        excluded = list(_excluded_real_points(domain_expr, X))
    except Exception:
        excluded = []
    y_point = evaluate(expr, x_point)
    constant_value = None
    constant_function = not bool(expr.free_symbols)
    if constant_function and expr.is_real is True and expr.is_number:
        try:
            candidate = float(sp.N(expr))
            if math.isfinite(candidate) and abs(candidate) < 1e12:
                constant_value = candidate
        except (TypeError, ValueError, OverflowError):
            pass
    try:
        domain = real_domain(domain_expr)[1]
        if domain is not None and domain.contains(sp.Float(x_point)) is sp.false:
            y_point = None
    except Exception:
        pass

    return {
        "expression": expression,
        "expression_tex": function_tex,
        # Plain symbolic form is used for the live point substitution readout.
        # It is text-only and never executed as JavaScript or HTML.
        "expression_plain": expression,
        "function_js": function_js,
        "constant_function": constant_function and constant_value is not None,
        "constant_value": constant_value,
        "x_min": x_min,
        "x_max": x_max,
        "x_point": x_point,
        "y_point": y_point,
        "roots": roots,
        "roots_all": bool(sp.simplify(expr) == 0),
        "critical_points": critical_points,
        "excluded_points": excluded,
        "domain_tex": domain_tex,
        "domain_message": domain_message,
        "line_y": 0.0,
    }


def _shifted_exponential(expr: sp.Expr):
    """Return (amplitude, base, shift) for c*b**x + k when recognizable."""
    try:
        shift, dependent = sp.expand(expr).as_independent(X, as_Add=True)
        if dependent == 0:
            return sp.S.Zero, sp.S.One, shift
        if dependent.func == sp.exp and dependent.args == (X,):
            return sp.S.One, sp.E, shift
        power_terms = [term for term in sp.Mul.make_args(dependent) if isinstance(term, sp.Pow) and term.exp == X]
        if len(power_terms) != 1:
            return None
        power = power_terms[0]
        base = sp.simplify(power.base)
        amplitude = sp.simplify(dependent / power)
        if base.is_positive is True and base != 1 and amplitude.is_real is True and amplitude.is_number:
            return amplitude, base, shift
    except Exception:
        pass
    return None


def _exponential_image_and_trend(expr: sp.Expr):
    parts = _shifted_exponential(expr)
    if parts is None:
        return None, None, None
    amplitude, base, shift = parts
    if amplitude == 0:
        return sp.FiniteSet(shift), "constante", None
    try:
        amplitude_sign = sp.sign(amplitude)
        base_grows = bool(sp.N(base) > 1)
        increasing = base_grows == (amplitude_sign > 0)
        image = sp.Interval.Lopen(shift, sp.oo) if amplitude_sign > 0 else sp.Interval.Ropen(-sp.oo, shift)
        return image, "crescente" if increasing else "decrescente", shift
    except Exception:
        return None, None, None


@lru_cache(maxsize=256)
def analyze_function(expression: str, x_min: float = -8.0, x_max: float = 8.0):
    """Conservative bounded analysis; avoids expensive global solvers."""
    expr = parse_math(expression)
    domain_expr = parse_math(expression, preserve_division=True, preserve_structure=True)
    if len(expr.free_symbols - {X}) > 0:
        raise ExpressionError("A análise de gráficos aceita apenas a variável x.")
    rows = [("Expressão", r"g(x) = " + sp.latex(expr))]
    try:
        _, domain, _ = real_domain(domain_expr)
        domain_formula, _ = real_domain_latex(domain_expr)
        rows.append(("Domínio", domain_formula.split("=", 1)[1] if "=" in domain_formula else domain_formula))
    except Exception:
        domain = None
        rows.append(("Domínio", r"\text{não determinado automaticamente}"))

    image, exponential_trend, exponential_shift = _exponential_image_and_trend(expr)
    if image is None and (expr == X**2 or expr == sp.sqrt(X)):
        image = sp.Interval(0, sp.oo)
    elif image is None and (expr == X**3 or expr == sp.log(X)):
        image = sp.S.Reals
    elif image is None and expr.is_polynomial(X):
        try:
            poly = sp.Poly(expr, X)
            if poly.degree() == 0:
                image = sp.FiniteSet(poly.as_expr())
            elif poly.degree() == 1:
                image = sp.S.Reals
            elif poly.degree() == 2:
                a, b, c = poly.all_coeffs()
                vertex_y = sp.cancel(expr.subs(X, -b / (2 * a)))
                image = sp.Interval(vertex_y, sp.oo) if a > 0 else sp.Interval(-sp.oo, vertex_y)
        except Exception:
            pass
    if image is None:
        rows.append(("Imagem", r"\text{não determinada automaticamente}"))
    else:
        rows.append(("Imagem", sp.latex(image)))

    try:
        roots = find_real_roots(expr, x_min, x_max)
        roots_text = sp.latex(sp.FiniteSet(*[sp.Float(root, 6) for root in roots])) if roots else r"\text{nenhuma raiz no intervalo}"
    except Exception:
        roots_text = r"\text{não determinada automaticamente}"
    rows.append(("Raízes no intervalo", roots_text))

    try:
        zero_valid = domain is None or domain.contains(0) is not sp.false
        intercept = sp.simplify(expr.subs(X, 0)) if zero_valid else None
        intercept_text = sp.latex(intercept) if intercept is not None and intercept not in (sp.zoo, sp.nan, sp.oo, -sp.oo) else r"\text{não definida}"
    except Exception:
        intercept_text = r"\text{não determinada automaticamente}"
    rows.append(("Interseção com o eixo y", intercept_text))

    polynomial_degree = None
    try:
        polynomial_degree = sp.Poly(expr, X).degree()
    except (sp.PolynomialError, TypeError, ValueError):
        pass

    derivative = None
    if polynomial_degree is not None and polynomial_degree > 24:
        rows.append(("Derivada", r"\text{não expandida automaticamente para polinômios de grau acima de 24, para preservar a responsividade}"))
    else:
        try:
            derivative = sp.diff(expr, X)
            rows.append(("Derivada", sp.latex(derivative)))
        except Exception:
            rows.append(("Derivada", r"\text{não determinada automaticamente}"))

    if exponential_trend:
        growth = exponential_trend + " em todo o domínio real."
    elif expr == X**2:
        growth = "decrescente em (−∞, 0] e crescente em [0, +∞)."
    elif expr == X**3:
        growth = "crescente em todo o domínio real."
    elif expr == 1 / X:
        growth = "decrescente em (−∞, 0) e em (0, +∞)."
    elif polynomial_degree is not None and polynomial_degree > 24:
        growth = "A monotonicidade não é calculada automaticamente para polinômios de grau acima de 24. Consulte o gráfico e a derivada em um intervalo menor."
    else:
        if derivative is None:
            try:
                derivative = sp.diff(expr, X)
            except Exception:
                derivative = None
        if derivative is not None and derivative.is_positive is True:
            growth = "crescente em todo o domínio real."
        elif derivative is not None and derivative.is_negative is True:
            growth = "decrescente em todo o domínio real."
        else:
            growth = "A monotonicidade não foi determinada automaticamente para todo o domínio. Consulte a derivada e seu sinal."
    rows.append(("Crescimento / decrescimento", growth))

    if exponential_shift is not None and _exponential_image_and_trend(expr)[0] is not None:
        asymptotes = sp.latex(sp.Eq(sp.Symbol("y"), exponential_shift)) + r"\;\text{(horizontal)}"
    elif expr == 1 / X:
        asymptotes = r"x=0\;\text{(vertical)},\quad y=0\;\text{(horizontal)}"
    else:
        asymptotes = r"\text{não determinadas automaticamente}"
    rows.append(("Assíntotas", asymptotes))
    rows.append(("Continuidade", "Contínua em todo ponto do domínio real."))
    return rows
