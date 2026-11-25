"""Randomized practice questions with worked, multi-step explanations."""
from __future__ import annotations
import random


def _question(level, prompt, answer, wrong, solution_steps):
    options = [str(answer)]
    for item in wrong:
        item = str(item)
        if item not in options:
            options.append(item)
        if len(options) == 4:
            break
    # The generators below deliberately provide three distinct distractors.
    if len(options) != 4:
        raise ValueError("A questão não produziu quatro alternativas distintas.")
    random.shuffle(options)
    return {
        "level": level,
        "prompt": prompt,
        "answer": str(answer),
        "options": options,
        "solution_steps": solution_steps,
    }


def make_question(level: str):
    """Create one randomized question in the selected difficulty band."""
    if level == "Básico":
        kind = random.choice(["multiplicação", "divisão", "zero"])
        if kind == "multiplicação":
            base = random.choice([2, 3, 4, 5, 7])
            m, n = random.randint(1, 5), random.randint(1, 5)
            exponent = m + n
            distractors = list(dict.fromkeys(v for v in [m*n, m-n, m+n+1, m+n-1, m+2*n, 2*m+n] if v != exponent))
            return _question(
                level,
                f"Simplifique: {base}^{m} · {base}^{n}",
                f"{base}^{exponent}",
                [f"{base}^{value}" for value in distractors],
                [
                    ("Observe as bases", rf"{base}^{{{m}}}\cdot {base}^{{{n}}}", f"As duas potências têm a mesma base, {base}. Isso permite reunir todos os fatores iguais."),
                    ("Escreva a propriedade", rf"a^m\cdot a^n=a^{{m+n}}", "Na multiplicação de potências de mesma base, conservamos a base e somamos os expoentes."),
                    ("Substitua os expoentes", rf"{base}^{{{m}+{n}}}", f"O primeiro expoente informa {m} fatores; o segundo informa {n} fatores."),
                    ("Some as quantidades", rf"{m}+{n}={exponent}", f"Juntando os grupos, temos {exponent} fatores iguais à base {base}."),
                    ("Resposta", rf"{base}^{{{exponent}}}", "A base permanece igual e o novo expoente é a soma encontrada."),
                ],
            )
        if kind == "divisão":
            base = random.choice([2, 3, 5, 7])
            n = random.randint(1, 3)
            m = random.randint(n+1, n+4)
            exponent = m-n
            distractors = list(dict.fromkeys(v for v in [m+n, n-m, exponent+1, exponent+2, m*n] if v != exponent))
            return _question(
                level,
                f"Simplifique: {base}^{m} / {base}^{n}",
                f"{base}^{exponent}",
                [f"{base}^{value}" for value in distractors],
                [
                    ("Observe a divisão", rf"\frac{{{base}^{{{m}}}}}{{{base}^{{{n}}}}}", "As bases são iguais e não nulas. Podemos comparar quantos fatores aparecem em cima e embaixo."),
                    ("Desenvolva as potências", rf"\frac{{\underbrace{{{base}\cdot\ldots\cdot {base}}}_{{{m}\text{{ fatores}}}}}}{{\underbrace{{{base}\cdot\ldots\cdot {base}}}_{{{n}\text{{ fatores}}}}}}", "Cada fator do numerador pode ser simplificado com um fator igual do denominador."),
                    ("Cancele os fatores comuns", rf"\text{{Restam }}{m}-{n}\text{{ fatores de }}{base}", f"Os {n} fatores do denominador cancelam com {n} fatores do numerador."),
                    ("Subtraia os expoentes", rf"{m}-{n}={exponent}", "Na divisão de potências de mesma base, fazemos expoente do numerador menos expoente do denominador."),
                    ("Resposta", rf"{base}^{{{exponent}}}", "Restam exatamente os fatores representados pela potência indicada."),
                ],
            )
        base = random.choice([2, 3, 5, 7, 10])
        return _question(
            level,
            f"Qual é o valor de {base}⁰?",
            "1",
            ["0", str(base), f"1/{base}"],
            [
                ("Comece com uma potência conhecida", rf"\frac{{{base}^3}}{{{base}^3}}", "Como a base é não nula, qualquer número dividido por ele mesmo vale 1."),
                ("Use a propriedade da divisão", rf"\frac{{{base}^3}}{{{base}^3}}={base}^{{3-3}}", "Na divisão de potências da mesma base, subtraímos os expoentes."),
                ("Calcule o expoente", r"3-3=0", "A diferença entre os expoentes é zero."),
                ("Conclua", rf"{base}^0=1", "Portanto, toda base não nula elevada a zero vale 1."),
            ],
        )

    if level == "Intermediário":
        kind = random.choice(["expoente negativo", "expoente fracionário", "fatoração", "fração algébrica"])
        if kind == "expoente negativo":
            base = random.choice([2, 3, 5])
            m = random.randint(2, 5)
            n = random.randint(1, m-1)
            exponent = n-m
            answer = f"1/{base}^{-exponent}"
            return _question(
                level,
                f"Simplifique e escreva com expoente positivo: {base}⁻{m} · {base}^{n}",
                answer,
                [f"{base}^{m+n}", f"{base}^{m-n}", f"1/{base}^{m+n}"],
                [
                    ("Identifique a propriedade", rf"{base}^{{-{m}}}\cdot {base}^{{{n}}}", "As bases são iguais; portanto, somamos os expoentes. O sinal negativo não significa uma quantidade negativa de fatores."),
                    ("Some com atenção aos sinais", rf"-{m}+{n}={exponent}", f"Partimos de −{m} e avançamos {n} unidades em direção ao zero."),
                    ("Reescreva a potência", rf"{base}^{{{exponent}}}={base}^{{-{(-exponent)}}}", "O expoente encontrado é negativo. Pela definição de potência negativa, tomamos o inverso da potência positiva correspondente."),
                    ("Passe para a forma fracionária", rf"{base}^{{-{(-exponent)}}}=\frac{{1}}{{{base}^{{{-exponent}}}}}", "O sinal negativo transforma a potência em seu inverso multiplicativo."),
                    ("Resposta", rf"\frac{{1}}{{{base}^{{{-exponent}}}}}", "A expressão está simplificada e o expoente aparece positivo no denominador."),
                ],
            )
        if kind == "expoente fracionário":
            base, index, power = random.choice([(8,3,2),(27,3,2),(16,4,3),(81,4,2)])
            root = round(base ** (1/index))
            answer_value = root ** power
            distractors = list(dict.fromkeys(str(v) for v in [root, base, answer_value + root, answer_value + 1, root*power] if v != answer_value))
            return _question(
                level,
                f"Calcule: {base}^({power}/{index})",
                str(answer_value),
                distractors,
                [
                    ("Leia o expoente fracionário", rf"{base}^{{\frac{{{power}}}{{{index}}}}}", f"O denominador {index} indica a raiz de índice {index}; o numerador {power} indica a potência à qual o resultado da raiz será elevado."),
                    ("Converta em radical", rf"\left(\sqrt[{index}]{{{base}}}\right)^{{{power}}}", "Usamos a equivalência entre expoente fracionário e radical."),
                    ("Calcule a raiz", rf"\sqrt[{index}]{{{base}}}={root}", f"De fato, {root}^{index}={base}."),
                    ("Eleve o resultado", rf"{root}^{power}={answer_value}", f"Agora calculamos {root} elevado ao numerador {power}."),
                    ("Resposta", str(answer_value), "O valor da potência é o número obtido após calcular a raiz e depois a potência."),
                ],
            )
        if kind == "fatoração":
            return _question(
                level,
                "Fatore colocando o fator comum em evidência: x³ + x²",
                "x²(x + 1)",
                ["x(x + 1)", "x²(x − 1)", "x³(x + 1)"],
                [
                    ("Separe os termos", r"x^3+x^2", "A expressão tem dois termos: x³ e x². Vamos procurar a maior potência de x que divide os dois."),
                    ("Identifique o fator comum", r"x^2", "x² divide x³ e também divide x². Por isso é o fator comum que podemos colocar em evidência."),
                    ("Divida o primeiro termo", r"\frac{x^3}{x^2}=x", "Ao retirar x² de x³, sobra um fator x."),
                    ("Divida o segundo termo", r"\frac{x^2}{x^2}=1", "Ao retirar x² de x², sobra 1."),
                    ("Monte o produto", r"x^2(x+1)", "Colocamos o fator comum do lado de fora e os quocientes dentro dos parênteses."),
                    ("Confira pela distributividade", r"x^2\cdot x+x^2\cdot1=x^3+x^2", "Distribuir x² recupera exatamente os dois termos iniciais."),
                ],
            )
        return _question(
            level,
            "Simplifique: (x² − x³)/(x³ + x⁵)",
            "(1 − x)/(x + x³), com x ≠ 0",
            ["(1 − x)/(1 + x²)", "(x − 1)/(x + x³)", "(1 − x)/(x² + x³)"],
            [
                ("Registre a expressão e seu domínio", r"\frac{x^2-x^3}{x^3+x^5}", "O denominador original não pode ser zero. Fatoraremos os dois polinômios antes de cancelar qualquer fator."),
                ("Fatore o numerador", r"x^2-x^3=x^2(1-x)", "Colocamos x² em evidência: x² dividido por x² dá 1; x³ dividido por x² dá x."),
                ("Fatore o denominador", r"x^3+x^5=x^2(x+x^3)", "O fator comum é x²: x³ dividido por x² dá x, e x⁵ dividido por x² dá x³."),
                ("Substitua as fatorações", r"\frac{x^2(1-x)}{x^2(x+x^3)}", "Agora a fração está escrita como produto de fatores no numerador e no denominador."),
                ("Cancele somente o fator comum", r"\frac{x^2(1-x)}{x^2(x+x^3)}\;\Longrightarrow\;\frac{1-x}{x+x^3}", "O x² é um fator multiplicativo inteiro. Não podemos cancelar parcelas de uma soma, como 1−x ou x+x³."),
                ("Preserve a restrição", r"x^2(x+x^3)\ne0\Rightarrow x\ne0", "O denominador original se anula em x=0. A simplificação não devolve esse valor ao domínio."),
                ("Resposta final", r"\frac{1-x}{x+x^3},\quad x\ne0", "Esta é a forma simplificada, acompanhada da condição herdada da expressão original."),
            ],
        )

    if level == "Difícil":
        kind = random.choice(["equação exponencial", "inequação exponencial", "interpretação de gráfico"])
        if kind == "equação exponencial":
            base = random.choice([2, 3])
            u, v = sorted(random.sample(range(2, 6), 2))
            p, q = base**u, base**v
            coefficient, constant = p+q, p*q
            answer = f"x = {u} ou x = {v}"
            return _question(
                level,
                f"Resolva em ℝ: {base}^(2x) − {coefficient}·{base}^x + {constant} = 0",
                answer,
                [f"x = {u+v}", f"x = {u*v}", f"x = −{u} ou x = −{v}"],
                [
                    ("Observe a estrutura exponencial", rf"{base}^{{2x}}-{coefficient}\cdot {base}^x+{constant}=0", "Aparecem a potência 2ˣ e seu quadrado, pois a base é a mesma e 2x é o dobro de x."),
                    ("Faça uma substituição", rf"t={base}^x,\quad t>0", "Toda potência de base positiva é positiva. Portanto, t não pode ser zero nem negativo."),
                    ("Reescreva a potência maior", rf"{base}^{{2x}}=({base}^x)^2=t^2", "Como 2x=2·x, podemos escrever a primeira parcela como o quadrado de 2ˣ."),
                    ("Monte a equação quadrática", rf"t^2-({coefficient})t+{constant}=0", "Substituímos cada ocorrência de 2ˣ por t e obtemos uma equação do segundo grau."),
                    ("Fatore o trinômio", rf"(t-{p})(t-{q})=0", f"Os números {p} e {q} têm produto {constant} e soma {coefficient}."),
                    ("Use o princípio do produto nulo", rf"t={p}\quad\text{{ou}}\quad t={q}", "Para o produto ser zero, pelo menos um dos fatores precisa ser zero."),
                    ("Retorne à variável original", rf"{base}^x={base}^{u}\quad\text{{ou}}\quad {base}^x={base}^{v}", f"Como {p}={base}^{u} e {q}={base}^{v}, escrevemos os dois lados com a mesma base."),
                    ("Iguale os expoentes", rf"x={u}\quad\text{{ou}}\quad x={v}", "A função exponencial de base maior que 1 é injetiva; potências iguais de mesma base têm expoentes iguais."),
                    ("Resposta final", rf"S=\{{{u},{v}\}}", "As duas soluções satisfazem a equação original e a substituição t=2ˣ respeita t>0."),
                ],
            )
        if kind == "inequação exponencial":
            base = random.choice([2, 3, 5])
            threshold = random.randint(1, 5)
            return _question(
                level,
                f"Resolva em ℝ: {base}^x > {base}^{threshold}",
                f"x > {threshold}",
                [f"x < {threshold}", f"x ≥ {threshold}", f"x > −{threshold}"],
                [
                    ("Compare as bases", rf"{base}^x>{base}^{{{threshold}}}", f"Os dois membros são potências da mesma base, {base}."),
                    ("Verifique o comportamento da função", rf"g(x)={base}^x", f"Como {base}>1, a função exponencial é estritamente crescente em ℝ."),
                    ("Use a monotonicidade", rf"{base}^x>{base}^{{{threshold}}}\Rightarrow x>{threshold}", "Em uma função crescente, valores maiores na imagem correspondem a valores maiores no domínio. O sentido da desigualdade é preservado."),
                    ("Interprete a solução", rf"x\in({threshold},+\infty)", f"Todos os reais maiores que {threshold} satisfazem a desigualdade; o próprio {threshold} não satisfaz porque a desigualdade é estrita."),
                    ("Resposta final", rf"x>{threshold}", "Esse é o conjunto-solução da inequação."),
                ],
            )
        base = random.choice([2, 3])
        x_value = random.randint(2, 4)
        answer_value = base**x_value
        return _question(
            level,
            f"Uma função é dada por g(x) = {base}^x. Qual é a ordenada do ponto da curva cuja abscissa é x = {x_value}?",
            str(answer_value),
            [str(base**(x_value+1)), str(base**(x_value-1)), str(answer_value+1)],
            [
                ("Identifique o que foi informado", rf"g(x)={base}^x,\quad x={x_value}", "A abscissa do ponto é o valor de x. Precisamos calcular a imagem desse valor pela função."),
                ("Substitua x na função", rf"g({x_value})={base}^{{{x_value}}}", "No lugar de x, colocamos o valor indicado no enunciado."),
                ("Calcule a potência", rf"{base}^{{{x_value}}}={answer_value}", f"Multiplicamos {base} por ele mesmo {x_value} vezes."),
                ("Escreva as coordenadas", rf"P=({x_value},{answer_value})", "A primeira coordenada é a abscissa x; a segunda é a ordenada g(x)."),
                ("Resposta", str(answer_value), "A ordenada pedida é o valor de g(x), portanto é o segundo número do par ordenado."),
            ],
        )

    raise ValueError("Nível desconhecido. Escolha Básico, Intermediário ou Difícil.")
