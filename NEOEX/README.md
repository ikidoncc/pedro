# NEOEX — EXPONENCIAL LAB

**Versão 1.10** · Laboratório Interativo de Matemática · Desenvolvido por PH - Δ

Esta versão corrige a largura do Canvas quando a aba GRÁFICOS é aberta, ocultada e reaberta. Também melhora a tipografia dos expoentes na substituição numérica do ponto móvel. As seções PROPRIEDADES, ÁLGEBRA e EXERCÍCIOS permanecem preservadas.

## Correções da versão 1.10

- **Canvas responsivo ao alternar abas:** o desenho não fixa mais `canvas.style.width` ou `canvas.style.height` com medidas em pixels. A folha de estilos mantém `width: 100%` e `height: 100%`; JavaScript altera somente a resolução interna do bitmap. Isso evita que o gráfico fique preso a cerca de 300 px quando é inicializado com a aba oculta.
- **Inicialização com a aba escondida:** se o Canvas ainda não tiver dimensões úteis, o desenho aguarda. `ResizeObserver`, `IntersectionObserver`, redimensionamento da janela, visibilidade do documento e seleção de abas solicitam uma nova medição quando o gráfico fica visível. A amostragem da curva é refeita depois que a largura real é conhecida.
- **Limpeza de instâncias antigas:** ao inicializar, o runtime remove dimensões inline deixadas por versões anteriores; ao destruir a instância, desconecta tanto o `ResizeObserver` quanto o `IntersectionObserver` e aborta os listeners.
- **Expoente variável na leitura:** a função continua mostrando `4ˣ` na expressão principal. Na substituição numérica do ponto, os expoentes são montados com elementos HTML `<sup>` criados por DOM, por exemplo `4` elevado a `(4,429)`. Isso mantém expoentes decimais corretamente elevados. O texto é inserido por `textContent`, sem interpolar HTML fornecido pelo usuário.
- **Teste visual de navegação:** o Canvas foi inicializado com o contêiner oculto, exibido, ocultado e exibido novamente três vezes. Em viewport desktop de 1440 px, manteve largura CSS e bitmap de 1368 px, sem largura inline fixa; o gráfico foi desenhado e o ponto móvel atualizou a leitura para `x = 4,429`.

## 1. Base do módulo gráfico (versão 1.9)

O módulo de gráficos foi reconstruído para deixar de depender do Plotly. A curva é desenhada em **Canvas 2D**, no próprio navegador. O Python/SymPy valida a expressão e prepara os dados matemáticos; o JavaScript desenha a curva e trata as interações.

Isso remove do projeto a dependência de uma biblioteca de gráficos grande, reduz o volume transferido ao navegador e evita inicializar uma biblioteca de gráficos pesada dentro de uma aba que ainda está oculta.

### Ferramentas do gráfico

- **Função personalizada:** digite uma função real de `x`, inclusive polinômios de grau elevado, frações, potências com expoente variável e funções elementares.
- **Pré-visualização:** a entrada é mostrada em notação matemática formatada.
- **Ponto móvel:** arraste o ponto verde sobre a curva, use o controle deslizante ou digite diretamente o valor de `x`.
- **Projeções:** linhas pontilhadas mostram as projeções do ponto para os eixos.
- **Leitura dinâmica:** mostra `x`, a expressão com o valor substituído e o resultado com até três casas decimais.
- **Raízes:** os pontos em que `g(x)=0` aparecem no eixo x, identificados como `x1`, `x2`, `x3` etc. A opção pode ser ocultada.
- **Reta horizontal:** mova a reta `y=c` verticalmente arrastando-a, usando o controle deslizante ou digitando o valor de `y`.
- **Interseções:** os pontos de encontro da reta horizontal com a curva são identificados como `A`, `B`, `C` etc. A interface também identifica tangências e o caso de uma função constante coincidente com a reta.
- **Navegação do plano:** arraste uma região vazia para deslocar os eixos; use a roda do mouse para aproximar/afastar; dê duplo clique ou use “Reenquadrar” para voltar à janela inicial.
- **Intervalo configurável:** o intervalo do ponto móvel começa em `[-8, 8]`, mas pode ser ampliado ou reduzido. O enquadramento visível dos eixos pode ser ajustado separadamente.
- **Comparação:** é possível sobrepor até quatro funções adicionais.

### Correções de exibição e atualização na versão 1.9

- A função, o domínio e os cartões de análise do módulo gráfico são apresentados em notação Unicode matemática (por exemplo, `g(x) = 2ˣ + 8x²` e `Dₓ = ℝ`). A área gráfica não depende de MathJax para exibir as fórmulas e, assim, não deixa comandos TeX crus caso o navegador atrase ou bloqueie a biblioteca.
- A pré-visualização da função também usa essa saída legível e mostra o domínio real calculado.
- Um observador global único, restrito a mudanças da saída gráfica, detecta quando o Gradio coloca um novo gráfico ou altera a configuração. A instância antiga é destruída e a nova curva é inicializada; os listeners e o observador de redimensionamento anteriores são descartados.
- Ao editar a função e pressionar Enter ou sair do campo, o gráfico e a análise são recalculados. O botão **GERAR GRÁFICO E ANÁLISE** continua disponível; escolher uma função preparada ou alterar a comparação também atualiza a curva.
- Se a expressão nova for inválida, o gráfico anterior é substituído por uma mensagem de erro, em vez de permanecer na tela como se a alteração tivesse funcionado.

