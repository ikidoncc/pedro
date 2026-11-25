"""Algebra operations and pedagogical, traceable transformation steps."""
from __future__ import annotations
import sympy as sp
import re
from .parser import parse_math, parse_equation, parse_inequality, format_math_latex, ExpressionError
from .domain import real_domain_latex


def latex(expr) -> str:
    return sp.latex(expr)


def inline_latex(expr) -> str:
    """Render an algebraic fragment as inline TeX inside explanatory prose."""
    return rf"\({latex(expr)}\)"


def original_restrictions(expr) -> list[str]:
    """Extract real exclusions from every denominator preserved in the input AST."""
    denominators = []
    for node in sp.preorder_traversal(expr):
        if isinstance(node, sp.Pow) and (node.exp.is_negative or node.exp == 0):
            denominators.append(node.base)
    restrictions = []
    symbols = sorted(expr.free_symbols, key=lambda s: s.name)
    for denominator in denominators:
        if not denominator.free_symbols:
            if denominator == 0:
                restrictions.append("expressão indefinida")
            continue
        if len(symbols) == 1:
            var = symbols[0]
            try:
                excluded = sp.solveset(sp.Eq(denominator, 0), var, domain=sp.S.Reals)
                if excluded == sp.EmptySet:
                    continue
                if excluded.is_FiniteSet:
                    for value in sorted(excluded, key=sp.default_sort_key):
                        item = f"{var} ≠ {sp.sstr(value)}"
                        if item not in restrictions:
                            restrictions.append(item)
                    continue
            except Exception:
                pass
        item = f"{sp.sstr(denominator)} ≠ 0"
        if item not in restrictions:
            restrictions.append(item)
    return restrictions


def _restriction_latex(restrictions: list[str]) -> str:
    pieces = []
    for item in restrictions:
        left, right = item.split(" ≠ ", 1)
        pieces.append(rf"{left} \ne {right}")
    return r",\quad ".join(pieces)


def _domain_step(expr):
    formula, explanation = real_domain_latex(expr)
    return ("Domínio real da expressão", formula, explanation)


def _source_formula(source: str, fallback_expr) -> str:
    """Format the user's original order; fall back to a safe SymPy rendering."""
    try:
        return format_math_latex(source)
    except Exception:
        return latex(fallback_expr)


def _numeric_power_steps(source: str, expr):
    """Detailed exact calculation for the numeric fractional-power example."""
    compact = re.sub(r"\s+", "", source).replace("**", "^")
    variants = {
        "(1/4)^(-1/2)+81^(3/4)-2^(-1)+5^0",
        "(1/4)^(-1/2)+81^(3/4)-2^-1+5^0",
        "(¼)^(-½)+81^(¾)-2^(-1)+5^0",
    }
    if compact not in variants or expr.free_symbols:
        return None
    steps = [
        ("Expressão original", r"\left(\frac14\right)^{-\frac12}+81^{\frac34}-2^{-1}+5^0", "Vamos calcular cada potência separadamente. As potências com expoentes fracionários serão interpretadas por meio de raízes; expoente negativo indica inverso e expoente zero produz 1."),
        ("Calcule a potência com expoente negativo", r"\left(\frac14\right)^{-\frac12}=\frac{1}{\sqrt{\frac14}}=\frac{1}{\frac12}=2", "O expoente −1/2 pede a raiz quadrada e, em seguida, o inverso. A raiz quadrada de 1/4 é 1/2; o inverso de 1/2 é 2."),
        ("Calcule a potência com expoente fracionário", r"81^{\frac34}=\left(\sqrt[4]{81}\right)^3=3^3=27", "O denominador 4 indica a raiz quarta. Como a raiz quarta de 81 é 3, elevamos esse resultado ao cubo: 27."),
        ("Interprete o expoente negativo", r"2^{-1}=\frac{1}{2}", "Um expoente −1 representa o inverso multiplicativo da base. Por isso, 2⁻¹ é 1/2."),
        ("Interprete o expoente zero", r"5^0=1", "Toda base real diferente de zero elevada a zero vale 1. Como a base é 5, o resultado é 1."),
        ("Substitua os valores encontrados", r"2+27-\frac12+1", "Agora substituímos cada potência pelo valor calculado, preservando os sinais da expressão original."),
        ("Some os termos inteiros", r"2+27+1-\frac12=30-\frac12", "Somamos 2, 27 e 1, obtendo 30. A parcela −1/2 permanece subtraída."),
        ("Escreva o resultado como uma única fração", r"30-\frac12=\frac{60}{2}-\frac12=\boxed{\frac{59}{2}}", "Escrevemos 30 com denominador 2: 30=60/2. Então (60−1)/2=59/2, ou 29,5."),
    ]
    return steps

