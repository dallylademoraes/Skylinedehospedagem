# Skyline de Hotéis com Divisão e Conquista

Este projeto demonstra uma consulta **Skyline** para escolha de hotéis usando
**Divisão e Conquista (D&C)** como ideia central.

O objetivo é encontrar os hotéis que fazem parte da fronteira ótima considerando
duas dimensões:

- menor preço;
- menor distância.

Um hotel entra no skyline quando nenhum outro hotel é melhor ou igual ao mesmo
tempo em preço e distância, sendo estritamente melhor em pelo menos uma dessas
dimensões.

## Centro do projeto: `DeC.py`

O arquivo principal do conceito é o [`DeC.py`](./DeC.py).

Ele contém a base teórica e algorítmica do projeto:

- a função `domina(oi, oj)`, que verifica se um objeto domina outro;
- a função `relacao_dominancia(oi, oj)`, que identifica quem domina quem;
- a classe `SkylineDivideConquista`, que calcula o skyline usando Divisão e
  Conquista;
- a estrutura do framework DAR, que parte do D&C Skyline e adiciona redução de
  análises de dominância.

Ou seja: **o centro da explicação é o `DeC.py`**. Ele é a referência para a regra
matemática de dominância e para o funcionamento do algoritmo.

## Como a Divisão e Conquista funciona

O algoritmo segue três fases:

1. **Divisão**

   O conjunto de hotéis é dividido recursivamente em partes menores.

2. **Conquista**

   Cada subconjunto calcula seu skyline local. Quando existe apenas um hotel no
   subconjunto, ele entra diretamente no skyline local, pois não há outro hotel
   para compará-lo.

3. **Combinação**

   Os skylines locais são fundidos. Nessa etapa, o algoritmo compara os hotéis
   das partes e remove os dominados.

Um hotel domina outro quando:

```text
preço_a <= preço_b
distância_a <= distância_b
e pelo menos uma das duas dimensões é estritamente melhor
```

Exemplo:

```text
Hotel A: R$ 200, 8 km
Hotel B: R$ 250, 12 km
```

O Hotel A domina o Hotel B, porque é mais barato e também fica mais perto.
Portanto, o Hotel B não precisa ser escolhido.

## Papel do `app_skyline.html`

O arquivo [`app_skyline.html`](./app_skyline.html) é o painel visual do projeto.

Ele mostra:

- o gráfico preço × distância;
- a animação dos passos de Divisão e Conquista;
- a árvore de recursão;
- a lista do skyline atual;
- os hotéis clicáveis com imagem, preço, distância e motivo da decisão.

Importante: o HTML não importa diretamente o Python. Como é um arquivo estático,
ele possui uma versão em JavaScript da mesma regra de dominância usada em
`DeC.py`.

Então a relação correta é:

```text
DeC.py = centro conceitual e algorítmico
app_skyline.html = visualização interativa da mesma lógica
```

## Por que um hotel é escolhido

Um hotel é escolhido quando ele fica na fronteira skyline.

Isso significa que ele representa um tipo de preferência real:

- pode ser muito barato, mesmo ficando longe;
- pode ser muito perto, mesmo sendo caro;
- pode ter um equilíbrio entre preço e distância.

Ele só sai da escolha quando existe outro hotel melhor ou igual nas duas
dimensões.

## Por que um hotel é eliminado

Um hotel é eliminado quando outro hotel o domina.

Isso quer dizer que existe uma alternativa que:

- custa menos ou igual;
- fica mais perto ou igual;
- é ainda melhor em pelo menos uma das duas dimensões.

Nesse caso, escolher o hotel dominado não faz sentido dentro da regra do
skyline.

## Como abrir o painel

Basta abrir o arquivo:

```text
app_skyline.html
```

no navegador.

As imagens dos hotéis ficam na pasta:

```text
hoteis/
```

O painel tenta carregar automaticamente arquivos como:

```text
hoteis/hotel1.jpg
hoteis/hotel2.jpg
hoteis/hotel3.jpg
...
```

## Resumo

Este projeto deve ser entendido assim:

- **`DeC.py` é o centro do trabalho**;
- o algoritmo principal é Skyline por Divisão e Conquista;
- a regra de decisão é dominância de Pareto;
- o `app_skyline.html` serve para visualizar, explicar e apresentar o que o
  algoritmo faz.
