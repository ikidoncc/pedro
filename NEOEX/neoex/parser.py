"""Safe mathematical-expression parser for NEOEX.

A small recursive-descent parser builds a private syntax tree and then converts
it to SymPy. It deliberately avoids eval/exec and sympy.parse_expr.

Notation policy for implicit products:
    2^2x       -> (2^2)·x
    3x^x       -> 3·(x^x)
    a/4x^2     -> a/(4·x^2)

Thus implicit multiplication binds more tightly than explicit division. When a
learner wants a different grouping, parentheses make it explicit.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

import sympy as sp

_ALLOWED_FUNCTIONS = {"sqrt", "abs", "exp", "log", "ln", "sin", "cos", "tan"}
_MAX_LENGTH = 320
_MAX_TOKENS = 180
_MAX_NODES = 180
_MAX_POWER = 1000


class ExpressionError(ValueError):
    """Raised when an expression is outside the supported safe grammar."""


@dataclass(frozen=True)
class _Node:
    kind: str
    value: Any = None
    children: tuple["_Node", ...] = ()


_TOKEN_RE = re.compile(
    r"\s*(?:(?P<number>(?:\d+(?:\.\d*)?|\.\d+))|"
    r"(?P<name>[A-Za-z][A-Za-z0-9]*)|"
    r"(?P<op>\*\*|[+\-*/^·×(),\[\]{}]))"
)


def _normalize_delimiters(text: str) -> str:
    pairs = {")": "(", "]": "[", "}": "{"}
    openers = set(pairs.values())
    stack: list[str] = []
    for char in text:
        if char in openers:
            stack.append(char)
        elif char in pairs:
            if not stack or stack[-1] != pairs[char]:
                raise ExpressionError("Confira os parênteses, colchetes e chaves: há delimitadores fora de ordem.")
            stack.pop()
    if stack:
        raise ExpressionError("Falta fechar um parêntese, colchete ou chave.")
    return text.translate(str.maketrans({"[": "(", "]": ")", "{": "(", "}": ")", "·": "*", "×": "*"}))


def _tokenize(text: str) -> list[tuple[str, str]]:
    source = _normalize_delimiters(text.strip())
    if not source:
        raise ExpressionError("Digite uma expressão matemática.")
    if len(source) > _MAX_LENGTH:
        raise ExpressionError("A expressão ultrapassou o limite de 320 caracteres.")
    # A comma between digits is accepted as a decimal separator.
    source = re.sub(r"(?<=\d),(?=\d)", ".", source)
    tokens: list[tuple[str, str]] = []
    pos = 0
    while pos < len(source):
        match = _TOKEN_RE.match(source, pos)
        if not match:
            if source[pos:].strip() == "":
                break
            raise ExpressionError(f"Caractere não permitido próximo de: {source[pos:pos+12]!r}.")
        if match.group("number") is not None:
            tokens.append(("number", match.group("number")))
        elif match.group("name") is not None:
            tokens.append(("name", match.group("name")))
        else:
            tokens.append(("op", match.group("op")))
        pos = match.end()
        if len(tokens) > _MAX_TOKENS:
            raise ExpressionError("A expressão contém elementos demais para ser processada com segurança.")
    tokens.append(("eof", ""))
    return tokens


class _Parser:
    def __init__(self, text: str):
        self.tokens = _tokenize(text)
        self.i = 0
        self.node_count = 0

    @property
    def token(self) -> tuple[str, str]:
        return self.tokens[self.i]

    def take(self, value: str | None = None) -> tuple[str, str]:
        tok = self.token
        if value is not None and tok[1] != value:
            raise ExpressionError(f"Esperava-se '{value}' na expressão.")
        self.i += 1
        return tok

    def node(self, kind: str, value=None, *children: _Node) -> _Node:
        self.node_count += 1
        if self.node_count > _MAX_NODES:
            raise ExpressionError("A expressão possui complexidade excessiva.")
        return _Node(kind, value, tuple(children))

    def parse(self) -> _Node:
        result = self.parse_sum()
        if self.token[0] != "eof":
            raise ExpressionError(f"Trecho inesperado na expressão: {self.token[1]!r}.")
        return result

    def parse_sum(self) -> _Node:
        node = self.parse_product()
        while self.token[1] in ("+", "-"):
            op = self.take()[1]
            right = self.parse_product()
            node = self.node("add" if op == "+" else "sub", None, node, right)
        return node

    def _starts_atom(self) -> bool:
        kind, value = self.token
        if kind == "number":
            return True
        if kind == "name":
            return True
        return kind == "op" and value == "("

    def parse_product(self) -> _Node:
        # Implicit products are parsed as a tighter unit than explicit * and /.
        # This makes a/4x^2 mean a/(4*x^2), which is the common classroom
        # convention for a monomial written without an explicit multiplication dot.
        node = self.parse_implicit_product()
        while self.token[1] in ("*", "/"):
            op = self.take()[1]
            right = self.parse_implicit_product()
            node = self.node("mul" if op == "*" else "div", None, node, right)
        return node

    def parse_implicit_product(self) -> _Node:
        node = self.parse_unary()
        while self._starts_atom():
            # A function name must be parsed together with its following '(';
            # ordinary symbols followed by '(' remain implicit multiplication.
            right = self.parse_unary()
            node = self.node("imul", None, node, right)
        return node

    def parse_unary(self) -> _Node:
        if self.token[1] in ("+", "-"):
            op = self.take()[1]
            child = self.parse_unary()
            return self.node("pos" if op == "+" else "neg", None, child)
        return self.parse_power()

    def parse_power(self) -> _Node:
        base = self.parse_primary()
        if self.token[1] in ("^", "**"):
            self.take()
            exponent = self.parse_unary()  # right associative: 2^3^2 = 2^(3^2)
            return self.node("pow", None, base, exponent)
        return base

    def parse_primary(self) -> _Node:
        kind, value = self.token
        if kind == "number":
            self.take()
            return self.node("number", value)
        if kind == "name":
            self.take()
            low = value.lower()
            if low in ("pi",):
                return self.node("constant", "pi")
            if low in ("e",):
                return self.node("constant", "e")
            if value in _ALLOWED_FUNCTIONS and self.token[1] == "(":
                self.take("(")
                argument = self.parse_sum()
                self.take(")")
                function_name = "log" if value == "ln" else value
                return self.node("call", function_name, argument)
            if value in _ALLOWED_FUNCTIONS:
                raise ExpressionError(f"A função {value} precisa ser chamada com parênteses, por exemplo {value}(x).")
            return self.node("symbol", value)
        if kind == "op" and value == "(":
            self.take("(")
            inside = self.parse_sum()
            self.take(")")
            return self.node("group", None, inside)
        if value == "":
            raise ExpressionError("A expressão terminou antes de ser concluída.")
        raise ExpressionError(f"Não esperava o símbolo {value!r} nessa posição.")


def _to_sympy(node: _Node, *, preserve_division=False, preserve_structure=False) -> sp.Expr:
    kind = node.kind
    if kind == "number":
        return sp.Rational(node.value)
    if kind == "symbol":
        return sp.Symbol(node.value, real=True)
    if kind == "constant":
        return sp.pi if node.value == "pi" else sp.E
    if kind == "group":
        return _to_sympy(node.children[0], preserve_division=preserve_division, preserve_structure=preserve_structure)
    if kind in ("pos", "neg"):
        child = _to_sympy(node.children[0], preserve_division=preserve_division, preserve_structure=preserve_structure)
        if kind == "pos":
            return child
        return sp.Mul(-1, child, evaluate=False) if preserve_structure else -child
    if kind == "call":
        arg = _to_sympy(node.children[0], preserve_division=preserve_division, preserve_structure=preserve_structure)
        fn = {"sqrt": sp.sqrt, "abs": sp.Abs, "exp": sp.exp, "log": sp.log,
              "sin": sp.sin, "cos": sp.cos, "tan": sp.tan}[node.value]
        if preserve_structure:
            if node.value == "sqrt":
                return sp.Pow(arg, sp.Rational(1, 2), evaluate=False)
            try:
                return fn(arg, evaluate=False)
            except TypeError:
                return fn(arg)
        return fn(arg)

    args = [_to_sympy(child, preserve_division=preserve_division, preserve_structure=preserve_structure) for child in node.children]
    if kind == "add":
        return sp.Add(*args, evaluate=False) if preserve_structure else args[0] + args[1]
    if kind == "sub":
        return sp.Add(args[0], sp.Mul(-1, args[1], evaluate=False), evaluate=False) if preserve_structure else args[0] - args[1]
    if kind in ("mul", "imul"):
        return sp.Mul(*args, evaluate=False) if preserve_structure else args[0] * args[1]
    if kind == "div":
        if args[1] == 0 or sp.simplify(args[1]) == 0:
            raise ExpressionError("Divisão por zero: o denominador precisa ser diferente de zero.")
        if preserve_division or preserve_structure:
            return sp.Mul(args[0], sp.Pow(args[1], -1, evaluate=False), evaluate=False)
        return args[0] / args[1]
    if kind == "pow":
        if sp.simplify(args[0]) == 0 and sp.simplify(args[1]) == 0:
            raise ExpressionError("0^0 não está definido nos números reais.")
        if args[1].is_number and args[1].is_real:
            try:
                if abs(float(args[1])) > _MAX_POWER:
                    raise ExpressionError("Expoente muito grande para esta demonstração.")
            except (TypeError, ValueError):
                pass
        return sp.Pow(args[0], args[1], evaluate=not preserve_structure)
    raise ExpressionError("Operação matemática não permitida.")


def parse_math(text: str, *, default_variable: str = "x", preserve_division: bool = False, preserve_structure: bool = False) -> sp.Expr:
    """Parse a safe real expression; implicit products bind tighter than /.

    Accepted operations: +, -, *, /, ^, **, implicit multiplication, grouping
    delimiters (), [] and {}, constants pi/e and one-argument elementary
    functions sqrt, abs, exp, log/ln, sin, cos, tan.
    """
    if not isinstance(text, str):
        raise ExpressionError("A expressão precisa ser texto.")
    node = _Parser(text).parse()
    result = _to_sympy(node, preserve_division=preserve_division, preserve_structure=preserve_structure)
    if result.has(sp.zoo, sp.nan, sp.oo, -sp.oo):
        raise ExpressionError("A expressão produz uma forma indefinida ou infinita.")
    return result


def _node_latex(node: _Node, parent: str = "") -> str:
    kind = node.kind
    if kind == "number":
        return sp.latex(sp.Rational(node.value))
    if kind == "symbol":
        return node.value
    if kind == "constant":
        return r"\pi" if node.value == "pi" else "e"
    if kind == "group":
        return r"\left(" + _node_latex(node.children[0]) + r"\right)"
    if kind == "pos":
        return "+" + _node_latex(node.children[0], "unary")
    if kind == "neg":
        child = node.children[0]
        rendered = _node_latex(child, "unary")
        if child.kind in ("add", "sub"):
            rendered = r"\left(" + _node_latex(child) + r"\right)"
        return "-" + rendered
    if kind == "call":
        arg = _node_latex(node.children[0])
        if node.value == "sqrt":
            return r"\sqrt{" + arg + "}"
        if node.value == "abs":
            return r"\left|" + arg + r"\right|"
        names = {"exp": r"\exp", "log": r"\log", "sin": r"\sin", "cos": r"\cos", "tan": r"\tan"}
        return names[node.value] + r"\left(" + arg + r"\right)"
    left_node = node.children[0]
    right_node = node.children[1]
    left = _node_latex(left_node)
    right = _node_latex(right_node)
    if kind == "add":
        rendered = left + " + " + right
    elif kind == "sub":
        rendered = left + " - " + right
    elif kind == "div":
        # The fraction bar already groups numerator and denominator. Strip
        # only the redundant outer grouping entered by the user.
        if left_node.kind == "group":
            left = _node_latex(left_node.children[0])
        if right_node.kind == "group":
            right = _node_latex(right_node.children[0])
        return r"\frac{" + left + "}{" + right + "}"
    elif kind in ("mul", "imul"):
        if left_node.kind in ("add", "sub", "div"):
            left = r"\left(" + _node_latex(left_node) + r"\right)"
        if right_node.kind in ("add", "sub", "div"):
            right = r"\left(" + _node_latex(right_node) + r"\right)"
        if kind == "mul":
            rendered = left + r" \cdot " + right
        else:
            # Numeric juxtaposition such as 2 3 is clearer with a dot;
            # variable/parenthesis juxtaposition follows algebraic convention.
            if left_node.kind == "number" and right_node.kind == "number":
                rendered = left + r" \cdot " + right
            else:
                rendered = left + right
    elif kind == "pow":
        base = left
        if left_node.kind in ("add", "sub", "mul", "imul", "div", "neg"):
            base = r"\left(" + _node_latex(left_node) + r"\right)"
        exponent_node = right_node.children[0] if right_node.kind == "group" else right_node
        exponent = _node_latex(exponent_node)
        return base + "^{" + exponent + "}"
    else:
        raise ExpressionError("Operação não permitida na pré-visualização.")
    if parent == "mul" and kind in ("add", "sub"):
        return r"\left(" + rendered + r"\right)"
    return rendered


def format_math_latex(text: str) -> str:
    """Format a safe expression as LaTeX, preserving its written grouping."""
    return _node_latex(_Parser(text).parse())


def parse_equation(text: str) -> sp.Equality:
    if text.count("=") != 1:
        raise ExpressionError("Para resolver uma equação, use exatamente um sinal =.")
    left, right = text.split("=", 1)
    return sp.Eq(parse_math(left), parse_math(right))


def parse_inequality(text: str):
    pattern = re.search(r"(<=|>=|<|>)", text)
    if not pattern:
        raise ExpressionError("Use <, >, <= ou >= para escrever a inequação.")
    op = pattern.group(1)
    left, right = text[:pattern.start()], text[pattern.end():]
    lhs, rhs = parse_math(left), parse_math(right)
    return {"<": sp.Lt, "<=": sp.Le, ">": sp.Gt, ">=": sp.Ge}[op](lhs, rhs)