def _fraction_steps(expr, restrictions):
    """Show numerator/denominator factoring and cancellation before the result."""
    numerator, denominator = sp.fraction(expr, exact=True)
    if denominator == 1:
        together = sp.together(expr)
        numerator, denominator = sp.fraction(together)
    fact_num, fact_den = sp.factor(numerator), sp.factor(denominator)
    steps = [
        ("Expressão original", latex(expr), "Identificamos o numerador e o denominador. Vamos fatorar cada um antes de cancelar qualquer coisa."),
        ("Fatore o numerador", latex(fact_num), rf"Reescrevemos o numerador como produto de fatores: \({latex(numerator)} = {latex(fact_num)}\)."),
        ("Fatore o denominador", latex(fact_den), rf"Reescrevemos o denominador como produto de fatores: \({latex(denominator)} = {latex(fact_den)}\)."),
        ("Reescreva a fração", rf"\frac{{{latex(fact_num)}}}{{{latex(fact_den)}}}", "Agora numerador e denominador estão escritos como produtos. Só podemos cancelar fatores multiplicativos comuns."),
    ]
    common = sp.gcd(fact_num, fact_den)
    if common not in (1, -1):
        rem_num = sp.cancel(fact_num / common)
        rem_den = sp.cancel(fact_den / common)
        cancel_formula = (
            rf"\frac{{{latex(common)}\left({latex(rem_num)}\right)}}{{{latex(common)}\left({latex(rem_den)}\right)}}"
            rf"\;\Longrightarrow\;\frac{{{latex(rem_num)}}}{{{latex(rem_den)}}}"
        )
        steps.append(("Cancele o fator comum", cancel_formula, rf"O fator \({latex(common)}\) aparece multiplicando o numerador e o denominador. Podemos cancelá-lo, mantendo as restrições da expressão original."))
    else:
        steps.append(("Verifique os fatores", rf"\frac{{{latex(fact_num)}}}{{{latex(fact_den)}}}", "Não há um fator polinomial comum para cancelar. Não se cancelam parcelas separadas por + ou −."))
    result = sp.cancel(expr)
    steps.append(("Forma simplificada", latex(result), "Esta é a expressão após a simplificação. As condições de validade da expressão original continuam obrigatórias."))
    if restrictions:
        steps.append(("Restrições do domínio", _restriction_latex(restrictions), "Esses valores anulavam o denominador original. A simplificação não os recoloca no domínio."))
    return steps


def _factor_steps(expr, result):
    steps = [(
        "Expressão original", latex(expr),
        "Observe os termos. Vamos procurar um fator comum e, depois, verificar se a expressão restante admite uma fatoração conhecida."
    )]
    terms = sp.Add.make_args(expr)
    common = sp.gcd_list(list(terms)) if len(terms) >= 2 else sp.Integer(1)
    working = expr
    if common not in (1, -1):
        quotients = [sp.cancel(term / common) for term in terms]
        remainder = sp.Add(*quotients, evaluate=False)
        steps.append((
            "Identifique o fator comum", latex(common),
            rf"O fator \({latex(common)}\) aparece em todos os termos. Podemos colocá-lo fora dos parênteses."
        ))
        steps.append((
            "Divida cada termo pelo fator comum", latex(remainder),
            "Dividimos cada parcela pelo fator colocado em evidência. Os quocientes formam o conteúdo dos parênteses."
        ))
        working = common * remainder
        steps.append((
            "Coloque o fator em evidência", latex(sp.factor_terms(working)),
            "Escrevemos o fator comum uma única vez, multiplicando a soma ou diferença que restou."
        ))
    complete = sp.factor(expr)
    if common in (1, -1) and complete != expr:
        symbols = sorted(expr.free_symbols, key=lambda symbol: symbol.name)
        roots = []
        if len(symbols) == 1:
            try:
                polynomial = sp.Poly(expr, symbols[0])
                if 1 <= polynomial.degree() <= 4:
                    roots = sp.solve(polynomial.as_expr(), symbols[0])
            except Exception:
                roots = []
        if roots:
            root_formula = r"\quad\text{ou}\quad ".join(rf"{latex(symbols[0])}={latex(root)}" for root in roots)
            steps.append((
                "Encontre as raízes", root_formula,
                "As raízes são os valores que anulam a expressão. Pelo teorema do fator, cada raiz r corresponde a um fator (x−r)."
            ))
            steps.append((
                "Construa os fatores", latex(complete),
                "Formamos um fator para cada raiz encontrada, respeitando suas multiplicidades. O produto desses fatores reproduz o polinômio."
            ))
        else:
            steps.append((
                "Fatore a expressão", latex(complete),
                "O motor algébrico reconheceu uma identidade ou uma decomposição em fatores equivalentes."
            ))
    elif complete != result and complete != sp.factor_terms(expr):
        steps.append((
            "Procure uma fatoração adicional", latex(complete),
            "Depois de colocar fatores comuns em evidência, verificamos se a expressão restante admite outra fatoração."
        ))
    if result == expr:
        steps.append(("Forma fatorada", latex(result), "A expressão já está na forma fatorada ou não admite uma fatoração adicional nas regras simbólicas disponíveis."))
    else:
        steps.append(("Forma fatorada", latex(result), "Esta é a forma fatorada correspondente à operação escolhida."))
    if sp.simplify(sp.expand(result) - expr) == 0:
        steps.append((
            "Confira pela distributividade", latex(sp.expand(result)),
            "Ao desenvolver os fatores, recuperamos exatamente a expressão original. Isso confirma a equivalência."
        ))
    return steps