### Desempenho

- A curva é amostrada entre 420 e 1100 pontos, conforme a largura da tela.
- Redesenhos de arraste, pan e zoom são agrupados por `requestAnimationFrame`. Eventos de ponteiro que acontecem no mesmo quadro não disparam várias amostragens redundantes.
- A lista de raízes, pontos críticos, funções numéricas e análises simbólicas usa cache limitado.
- Pontos fora do domínio real ou valores não finitos interrompem a curva em vez de quebrar o JSON ou o desenho inteiro.
- O código do usuário nunca é executado como JavaScript. O parser cria uma árvore matemática segura; o SymPy converte essa árvore para uma expressão JavaScript construída apenas a partir de operações permitidas.
- Não há Plotly, `setInterval` nem uma biblioteca externa de gráficos. O desenho usa o Canvas do navegador.

### Correções de exibição e atualização na versão 1.9

- A função, o domínio e os cartões da análise gráfica são exibidos como texto matemático Unicode (por exemplo, `g(x) = 2ˣ + 8x²`, `Dₓ = ℝ`). Essa área não depende de o MathJax conseguir iniciar dentro do iframe do Colab, portanto não mostra comandos TeX crus.
- A pré-visualização gráfica também usa a mesma saída legível, incluindo o domínio real.
- A saída do gráfico é observada globalmente de forma restrita: ao entrar um novo HTML ou mudar `data-config`, a instância anterior é destruída e o novo Canvas é inicializado. Listeners e `ResizeObserver` anteriores são descartados.
- Alterar a expressão e sair do campo ou pressionar Enter recalcula o gráfico e a análise. O botão **GERAR GRÁFICO E ANÁLISE** continua disponível como ação explícita; escolher uma função preparada e alterar a comparação também redesenha.
- Se a nova expressão for inválida, o gráfico anterior é removido e substituído por um aviso. Assim, uma curva antiga não fica na tela dando a impressão de que a nova função foi aceita.

## 2. Como o exemplo do usuário é interpretado

A expressão

```text
(2^2x + 3x^x)/4x^2
```

é interpretada pela convenção algébrica usada no projeto como

\[
\frac{2^2\cdot x + 3\cdot x^x}{4\cdot x^2}.
\]

Em particular:

- `2^2x` significa `2^2 * x`, isto é, `4x`.
- `3x^x` significa `3 * (x^x)`.
- `a/4x^2` significa `a/(4*x^2)`.

A multiplicação implícita liga-se antes da divisão. Para outra agrupação, use parênteses: `2^(2x)` representa `2` elevado a `2x`.

Como a expressão contém `x^x`, seu domínio real usual é `x > 0`. A parte do gráfico fora desse domínio fica vazia; isso é esperado e não é erro de renderização.

## 3. Sintaxe aceita

O parser aceita:

| Recurso | Exemplos |
|---|---|
| Soma e subtração | `x^3 - 2x + 1` |
| Multiplicação explícita | `3 * 2^x` |
| Multiplicação implícita | `2x`, `3(x+1)`, `x(x-2)` |
| Divisão | `(x^2+1)/(x-1)` |
| Potência | `x^5`, `2^x`, `x^x`, `2^(2x)` |
| Agrupamento | `(x+1)`, `[x+1]`, `{x+1}` |
| Raiz e módulo | `sqrt(x)`, `abs(x)` |
| Funções | `exp(x)`, `log(x)`, `ln(x)`, `sin(x)`, `cos(x)`, `tan(x)` |
| Constantes | `pi`, `e` |

O gráfico usa `x` como única variável independente. A seção ÁLGEBRA pode trabalhar com outras variáveis, como `n`.

Limites defensivos do parser: 320 caracteres, 180 tokens/nós sintáticos e expoente numérico máximo de 1000. Esses limites evitam que uma entrada acidentalmente enorme ou degenerada bloqueie o aplicativo.

## 4. Raízes e interseções: precisão e limites

A curva pode ser desenhada para expressões mais amplas do que aquelas para as quais é possível garantir uma solução simbólica exata. Por isso, a localização de raízes e interseções segue métodos limitados:

- Polinômios de menor grau usam isolamento real de raízes do SymPy.
- Polinômios de grau moderado usam aproximação numérica depois de remover multiplicidades repetidas, o que evita raízes falsas próximas umas das outras.
- Polinômios de grau muito alto e funções gerais usam amostragem no intervalo e refinamento numérico por bisseção.
- Raízes tangenciais são procuradas também nos pontos críticos reconhecidos. Esse tratamento é importante, por exemplo, quando a reta horizontal toca o vértice de uma parábola sem atravessar a curva.
- As interseções são calculadas apenas no intervalo visível/definido e respeitam exclusões do domínio.

