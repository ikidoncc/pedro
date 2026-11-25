"""Prepared, auditable demonstrations for the eight exponent laws."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class Step:
    title: str
    formula: str
    explanation: str
    visual: str = "equation"

@dataclass(frozen=True)
class Example:
    label: str
    steps: List[Step]

@dataclass(frozen=True)
class Property:
    label: str
    rule: str
    note: str
    examples: List[Example]


def S(title, formula, explanation, visual="equation"):
    return Step(title, formula, explanation, visual)

PROPERTIES = {
"mult": Property("Multiplicação de potências de mesma base", "aᵐ · aⁿ = aᵐ⁺ⁿ", "Mantendo a mesma base não nula, reunimos os fatores iguais e somamos suas quantidades.", [
    Example("3³ · 3⁵", [
        S("Expressão inicial", "<span class='base'>3</span><sup class='exp-purple'>3</sup> <span class='operator'>·</span> <span class='base'>3</span><sup class='exp-red'>5</sup>", "Temos duas potências de base 3. O expoente roxo identifica a primeira potência; o vermelho identifica a segunda.", "initial"),
        S("Desenvolva a primeira potência", "<span class='factor purple'>3</span> · <span class='factor purple'>3</span> · <span class='factor purple'>3</span>", "O expoente 3 indica três fatores iguais à base 3. Cada fator recebe a cor do expoente de origem.", "first_factors"),
        S("Desenvolva a segunda potência", "<span class='factor red'>3</span> · <span class='factor red'>3</span> · <span class='factor red'>3</span> · <span class='factor red'>3</span> · <span class='factor red'>3</span>", "O expoente 5 indica cinco fatores iguais à base 3. Eles permanecem identificados em vermelho.", "second_factors"),
        S("Agrupe as origens", "", "Os três fatores roxos formam um grupo; os cinco fatores vermelhos formam outro. As chaves inferiores registram quantos fatores existem em cada grupo.", "grouped"),
        S("Reúna os oito fatores", "3 · 3 · 3 · 3 · 3 · 3 · 3 · 3", "Ao retirar a separação entre as duas potências, temos uma única sequência de oito fatores iguais.", "joined"),
        S("Some os expoentes", "3<sup><span class='exp-purple'>3</span><span class='exp-red'>+5</span></sup> = 3<sup>8</sup>", "A quantidade total de fatores é 3 + 5 = 8. Por isso, os expoentes são somados.", "sum"),
        S("Resultado", "3<sup>8</sup> = <strong class='result'>6561</strong>", "Como as potências possuem a mesma base, reunimos todos os fatores iguais. Por isso, somamos os expoentes.", "result"),
    ]),
    Example("4⁻⁵ · 4³", [
        S("Expressão inicial", "4<sup class='exp-purple'>−5</sup> · 4<sup class='exp-red'>3</sup>", "As bases são iguais. O expoente negativo representa o inverso multiplicativo, não uma quantidade negativa de fatores."),
        S("Interprete o expoente negativo", "(1 / 4<sup>5</sup>) · 4<sup>3</sup>", "Substituímos 4⁻⁵ por seu inverso: 1/4⁵. Assim, não tentamos criar −5 fatores."),
        S("Reúna os expoentes", "4<sup>−5+3</sup> = 4<sup>−2</sup>", "A propriedade de multiplicação conserva a base e soma os expoentes: −5 + 3 = −2."),
        S("Volte à forma de fração", "4<sup>−2</sup> = 1 / 4<sup>2</sup>", "Um expoente negativo indica o inverso da potência com expoente positivo."),
        S("Resultado", "1 / 16", "A expressão vale 1/16."),
    ]),
    Example("7⁶ · 7⁻⁴", [
        S("Expressão inicial", "7<sup>6</sup> · 7<sup>−4</sup>", "As bases são iguais; podemos somar os expoentes."),
        S("Interprete o expoente negativo", "7<sup>6</sup> · (1 / 7<sup>4</sup>)", "A segunda potência equivale ao inverso de 7⁴."),
        S("Some os expoentes", "7<sup>6+(−4)</sup> = 7<sup>2</sup>", "6 + (−4) = 2."),
        S("Resultado", "7<sup>2</sup> = 49", "A potência restante é 7², cujo valor é 49."),
    ]),
    Example("2² · 2⁻³ · 2⁻⁴ · 2⁵", [
        S("Expressão inicial", "2<sup>2</sup> · 2<sup>−3</sup> · 2<sup>−4</sup> · 2<sup>5</sup>", "Todas as potências têm base 2."),
        S("Reúna as potências", "2<sup>2−3−4+5</sup>", "A multiplicação sucessiva permite somar todos os expoentes, inclusive os negativos."),
        S("Calcule a soma", "2<sup>0</sup>", "2 − 3 − 4 + 5 = 0."),
        S("Resultado", "2<sup>0</sup> = 1", "Toda base não nula elevada a zero é igual a 1."),
    ]),
]),
"div": Property("Divisão de potências de mesma base", "aᵐ / aⁿ = aᵐ⁻ⁿ (a ≠ 0)", "Na divisão, fatores iguais do numerador e do denominador se cancelam. A base deve ser diferente de zero.", [
    Example("a³ / a²", [S("Expressão inicial", "a<sup>3</sup> / a<sup>2</sup>", "A base é a mesma e a divisão exige a ≠ 0."), S("Desenvolva as potências", "(a · a · a) / (a · a)", "O numerador tem três fatores a; o denominador tem dois."), S("Cancele fatores comuns", "(a̶ · a̶ · a) / (a̶ · a̶)", "Um fator a do numerador cancela com cada fator a do denominador."), S("Subtraia os expoentes", "a<sup>3−2</sup> = a", "Restam 3 − 2 = 1 fatores no numerador."), S("Resultado e condição", "a, <span class='condition'>a ≠ 0</span>", "A restrição a ≠ 0 permanece porque a expressão original tinha a² no denominador.")]),
    Example("5² / 5⁵", [S("Expressão inicial", "5<sup>2</sup> / 5<sup>5</sup>", "As bases são iguais e não nulas."), S("Subtraia os expoentes", "5<sup>2−5</sup> = 5<sup>−3</sup>", "Na divisão, fazemos expoente do numerador menos expoente do denominador."), S("Interprete o expoente negativo", "1 / 5<sup>3</sup>", "O resultado é o inverso de 5³."), S("Resultado", "1 / 125", "5³ = 125.")]),
    Example("3⁻² / 3⁻⁵", [S("Expressão inicial", "3<sup>−2</sup> / 3<sup>−5</sup>", "A base 3 é não nula."), S("Subtraia os expoentes", "3<sup>−2−(−5)</sup> = 3<sup>3</sup>", "Subtrair −5 equivale a somar 5: −2 + 5 = 3."), S("Resultado", "3<sup>3</sup> = 27", "O resultado é 27.")]),
    Example("x⁴ / x⁻²", [S("Expressão inicial", "x<sup>4</sup> / x<sup>−2</sup>", "A divisão exige x ≠ 0."), S("Subtraia os expoentes", "x<sup>4−(−2)</sup> = x<sup>6</sup>", "Subtrair um expoente negativo equivale a somá-lo com sinal trocado."), S("Resultado", "x<sup>6</sup>, <span class='condition'>x ≠ 0</span>", "A restrição da expressão original continua válida.")]),
]),
"power": Property("Potência de potência", "(aᵐ)ⁿ = aᵐ·ⁿ", "A potência externa repete o bloco interno. Contamos quantos fatores há em cada bloco e quantos blocos existem; por isso, multiplicamos os expoentes.", [
    Example("(5²)³", [
        S("Expressão inicial", "(<span class='base'>5</span><sup class='exp-blue'>2</sup>)<sup class='exp-red outer-exp'>3</sup>", "O expoente azul 2 informa quantos fatores 5 existem em cada bloco. O expoente vermelho 3 informa quantas vezes o bloco inteiro será repetido.", "power_initial"),
        S("Abra o expoente externo: crie três blocos", "(5<sup class='exp-blue'>2</sup>) · (5<sup class='exp-blue'>2</sup>) · (5<sup class='exp-blue'>2</sup>)", "O expoente externo 3 cria três cópias idênticas da potência interna. Os contornos vermelhos identificam cada bloco; o expoente azul continua indicando dois fatores em cada um.", "power_blocks"),
        S("Abra o expoente interno em cada bloco", "(5 · 5) · (5 · 5) · (5 · 5)", "Agora desenvolvemos cada 5². Em cada bloco aparecem dois fatores 5 azuis. Os parênteses vermelhos continuam mostrando que existem três blocos.", "power_inner"),
        S("Conte os fatores de cada bloco", "2 fatores × 3 blocos", "Cada bloco contém dois fatores 5 e há três blocos iguais. A quantidade total é formada por 2 + 2 + 2, isto é, três grupos de dois.", "power_groups"),
        S("Reúna os seis fatores", "5 · 5 · 5 · 5 · 5 · 5", "Ao retirar os parênteses, vemos uma única sequência com seis fatores iguais a 5. Todos permanecem azuis porque vieram do expoente interno 2.", "power_joined"),
        S("Conte a quantidade total", "2 + 2 + 2 = 6  ⇔  2 · 3 = 6", "Somar três grupos de dois equivale a multiplicar a quantidade de fatores por bloco pela quantidade de blocos: 2 vezes 3 é 6.", "power_count"),
        S("Aplique a propriedade", "5<sup class='exp-blue'>2</sup><sup class='exp-red'>·3</sup> = 5<sup class='exp-gold'>6</sup>", "A potência interna fornece 2 fatores por bloco; a externa fornece 3 blocos. Portanto, multiplicamos os expoentes: 2 · 3 = 6. Não somamos 2 + 3.", "power_rule"),
        S("Resultado", "5<sup class='exp-gold'>6</sup> = <strong class='result'>15625</strong>", "A expressão (5²)³ equivale a 5⁶. O valor numérico é 15 625.", "power_result"),
    ]),
    Example("(5⁻²)³", [
        S("Expressão inicial", "(5<sup class='exp-blue'>−2</sup>)<sup class='exp-red'>3</sup>", "A potência interna tem expoente negativo e a potência externa repete esse bloco três vezes."),
        S("Interprete a potência interna", "(1 / 5<sup class='exp-blue'>2</sup>)<sup class='exp-red'>3</sup>", "Antes de contar fatores, transformamos 5⁻² no inverso de 5²."),
        S("Repita o bloco três vezes", "(1/5²) · (1/5²) · (1/5²)", "O expoente externo 3 cria três frações iguais. Cada fração contém dois fatores 5 no denominador."),
        S("Desenvolva os denominadores", "1 / [(5 · 5) · (5 · 5) · (5 · 5)]", "Cada 5² se abre em dois fatores. Temos três grupos com dois fatores cada."),
        S("Conte os fatores", "2 · 3 = 6", "São seis fatores 5 no denominador. Por isso, os expoentes são multiplicados."),
        S("Multiplique os expoentes", "5<sup class='exp-blue'>−2</sup><sup class='exp-red'>·3</sup> = 5<sup class='exp-gold'>−6</sup>", "(−2) · 3 = −6. O sinal negativo permanece."),
        S("Escreva o inverso", "5<sup class='exp-gold'>−6</sup> = 1 / 5<sup class='exp-gold'>6</sup>", "O expoente negativo indica o inverso da potência positiva correspondente."),
        S("Resultado", "1 / 15625", "Como 5⁶ = 15 625, o resultado é 1/15 625."),
    ]),
    Example("(x⁴)⁻²", [
        S("Expressão inicial", "(x<sup class='exp-blue'>4</sup>)<sup class='exp-red'>−2</sup>", "O expoente interno 4 indica quatro fatores x; o expoente externo −2 pede o inverso de dois blocos."),
        S("Interprete o expoente externo negativo", "1 / (x<sup class='exp-blue'>4</sup>)<sup class='exp-red'>2</sup>", "O expoente −2 transforma a potência em 1 dividido pela mesma potência elevada a 2."),
        S("Repita o bloco interno", "1 / [(x⁴) · (x⁴)]", "O expoente externo positivo 2 indica dois blocos x⁴ no denominador."),
        S("Abra cada bloco", "1 / [(x · x · x · x) · (x · x · x · x)]", "Cada x⁴ se transforma em quatro fatores x. Os dois blocos totalizam oito fatores."),
        S("Conte os fatores", "4 · 2 = 8", "Há quatro fatores em cada bloco e dois blocos. Multiplicamos 4 por 2."),
        S("Multiplique os expoentes", "x<sup class='exp-blue'>4</sup><sup class='exp-red'>·(−2)</sup> = x<sup class='exp-gold'>−8</sup>", "4 · (−2) = −8. A regra vale também quando o expoente externo é negativo."),
        S("Volte à forma de fração", "1 / x<sup class='exp-gold'>8</sup>", "A potência com expoente −8 equivale ao inverso de x⁸."),
        S("Resultado e condição", "1 / x<sup class='exp-gold'>8</sup>, <span class='condition'>x ≠ 0</span>", "A expressão original não está definida em x=0, pois a base da potência externa não pode ser zero quando o expoente é negativo."),
    ]),
    Example("((3/2)²)³", [
        S("Expressão inicial", "((3/2)<sup class='exp-blue'>2</sup>)<sup class='exp-red'>3</sup>", "A fração 3/2 está elevada ao quadrado; depois, o bloco inteiro é elevado ao cubo."),
        S("Repita o bloco três vezes", "(3/2)² · (3/2)² · (3/2)²", "O expoente externo 3 cria três cópias da fração ao quadrado."),
        S("Abra o quadrado de cada bloco", "[(3/2) · (3/2)] · [(3/2) · (3/2)] · [(3/2) · (3/2)]", "Cada bloco passa a conter duas cópias da fração. Temos três blocos, cada um com dois fatores."),
        S("Separe numeradores e denominadores", "(3 · 3 · 3 · 3 · 3 · 3) / (2 · 2 · 2 · 2 · 2 · 2)", "Multiplicamos os numeradores entre si e os denominadores entre si. São seis fatores 3 e seis fatores 2."),
        S("Conte os fatores", "2 · 3 = 6", "Dois fatores em cada bloco, repetidos três vezes, totalizam seis fatores no numerador e seis no denominador."),
        S("Multiplique os expoentes", "(3/2)<sup class='exp-blue'>2</sup><sup class='exp-red'>·3</sup> = (3/2)<sup class='exp-gold'>6</sup>", "A potência de potência multiplica os expoentes: 2 · 3 = 6."),
        S("Calcule as potências", "3⁶ / 2⁶ = 729 / 64", "3⁶ vale 729 e 2⁶ vale 64."),
        S("Resultado", "729 / 64", "A forma exata do resultado é a fração 729/64."),
    ]),
]),
"product": Property("Potência de um produto", "(a · b)ⁿ = aⁿ · bⁿ", "O expoente atua sobre cada fator do produto.", [
    Example("(2 · 3)²", [S("Expressão inicial", "(2 · 3)<sup>2</sup>", "O produto inteiro está elevado ao quadrado."), S("Repita o produto", "(2 · 3) · (2 · 3)", "O expoente 2 indica dois blocos iguais."), S("Reagrupe fatores", "(2 · 2) · (3 · 3)", "Pela comutatividade e associatividade, agrupamos os fatores de mesma origem."), S("Distribua o expoente", "2<sup>2</sup> · 3<sup>2</sup>", "Cada fator recebe o expoente 2."), S("Resultado", "4 · 9 = 36", "O resultado coincide com (2 · 3)² = 6².")]),
    Example("(x · y)³", [S("Expressão inicial", "(x · y)<sup>3</sup>", "O produto xy é elevado à terceira potência."), S("Desenvolva", "(x · y) · (x · y) · (x · y)", "Temos três cópias do produto."), S("Agrupe bases iguais", "(x · x · x) · (y · y · y)", "Reunimos os três fatores x e os três fatores y."), S("Resultado", "x<sup>3</sup> · y<sup>3</sup>", "O expoente distribui-se pelos fatores do produto.")]),
    Example("(2a)⁻²", [S("Expressão inicial", "(2a)<sup>−2</sup>", "A base 2a deve ser diferente de zero; portanto a ≠ 0."), S("Aplique o expoente negativo", "1 / (2a)<sup>2</sup>", "Transformamos a potência no inverso."), S("Distribua o expoente", "1 / (2<sup>2</sup> · a<sup>2</sup>)", "A potência do produto atua sobre cada fator."), S("Resultado", "1 / (4a<sup>2</sup>), <span class='condition'>a ≠ 0</span>", "O resultado conserva a restrição da expressão original.")]),
    Example("(3/5 · 2/7)²", [S("Expressão inicial", "((3/5) · (2/7))<sup>2</sup>", "O produto de duas frações está ao quadrado."), S("Distribua o expoente", "(3/5)<sup>2</sup> · (2/7)<sup>2</sup>", "O expoente 2 atua sobre cada fator."), S("Eleve numeradores e denominadores", "(3<sup>2</sup>/5<sup>2</sup>) · (2<sup>2</sup>/7<sup>2</sup>)", "A potência de cada quociente atua no numerador e no denominador."), S("Resultado", "9/25 · 4/49 = 36/1225", "Multiplicando as frações, obtemos 36/1225.")]),
]),
"quotient": Property("Potência de um quociente", "(a / b)ⁿ = aⁿ / bⁿ (b ≠ 0)", "O expoente atua no numerador e no denominador; o denominador original precisa ser não nulo.", [
    Example("(2/3)²", [S("Expressão inicial", "(2/3)<sup>2</sup>", "A fração inteira está elevada ao quadrado."), S("Repita a fração", "(2/3) · (2/3)", "O expoente 2 indica duas cópias da fração."), S("Agrupe numeradores e denominadores", "(2 · 2) / (3 · 3)", "Multiplicamos os numeradores entre si e os denominadores entre si."), S("Distribua o expoente", "2<sup>2</sup> / 3<sup>2</sup>", "A potência atua separadamente sobre numerador e denominador."), S("Resultado", "4/9", "O resultado é 4/9.")]),
    Example("(x/y)³", [S("Expressão inicial", "(x/y)<sup>3</sup>", "A expressão exige y ≠ 0."), S("Distribua o expoente", "x<sup>3</sup> / y<sup>3</sup>", "Elevamos o numerador e o denominador à terceira potência."), S("Resultado e condição", "x<sup>3</sup> / y<sup>3</sup>, <span class='condition'>y ≠ 0</span>", "A restrição original continua válida.")]),
    Example("(4/5)⁻²", [S("Expressão inicial", "(4/5)<sup>−2</sup>", "O expoente negativo inverte a fração."), S("Inverta a base", "(5/4)<sup>2</sup>", "A potência negativa do quociente é o inverso da potência positiva."), S("Aplique o expoente", "5<sup>2</sup> / 4<sup>2</sup>", "Elevamos numerador e denominador ao quadrado."), S("Resultado", "25/16", "O valor é 25/16.")]),
    Example("(a/b)⁻³", [S("Expressão inicial", "(a/b)<sup>−3</sup>", "A expressão exige b ≠ 0 e a ≠ 0 para que a base do expoente negativo seja não nula."), S("Inverta a base", "(b/a)<sup>3</sup>", "O expoente negativo inverte o quociente."), S("Distribua o expoente", "b<sup>3</sup> / a<sup>3</sup>", "Elevamos o numerador e o denominador ao cubo."), S("Resultado e condições", "b<sup>3</sup> / a<sup>3</sup>, <span class='condition'>a ≠ 0, b ≠ 0</span>", "As condições vêm da expressão original.")]),
]),
"zero": Property("Expoente zero", "a⁰ = 1 (a ≠ 0)", "Toda base não nula elevada a zero vale 1. A condição a ≠ 0 é essencial.", [
    Example("5⁰", [S("Expressão inicial", "5<sup>0</sup>", "A base 5 é diferente de zero."), S("Use a divisão de potências", "5<sup>3</sup> / 5<sup>3</sup> = 5<sup>3−3</sup>", "Uma quantidade não nula dividida por ela mesma vale 1."), S("Resultado", "5<sup>0</sup> = 1", "3 − 3 = 0, portanto 5⁰ = 1.")]),
    Example("(−3)⁰", [S("Expressão inicial", "(−3)<sup>0</sup>", "A base completa é −3, que é não nula."), S("Aplique a propriedade", "(−3)<sup>0</sup> = 1", "O sinal faz parte da base, mas não altera a regra do expoente zero."), S("Resultado", "1", "A base não nula elevada a zero vale 1.")]),
    Example("(2x)⁰", [S("Expressão inicial", "(2x)<sup>0</sup>", "A base 2x precisa ser diferente de zero; logo x ≠ 0."), S("Aplique a propriedade", "(2x)<sup>0</sup> = 1", "Com base não nula, o resultado é 1."), S("Resultado e condição", "1, <span class='condition'>x ≠ 0</span>", "Em x = 0, a expressão seria 0⁰, que não é definida nesta regra.")]),
    Example("(a/b)⁰", [S("Expressão inicial", "(a/b)<sup>0</sup>", "É necessário b ≠ 0 para a fração existir e a ≠ 0 para que a base seja não nula."), S("Aplique a propriedade", "(a/b)<sup>0</sup> = 1", "A base a/b é não nula sob essas condições."), S("Resultado e condições", "1, <span class='condition'>a ≠ 0, b ≠ 0</span>", "As condições garantem que a base original esteja definida e seja não nula.")]),
]),
"negative": Property("Expoente negativo", "a⁻ⁿ = 1 / aⁿ (a ≠ 0)", "O expoente negativo representa o inverso multiplicativo da potência positiva.", [
    Example("2⁻³", [S("Expressão inicial", "2<sup>−3</sup>", "O expoente negativo não significa uma quantidade negativa de fatores."), S("Inverta a potência", "1 / 2<sup>3</sup>", "A potência passa ao denominador como inverso multiplicativo."), S("Desenvolva", "1 / (2 · 2 · 2)", "O expoente positivo 3 indica três fatores iguais a 2."), S("Resultado", "1/8", "2³ = 8.")]),
    Example("5⁻²", [S("Expressão inicial", "5<sup>−2</sup>", "A base 5 é não nula."), S("Inverta a potência", "1 / 5<sup>2</sup>", "Trocamos o expoente negativo por positivo e tomamos o inverso."), S("Resultado", "1/25", "5² = 25.")]),
    Example("x⁻⁴", [S("Expressão inicial", "x<sup>−4</sup>", "A base x precisa ser diferente de zero."), S("Inverta a potência", "1 / x<sup>4</sup>", "O expoente negativo indica o inverso da potência positiva."), S("Resultado e condição", "1 / x<sup>4</sup>, <span class='condition'>x ≠ 0</span>", "A expressão não existe em x = 0.")]),
    Example("(2/3)⁻³", [S("Expressão inicial", "(2/3)<sup>−3</sup>", "A base fracionária é não nula."), S("Inverta a base", "(3/2)<sup>3</sup>", "O expoente negativo inverte a fração."), S("Eleve", "3<sup>3</sup> / 2<sup>3</sup>", "Agora o expoente é positivo e atua sobre numerador e denominador."), S("Resultado", "27/8", "O resultado é 27/8.")]),
]),
"fractional": Property("Expoente fracionário", "a^(m/n) = ⁿ√(aᵐ) (condições reais)", "Em números reais, raízes de índice par exigem radicando não negativo. O significado depende do domínio e da convenção de raiz principal.", [
    Example("16^(1/2)", [S("Expressão inicial", "16<sup>1/2</sup>", "O denominador 2 do expoente indica raiz quadrada."), S("Converta em radical", "√16", "O expoente 1/2 corresponde à raiz quadrada principal."), S("Resultado", "4", "A raiz quadrada principal de 16 é 4.")]),
    Example("27^(1/3)", [S("Expressão inicial", "27<sup>1/3</sup>", "O denominador 3 indica raiz cúbica."), S("Converta em radical", "∛27", "A raiz cúbica é o número que elevado a 3 resulta em 27."), S("Resultado", "3", "3³ = 27.")]),
    Example("8^(2/3)", [S("Expressão inicial", "8<sup>2/3</sup>", "O denominador 3 indica raiz cúbica; o numerador 2 indica quadrado."), S("Converta em radical", "(∛8)<sup>2</sup>", "Primeiro, ∛8 = 2; em seguida elevamos ao quadrado."), S("Calcule", "2<sup>2</sup>", "A raiz cúbica principal de 8 é 2."), S("Resultado", "4", "2² = 4.")]),
    Example("x^(3/2)", [S("Expressão inicial", "x<sup>3/2</sup>", "Para valores reais, a raiz quadrada exige x ≥ 0."), S("Converta em radical", "√(x<sup>3</sup>)", "O denominador 2 indica raiz quadrada; equivalentemente, (√x)³ para x ≥ 0."), S("Resultado e condição", "(√x)<sup>3</sup>, <span class='condition'>x ≥ 0</span>", "A condição garante que a raiz quadrada seja real.")]),
]),
}

# Add two pedagogical checkpoints to shorter prepared proofs. These are real
# stages in the same step model, so the visual panel and narration advance
# together; no formula is calculated separately by the UI.
_EXTRA_STEPS = {
    "mult": (
        S("Visualize os fatores que serão reunidos", "a · a · ⋯ · a", "Cada potência representa uma quantidade de fatores iguais à base. Ao multiplicar potências, os fatores das duas sequências ficam lado a lado."),
        S("Confira a quantidade total", "m + n", "A nova quantidade de fatores é a quantidade do primeiro grupo mais a quantidade do segundo grupo. A base permanece inalterada."),
    ),
    "div": (
        S("Visualize a divisão como fatores", "(a · ⋯ · a) / (a · ⋯ · a)", "O denominador contém fatores iguais aos do numerador. Cada fator do denominador pode cancelar um fator correspondente do numerador, desde que a seja não nulo."),
        S("Confira o que sobra", "m − n", "A quantidade restante é a quantidade inicial do numerador menos os fatores cancelados pelo denominador."),
    ),
    "product": (
        S("Repita o bloco do produto", "(a · b) · (a · b) · ⋯ · (a · b)", "O expoente n informa quantas cópias do bloco inteiro aparecem. Cada cópia contém um fator a e um fator b."),
        S("Separe os fatores pela origem", "(a · ⋯ · a) · (b · ⋯ · b)", "Pela comutatividade e associatividade da multiplicação, podemos agrupar os fatores a entre si e os fatores b entre si."),
    ),
    "quotient": (
        S("Repita a fração como um bloco", "(a/b) · (a/b) · ⋯ · (a/b)", "Cada cópia contém um fator a no numerador e um fator b no denominador. O denominador original precisa ser diferente de zero."),
        S("Agrupe numeradores e denominadores", "(a · ⋯ · a) / (b · ⋯ · b)", "Multiplicamos os numeradores entre si e os denominadores entre si. A quantidade de fatores em cada grupo é n."),
    ),
    "zero": (
        S("Relacione com a divisão de potências", "aᵐ / aᵐ = aᵐ⁻ᵐ", "Como a é não nulo, a potência aᵐ também é não nula. Um número não nulo dividido por ele mesmo vale 1."),
        S("Observe por que surge o zero", "m − m = 0", "A divisão de duas potências idênticas subtrai expoentes iguais. A diferença é zero, o que explica a propriedade."),
    ),
    "negative": (
        S("Interprete o sinal negativo", "a⁻ⁿ = 1 / aⁿ", "O expoente negativo indica o inverso multiplicativo. Ele não representa uma quantidade negativa de fatores."),
        S("Desenvolva a potência positiva", "1 / (a · a · ⋯ · a)", "Depois de inverter, o expoente n positivo indica n fatores iguais a a no denominador."),
    ),
    "fractional": (
        S("Separe numerador e denominador do expoente", "m/n = (1/n) · m", "O denominador n indica o índice da raiz; o numerador m indica a potência aplicada ao resultado da raiz."),
        S("Confira a interpretação como radical", "a^(m/n) = (ⁿ√a)ᵐ", "A raiz principal precisa respeitar o domínio real. Se o índice for par, o radicando deve ser não negativo."),
    ),
}

for _key, _property in list(PROPERTIES.items()):
    if _key == "power":
        continue
    _new_examples = []
    for _example in _property.examples:
        _steps = list(_example.steps)
        if len(_steps) < 6:
            _extra_a, _extra_b = _EXTRA_STEPS[_key]
            _steps.insert(1, _extra_a)
            if len(_steps) < 6:
                _steps.insert(-1, _extra_b)
        _new_examples.append(Example(_example.label, _steps))
    PROPERTIES[_key] = Property(_property.label, _property.rule, _property.note, _new_examples)

PROPERTY_ORDER = list(PROPERTIES.keys())