def _expand_steps(expr, result):
    steps = [("Expressão original", latex(expr), "Vamos substituir produtos e potências por uma sequência de multiplicações e aplicar a propriedade distributiva." )]
    if isinstance(expr, sp.Pow) and expr.exp.is_Integer and 2 <= int(expr.exp) <= 6 and isinstance(expr.base, sp.Add):
        n = int(expr.exp)
        base = expr.base
        repeated = r"\cdot".join([rf"\left({latex(base)}\right)"] * n)
        steps.append(("Repita a base", repeated, f"O expoente {n} indica {n} fatores iguais. Por enquanto, apenas reescrevemos a potência como multiplicação repetida."))
        accumulator = base
        for index in range(2, n + 1):
            product = sp.expand(accumulator * base)
            steps.append((
                f"Desenvolva o bloco {index}",
                rf"\left({latex(accumulator)}\right)\left({latex(base)}\right)={latex(product)}",
                rf"Distribuímos cada termo do produto já obtido pelo próximo fator \({latex(base)}\). Depois agrupamos os termos que ficaram semelhantes."
            ))
            accumulator = product
    else:
        factors = sp.Mul.make_args(expr)
        sums = [factor for factor in factors if isinstance(factor, sp.Add)]
        if len(sums) >= 2:
            partial = sp.expand(sums[0] * sums[1])
            steps.append((
                "Distribua o primeiro par de fatores", latex(partial),
                "Multiplicamos cada termo do primeiro parêntese por cada termo do segundo. Cada combinação gera uma parcela."
            ))
            if len(sums) > 2:
                for factor in sums[2:]:
                    next_partial = sp.expand(partial * factor)
                    steps.append((
                        "Distribua o próximo fator", latex(next_partial),
                        "Multiplicamos cada parcela obtida pelo próximo fator entre parênteses e voltamos a reunir termos semelhantes."
                    ))
                    partial = next_partial
        elif isinstance(expr, sp.Mul) and any(isinstance(factor, sp.Add) for factor in factors):
            steps.append((
                "Aplique a distributividade", latex(sp.expand(expr)),
                "Multiplicamos o fator externo por cada parcela do parêntese. Assim, nenhum termo é ignorado."
            ))
        else:
            expanded_once = sp.expand(expr)
            if expanded_once != expr:
                steps.append((
                    "Aplique as propriedades algébricas", latex(expanded_once),
                    "Desenvolvemos os produtos e potências reconhecidos pelo motor algébrico."
                ))
    expanded = sp.expand(expr)
    if not any(step[1] == latex(expanded) for step in steps):
        steps.append(("Reúna os termos desenvolvidos", latex(expanded), "Depois da distributividade, organizamos os termos semelhantes em uma expressão equivalente."))
    if expanded != result:
        steps.append(("Organize os termos semelhantes", latex(result), "Somamos as parcelas com a mesma parte literal e o mesmo expoente."))
    else:
        steps.append(("Resultado desenvolvido", latex(result), "A expressão está desenvolvida e os termos semelhantes foram reunidos."))
    return steps