**Limitação honesta:** para funções altamente oscilatórias, raízes extremamente próximas ou expressões muito mal condicionadas, uma busca numérica por amostragem pode não detectar todas as raízes. O gráfico ainda pode ser desenhado, mas a lista de pontos não deve ser interpretada como prova simbólica universal. Para polinômios de grau muito alto, a localização é numérica, não uma demonstração exata.

## 5. Estrutura do projeto

```text
NEOEX/
├── app.py                  # inicialização local
├── requirements.txt        # dependências Python
├── run_colab.ipynb         # notebook para Google Colab
├── neoex/
│   ├── parser.py           # parser matemático seguro
│   ├── domain.py           # domínio real
│   ├── graphs.py           # cálculo simbólico/numerico de gráficos
│   ├── graph_runtime.js    # desenho Canvas e interações
│   ├── algebra.py          # transformações algébricas
│   ├── properties.py       # demonstrações de potenciação
│   ├── exercises.py        # exercícios
│   └── ui.py               # interface Gradio
└── tests/
    ├── test_core.py
    └── test_graph_interface.py
```

## 6. Dependências

Somente três dependências Python principais:

- **Gradio 6.x:** interface web e controles.
- **SymPy 1.13+:** parsing já validado, domínio, raízes e álgebra simbólica.
- **NumPy 1.26+:** avaliação numérica e aproximações.

Não é necessário instalar Plotly, Matplotlib, Bokeh ou outra biblioteca de gráficos.

## 7. Executar no Google Colab

1. Abra `NEOEX_Colab_v1.9.ipynb`.
2. Execute a primeira célula e envie `NEOEX_v1.9.zip`.
3. Execute a célula de instalação das dependências.
4. Execute a última célula para iniciar o aplicativo.
5. Abra o link temporário do Gradio apresentado pelo Colab.

Para substituir uma versão que já estava rodando, reinicie a sessão do Colab antes de executar o notebook novo. Isso evita que módulos e processos da versão antiga permaneçam carregados.

O link público do Gradio é temporário e depende de a sessão do Colab permanecer ativa. O Colab é um ambiente online; a sessão e o link não são hospedagem permanente.

## 8. Executar localmente no computador

É possível executar o mesmo projeto localmente, sem Colab e sem link público do Gradio. No Windows, abra o terminal dentro da pasta `NEOEX`:

```powershell
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py
```

Depois abra `http://127.0.0.1:7860` no navegador. `app.py` inicia o servidor local, sem criar link público.

**Conectividade:** depois de instalar os pacotes, o motor Canvas não precisa baixar uma biblioteca de gráficos. O MathJax utilizado nas seções de propriedades, álgebra e exercícios está incluído localmente no projeto e é servido pelo próprio Gradio. A área de gráficos usa notação Unicode e não depende do MathJax. A identidade visual ainda tenta carregar fontes do Google Fonts; sem internet, o navegador utiliza fontes de sistema como alternativa. O projeto pode ser executado localmente, mas ainda não é o aplicativo instalável final para PC/celular.

## 9. Testes realizados nesta versão

A suíte automatizada contém **45 testes aprovados**, incluindo:

- Interpretação de `2^2x`, `3x^x` e da expressão completa do exemplo.
- Funções polinomiais de grau baixo, moderado e elevado.
- Raízes com multiplicidade alta, evitando falsos pontos próximos.
- Cruzamentos e tangências com retas horizontais.
- Funções descontínuas como `1/x`, `sqrt(x)` e `log(x)`.
- Domínios, pontos excluídos e serialização JSON estrita.
- Controles de Canvas, arraste, sliders, campo de `x`, raiz e reta horizontal.
- Estrutura do aplicativo Gradio, atualização da curva nos eventos `change` e `submit`, e ausência de dependência Plotly.
- Renderização do módulo gráfico sem comandos LaTeX crus na função, pré-visualização, domínio, análise e saída textual do ponto.
- Observação global da saída Gradio e reconstrução do Canvas quando a configuração da função muda.

Também foram verificados a sintaxe JavaScript (`node --check`), a compilação Python (`py_compile`), a extração do ZIP e a inicialização local do servidor Gradio por HTTP. O ambiente desta execução bloqueou a navegação automatizada do Chromium para arquivos locais e para `localhost`; portanto, não afirmo ter concluído um teste visual ponta a ponta no navegador nesta rodada. A interação final deve ser confirmada no Colab ou no navegador local do usuário.

## 10. O que ainda não é

- Ainda não é um aplicativo nativo instalável `.exe`, `.apk` ou `.ipa`.
- Não substitui integralmente o GeoGebra: o objetivo desta etapa é estabelecer um núcleo de gráficos 2D eficiente, com ponto móvel, raízes e interseções.
- A busca numérica de raízes e interseções não oferece garantia universal para qualquer expressão possível.
- A análise de imagem, assíntotas e monotonicidade é simbólica quando possível; em casos difíceis, o programa informa que não determinou o resultado automaticamente.

A arquitetura já separa o motor matemático (`graphs.py`) da camada de desenho/interação (`graph_runtime.js`). Isso permite futuramente reaproveitar o motor Canvas e os recursos matemáticos em um aplicativo desktop ou mobile.