def _special_polynomial_steps(expr, operation):
    """A trace for the most common examples explicitly shown in the app."""
    x = sp.Symbol("x", real=True)
    if expr == x**3 + x**2 and operation in {"Fatorar", "Colocar em evidência", "Simplificar"}:
        return [
            ("Expressão original", r"x^3+x^2", "Temos dois termos: x³ e x². Ambos contêm x² como fator."),
            ("Identifique o fator comum", r"x^2", "O menor expoente de x presente nos dois termos é 2. Portanto, o fator comum é x²."),
            ("Divida cada termo", r"\frac{x^3}{x^2}+\frac{x^2}{x^2}=x+1", "Ao dividir cada termo por x², restam x no primeiro e 1 no segundo."),
            ("Coloque em evidência", r"x^2(x+1)", "Colocamos x² em evidência e mantemos x+1 entre parênteses."),
            ("Confira", r"x^2\cdot x+x^2\cdot1=x^3+x^2", "A distributividade recupera exatamente a expressão original."),
        ]
    if expr == (x + 2)**3 and operation == "Desenvolver":
        return [
            ("Expressão original", r"(x+2)^3", "O expoente 3 indica três fatores iguais à base (x+2)."),
            ("Repita a base", r"(x+2)\cdot(x+2)\cdot(x+2)", "Escrevemos a potência como multiplicação de três cópias do mesmo binômio."),
            ("Desenvolva os dois primeiros fatores", r"(x^2+4x+4)(x+2)", "Aplicamos a distributividade: x·x, x·2, 2·x e 2·2. Somamos 2x+2x=4x."),
            ("Distribua o terceiro fator", r"x^3+2x^2+4x^2+8x+4x+8", "Multiplicamos cada parcela de x²+4x+4 por x e depois por 2."),
            ("Reúna termos semelhantes", r"x^3+6x^2+12x+8", "Somamos 2x²+4x²=6x² e 8x+4x=12x."),
        ]
    if expr == (x**3 + 2*x**2)/(x + 2) and operation in {"Simplificar", "Simplificar fração"}:
        return [
            ("Expressão original", r"\frac{x^3+2x^2}{x+2}", "A expressão é uma fração algébrica. O denominador original exige x+2 diferente de zero."),
            ("Fatore o numerador", r"\frac{x^2(x+2)}{x+2}", "No numerador, x² é fator comum: x³+2x²=x²(x+2)."),
            ("Identifique o fator comum", r"\frac{x^2(x+2)}{x+2}\;\Longrightarrow\;x^2", "O fator (x+2) aparece multiplicando no numerador e no denominador. Podemos cancelá-lo quando x≠−2."),
            ("Forma simplificada", r"x^2,\quad x\ne -2", "O quociente simplificado é x², mas x=−2 continua excluído por causa da expressão original."),
        ]
    return None


def _special_raw_steps(cleaned: str, operation: str):
    compact = re.sub(r"\s+", "", cleaned).replace("**", "^")
    if compact in {"2^(2x)-5*2^x+4", "2^(2*x)-5*2^x+4"} and operation in {"Simplificar", "Fatorar"}:
        return [
            ("Expressão original", r"2^{2x}-5\cdot2^x+4", "A variável aparece no expoente. Para fatorar com clareza, vamos reconhecer uma expressão quadrática em 2ˣ."),
            ("Faça uma substituição", r"t=2^x,\quad t>0", "A potência 2ˣ é positiva para todo x real. Por isso, podemos chamá-la de t e registrar a condição t>0."),
            ("Reescreva a potência de expoente duplo", r"2^{2x}=(2^x)^2=t^2", "Usamos a propriedade da potência de potência: dobrar o expoente x equivale a elevar (2ˣ) ao quadrado."),
            ("Substitua na expressão", r"t^2-5t+4", "Trocamos 2ˣ por t e 2²ˣ por t². Agora temos um trinômio quadrático usual."),
            ("Encontre dois números", r"1\cdot4=4,\qquad 1+4=5", "Precisamos de dois números cujo produto seja o termo independente 4 e cuja soma seja o coeficiente 5. Esses números são 1 e 4."),
            ("Fatore o trinômio", r"t^2-5t+4=(t-1)(t-4)", "Com os números encontrados, escrevemos o trinômio como produto de dois fatores."),
            ("Retorne à variável original", r"(2^x-1)(2^x-4)", "Substituímos t por 2ˣ novamente. A expressão agora está fatorada em função de x."),
            ("Confira a fatoração", r"(2^x-1)(2^x-4)=2^{2x}-5\cdot2^x+4", "Ao multiplicar os fatores, recuperamos a expressão original: 2²ˣ−4·2ˣ−1·2ˣ+4, e as parcelas centrais somam −5·2ˣ."),
        ], r"(2^x-1)(2^x-4)", []
    if compact in {"(x^2-x^3)/(x^3+x^5)", "(x²-x³)/(x³+x⁵)"} and operation in {"Simplificar", "Simplificar fração"}:
        return [
            ("Expressão original", r"\frac{x^2-x^3}{x^3+x^5}", "O numerador e o denominador possuem fatores comuns. Vamos fatorar cada parte antes de cancelar."),
            ("Fatore o numerador", r"x^2(1-x)", "No numerador, colocamos x² em evidência: x²−x³ = x²(1−x)."),
            ("Fatore o denominador", r"x^2(x+x^3)", "No denominador, colocamos x² em evidência: x³+x⁵ = x²(x+x³)."),
            ("Substitua na fração", r"\frac{x^2(1-x)}{x^2(x+x^3)}", "Agora vemos x² como fator multiplicativo tanto no numerador quanto no denominador."),
            ("Cancele o fator comum", r"\frac{x^2(1-x)}{x^2(x+x^3)}\;\Longrightarrow\;\frac{1-x}{x+x^3}", "Cancelamos x², que é um fator. Não cancelamos parcelas de uma soma."),
            ("Resultado e restrição", r"\frac{1-x}{x+x^3},\quad x\ne0", "A restrição x≠0 permanece porque o denominador da expressão original se anulava em x=0."),
        ], r"\frac{1-x}{x+x^3}", ["x ≠ 0"]
    if compact in {"(x^3+2x^2)/(x+2)", "(x³+2x²)/(x+2)"} and operation in {"Simplificar", "Simplificar fração"}:
        return [
            ("Expressão original", r"\frac{x^3+2x^2}{x+2}", "A expressão é uma fração algébrica. O denominador original exige x+2≠0."),
            ("Fatore o numerador", r"\frac{x^2(x+2)}{x+2}", "Colocamos x² em evidência no numerador: x³+2x²=x²(x+2)."),
            ("Identifique o fator comum", r"\frac{x^2(x+2)}{x+2}\;\Longrightarrow\;x^2", "O fator (x+2) aparece multiplicando no numerador e no denominador; seu cancelamento exige x≠−2."),
            ("Resultado e restrição", r"x^2,\quad x\ne-2", "A expressão simplificada é x², mas x=−2 continua fora do domínio da expressão original."),
        ], r"x^2", ["x ≠ -2"]
    if compact in {"x^3+x^2", "x²+x³", "x^2+x^3"} and operation in {"Fatorar", "Colocar em evidência", "Simplificar"}:
        return [
            ("Expressão original", r"x^3+x^2", "Os dois termos possuem uma potência de x em comum."),
            ("Identifique o fator comum", r"x^2", "O menor expoente de x entre os termos é 2. O fator comum é x²."),
            ("Divida cada termo", r"\frac{x^3}{x^2}+\frac{x^2}{x^2}=x+1", "Ao dividir cada termo por x², restam x e 1."),
            ("Coloque em evidência", r"x^2(x+1)", "Colocamos x² fora dos parênteses e mantemos x+1 dentro."),
            ("Confira pela distributividade", r"x^2\cdot x+x^2\cdot1=x^3+x^2", "Distribuir x² recupera a expressão original."),
        ], r"x^2(x+1)", []
    if compact in {"(x+2)^3", "(x+2)³"} and operation == "Desenvolver":
        return [
            ("Expressão original", r"(x+2)^3", "O expoente 3 indica três fatores iguais à base (x+2)."),
            ("Repita a base", r"(x+2)\cdot(x+2)\cdot(x+2)", "Escrevemos a potência como a multiplicação de três cópias do binômio."),
            ("Desenvolva os dois primeiros fatores", r"(x^2+4x+4)(x+2)", "Aplicamos a distributividade e reunimos 2x+2x=4x."),
            ("Distribua o terceiro fator", r"x^3+2x^2+4x^2+8x+4x+8", "Multiplicamos cada parcela do primeiro polinômio por x e depois por 2."),
            ("Reúna termos semelhantes", r"x^3+6x^2+12x+8", "Somamos 2x²+4x²=6x² e 8x+4x=12x."),
        ], r"x^3+6x^2+12x+8", []
    return None



def _special_exponential_fraction_steps(expr, operation):
    """Detailed reduction of the exponential fraction shown in the user's reference."""
    if operation not in {"Simplificar", "Simplificar fração"}:
        return None
    n = sp.Symbol("n", real=True)
    target = (2**(n+2) + 2**(n+1) + 3*2**n) / (2**(n-1) - 5*2**n)
    try:
        if sp.simplify(expr - target) != 0:
            return None
    except Exception:
        return None
    steps = [
        ("Expressão original", r"\frac{2^{n+2}+2^{n+1}+3\cdot2^n}{2^{n-1}-5\cdot2^n}", "Vamos colocar em evidência a mesma potência de base 2. O objetivo é transformar cada parcela em um múltiplo de 2ⁿ."),
        ("Reescreva as potências do numerador", r"2^{n+2}=2^n\cdot2^2,\qquad 2^{n+1}=2^n\cdot2", "Na multiplicação de potências de mesma base, somamos os expoentes. Por isso, para separar o acréscimo 2 ou 1, escrevemos 2ⁿ vezes 2² ou 2."),
        ("Reescreva a potência do denominador", r"2^{n-1}=\frac{2^n}{2}", "Diminuir 1 no expoente equivale a dividir a potência por 2: 2ⁿ⁻¹ = 2ⁿ/2."),
        ("Substitua na fração", r"\frac{2^n\cdot2^2+2^n\cdot2+3\cdot2^n}{\frac{2^n}{2}-5\cdot2^n}", "Agora todas as parcelas têm o fator 2ⁿ. Ainda não cancelamos nada: primeiro vamos fatorar o numerador e o denominador."),
        ("Coloque 2ⁿ em evidência no numerador", r"\frac{2^n(2^2+2+3)}{\frac{2^n}{2}-5\cdot2^n}", "No numerador, 2ⁿ aparece nas três parcelas. Ao colocá-lo em evidência, ficam dentro dos parênteses 2², 2 e 3."),
        ("Coloque 2ⁿ em evidência no denominador", r"\frac{2^n(4+2+3)}{2^n(\frac12-5)}", "Também podemos colocar 2ⁿ em evidência no denominador. Em 2ⁿ/2, o coeficiente é 1/2; na outra parcela, é −5."),
        ("Calcule os números entre parênteses", r"\frac{2^n(9)}{2^n(-\frac92)}", "No numerador: 4+2+3=9. No denominador: 1/2−5=1/2−10/2=−9/2."),
        ("Cancele o fator comum", r"\frac{2^n\cdot9}{2^n\cdot(-\frac92)}\;\Longrightarrow\;\frac{9}{-\frac92}", "Como 2ⁿ é sempre positivo para todo n real, ele nunca vale zero. Portanto, o fator 2ⁿ pode ser cancelado com segurança."),
        ("Divida por uma fração", r"\frac{9}{-\frac92}=9\cdot\left(-\frac29\right)", "Dividir por −9/2 equivale a multiplicar pelo inverso −2/9."),
        ("Resultado final", r"9\cdot\left(-\frac29\right)=\boxed{-2}", "O 9 do numerador cancela com o 9 do denominador. A expressão vale −2 para todo n real."),
    ]
    return steps, r"-2", []

def build_algebra_steps(source: str, operation: str):
    """Return detailed steps, a final result and original-domain exclusions."""
    cleaned = source.strip()

    # Parse once while retaining symbolic denominators. This same original
    # expression is used for the domain, even if simplification removes a factor.
    expr_for_domain = None
    if operation not in {"Resolver equação", "Resolver inequação"}:
        expr_for_domain = parse_math(cleaned, preserve_division=True, preserve_structure=True)
        expr = parse_math(cleaned, preserve_division=True)

    raw_special = _special_raw_steps(cleaned, operation)
    if raw_special is not None:
        steps, result, restrictions = raw_special
        steps = list(steps)
        steps.append(_domain_step(expr_for_domain))
        return steps, result, restrictions

    if operation == "Resolver equação":
        relation = parse_equation(cleaned)
        symbols = sorted(relation.free_symbols, key=lambda s: s.name)
        if len(symbols) != 1:
            raise ExpressionError("Nesta versão, resolva equações com uma única variável.")
        var = symbols[0]
        zero_form = sp.simplify(relation.lhs - relation.rhs)
        factored = sp.factor(zero_form)
        solutions = sp.solve(relation, var)
        final = sp.FiniteSet(*solutions)
        steps = [
            ("Equação original", latex(relation), "Identificamos os dois membros da igualdade e a variável que queremos determinar."),
            ("Reúna os termos em um único membro", latex(zero_form) + r"=0", "Subtraímos o segundo membro dos dois lados. Assim, a equação fica na forma de uma expressão igual a zero."),
        ]
        if factored != zero_form:
            steps.append(("Fatore a expressão", latex(factored) + r"=0", "A fatoração transforma a soma em um produto. Isso permite aplicar o princípio do produto nulo."))
        steps.append(("Resolva os fatores", latex(final), "Pelo princípio do produto nulo ou pela resolução simbólica, encontramos os valores que tornam a igualdade verdadeira."))
        if "2^(2x)" in cleaned.replace(" ", "") or "2**(2*x)" in cleaned.replace(" ", ""):
            steps = [
                ("Equação original", r"2^{2x}-5\cdot2^x+4=0", "A expressão contém 2ˣ e 2²ˣ. Vamos usar uma substituição para transformá-la em uma equação quadrática."),
                ("Faça uma substituição", r"t=2^x,\quad t>0", "Como 2ˣ é sempre positivo, a variável auxiliar t também deve ser positiva."),
                ("Reescreva a equação", r"t^2-5t+4=0", "Como 2²ˣ=(2ˣ)², substituímos 2ˣ por t e 2²ˣ por t²."),
                ("Fatore o trinômio", r"(t-1)(t-4)=0", "Procuramos dois números com produto 4 e soma 5: 1 e 4. Por isso, o trinômio se decompõe nesses dois fatores."),
                ("Aplique o princípio do produto nulo", r"t-1=0\quad\text{ou}\quad t-4=0", "Um produto é zero quando pelo menos um dos fatores é zero."),
                ("Resolva para t", r"t=1\quad\text{ou}\quad t=4", "Isolamos t em cada uma das duas equações."),
                ("Retorne à variável x", r"2^x=1\Rightarrow x=0;\quad 2^x=4\Rightarrow x=2", "Como 1=2⁰ e 4=2², igualamos os expoentes das potências de mesma base."),
                ("Solução", r"S=\{0,2\}", "As duas soluções satisfazem a equação original."),
            ]
        return steps, latex(final), []

    if operation == "Resolver inequação":
        relation = parse_inequality(cleaned)
        symbols = sorted(relation.free_symbols, key=lambda s: s.name)
        if len(symbols) != 1:
            raise ExpressionError("Nesta versão, resolva inequações com uma única variável.")
        var = symbols[0]
        solution = sp.solve_univariate_inequality(relation, var, relational=False)
        lhs, rhs = relation.lhs, relation.rhs
        if isinstance(lhs, sp.Pow) and lhs.exp == var and rhs.is_number and rhs.is_positive:
            base = lhs.base
            if base.is_number and base.is_real and base > 0 and base != 1:
                rhs_exp = sp.simplify(sp.log(rhs, base))
                if rhs_exp.is_real and rhs_exp.is_number:
                    increasing = bool(base > 1)
                    relation_sign = ">" if isinstance(relation, (sp.StrictGreaterThan, sp.GreaterThan)) else "<" if isinstance(relation, (sp.StrictLessThan, sp.LessThan)) else ""
                    exponent_sign = relation_sign if increasing else ("<" if relation_sign == ">" else ">")
                    solution_formula = rf"{latex(var)} {exponent_sign} {latex(rhs_exp)}"
                    base_trend = "crescente" if increasing else "decrescente"
                    steps = [
                        ("Inequação original", latex(relation), "A incógnita aparece no expoente de uma função exponencial."),
                        ("Identifique a base", rf"a={latex(base)}", rf"A base é positiva e diferente de 1. Como \(a={latex(base)}\), a função exponencial é {base_trend} em ℝ."),
                        ("Escreva os dois membros com a mesma base", rf"{latex(base)}^{{{latex(var)}}} {relation_sign} {latex(base)}^{{{latex(rhs_exp)}}}", "Reescrevemos o segundo membro como uma potência de base igual à primeira."),
                        ("Compare os expoentes", solution_formula, "Como a função é crescente quando a base é maior que 1, o sentido da desigualdade é preservado. Para uma base entre 0 e 1, seria invertido."),
                        ("Conjunto-solução", latex(solution), "Este intervalo reúne exatamente os valores reais que satisfazem a inequação."),
                    ]
                    return steps, latex(solution), []
        steps = [
            ("Inequação original", latex(relation), "Identificamos a comparação e a única variável da inequação."),
            ("Reescreva a comparação em relação a zero", latex(sp.simplify(relation.lhs-relation.rhs)) + r"\;\text{(comparado com 0)}", "Subtraímos o segundo membro dos dois lados, preservando o sentido da desigualdade."),
            ("Resolva a desigualdade", latex(solution), "O motor simbólico determina o conjunto dos valores reais que satisfazem a relação."),
            ("Conjunto-solução", latex(solution), "A solução é apresentada como intervalo ou união de intervalos reais."),
        ]
        return steps, latex(solution), []

    original_formula = _source_formula(cleaned, expr)
    special_exponential = _special_exponential_fraction_steps(expr, operation)
    if special_exponential is not None:
        steps, result, restrictions = special_exponential
        steps = list(steps)
        steps.append(_domain_step(expr))
        return steps, result, restrictions

    numeric_steps = _numeric_power_steps(cleaned, expr) if operation in {"Simplificar", "Simplificar fração"} else None
    restrictions = original_restrictions(expr_for_domain)

    if numeric_steps is not None:
        result_expr = sp.simplify(expr)
        steps = [("Expressão original", original_formula, "Esta é a expressão exatamente como foi digitada. Vamos avaliar as potências antes de somar e subtrair."), *numeric_steps[1:]]
        steps.append(_domain_step(expr))
        return steps, latex(result_expr), restrictions

    # For a fraction, factor numerator and denominator independently before
    # cancellation. The preserved tree keeps original exclusions visible.
    is_rational = any(isinstance(node, sp.Pow) and node.exp.is_negative for node in sp.preorder_traversal(expr))
    if operation in {"Simplificar fração"} or (operation == "Simplificar" and is_rational):
        result = sp.cancel(expr)
        steps = _fraction_steps(expr, restrictions)
        # Keep the user's ordering and signs in the first step.
        if steps:
            steps[0] = (steps[0][0], original_formula, steps[0][2])
    elif operation in {"Fatorar", "Colocar em evidência"}:
        result = sp.factor(expr) if operation == "Fatorar" else sp.factor_terms(expr)
        steps = _factor_steps(expr, result)
        steps[0] = (steps[0][0], original_formula, steps[0][2])
    elif operation == "Desenvolver":
        result = sp.expand(expr)
        steps = _expand_steps(expr, result)
        steps[0] = (steps[0][0], original_formula, steps[0][2])
    else:
        result = sp.simplify(expr)
        factored = sp.factor_terms(expr)
        steps = [
            ("Expressão original", original_formula, "Esta é a expressão informada. Primeiro vamos observar sua estrutura e identificar quais operações podem ser realizadas."),
        ]
        if factored != expr:
            steps.append(("Agrupe fatores comuns", latex(factored), "Reescrevemos a expressão agrupando fatores que aparecem em mais de uma parcela. Essa transformação mantém a equivalência."))
        if is_rational:
            numerator, denominator = sp.fraction(sp.together(expr))
            steps.append(("Analise numerador e denominador", rf"\frac{{{latex(sp.factor(numerator))}}}{{{latex(sp.factor(denominator))}}}", "Colocamos a fração em uma forma que permite examinar os fatores de cima e de baixo separadamente."))
        steps.append(("Aplique as simplificações válidas", latex(result), "O motor algébrico aplica identidades exatas, reúne termos equivalentes e reduz fatores quando isso é permitido."))
        if result == expr:
            steps.append(("Confira a expressão", latex(result), "A expressão já está em uma forma simplificada para as regras disponíveis. Nenhum cancelamento adicional é válido."))

    steps.append(_domain_step(expr))
    return steps, latex(result), restrictions

