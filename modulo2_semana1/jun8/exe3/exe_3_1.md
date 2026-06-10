# Exercício — Análise de Feedbacks com OpenAI, Workflow e Agente

# Para rodar os exemplos
cd modulo2_semana1/jun8/exe3
`python ou python3 workflow_feedbacks.py`
`python ou python3 agent_feedback.py`

## Objetivo da aula

Neste exercício, vamos usar a OpenAI para analisar feedbacks de usuários.

A ideia é simular uma situação comum em empresas: vários usuários enviam comentários sobre um produto, aplicativo ou serviço, e alguém precisa transformar esses textos em informações úteis para o negócio.

Ao final, o sistema deve:

1. Ler feedbacks de uma tabela.
2. Analisar cada feedback com apoio de um modelo de linguagem.
3. Classificar o feedback.
4. Identificar o sentimento do usuário.
5. Gerar um resumo curto.
6. Consolidar os resultados.
7. Gerar um relatório para liderança, produto ou suporte.
8. Opcionalmente, decidir qual time deve tratar cada feedback.

---

# Parte 1 — O problema de negócio

A empresa tem uma tabela chamada `feedbacks`.

Exemplo:

| id | feedback |
|---:|----------|
| 1 | O app trava quando tento abrir a tela de pagamento |
| 2 | Gostei muito da nova interface |
| 3 | O sistema está muito lento |
| 4 | Não consegui finalizar minha compra |
| 5 | Atendimento excelente |

A empresa quer transformar esses textos em dados estruturados.

Por exemplo, este feedback:

```text
O app trava quando tento abrir a tela de pagamento
```

Pode virar:

```json
{
  "feedback_id": 1,
  "categoria": "bug",
  "sentimento": "negativo",
  "resumo": "Usuário relatou falha ao acessar a tela de pagamento."
}
```

---

# Parte 2 — Categorias sugeridas

Para simplificar o exercício, vamos usar categorias fixas:

- `bug`
- `elogio`
- `pagamento`
- `performance`
- `atendimento`
- `outros`

Também vamos usar sentimentos fixos:

- `positivo`
- `negativo`
- `neutro`

---

# Parte 3 — Resultado esperado por feedback

Para cada feedback, esperamos um resultado parecido com este:

```json
{
  "feedback_id": 1,
  "categoria": "bug",
  "sentimento": "negativo",
  "resumo": "Usuário relatou falha ao acessar a tela de pagamento."
}
```

Esse formato é importante porque transforma texto livre em dados que podem ser contados, filtrados e analisados.

---

# Parte 4 — Relatório consolidado

Depois de analisar todos os feedbacks, o sistema deve gerar um resumo geral.

Exemplo:

```json
{
  "total_feedbacks": 5,
  "categorias": {
    "bug": 1,
    "elogio": 2,
    "pagamento": 1,
    "performance": 1
  },
  "sentimentos": {
    "positivo": 2,
    "negativo": 3,
    "neutro": 0
  },
  "principais_pontos": [
    "Usuários relataram problemas técnicos no app.",
    "Houve elogios à nova interface e ao atendimento.",
    "Questões de pagamento e lentidão apareceram com frequência."
  ]
}
```

Também podemos gerar um relatório em texto, como se fosse enviado para uma liderança:

```text
Foram analisados 5 feedbacks de usuários. A maior parte dos comentários negativos está relacionada a problemas técnicos, lentidão e dificuldades no pagamento. Também houve feedbacks positivos sobre a interface e o atendimento. Recomenda-se priorizar a investigação dos problemas de pagamento e performance.
```

---

# Parte 5 — Antes de falar de agente: o que é um workflow?

Um workflow é um fluxo com passos definidos.

Neste exercício, o caminho é claro:

```text
Ler feedbacks
     ↓
Analisar cada feedback
     ↓
Salvar resultados
     ↓
Gerar relatório
```

Ou seja, o programador já sabe exatamente o que deve acontecer.

Em código, isso pode ser algo assim:

```python
feedbacks = ler_feedbacks()

resultados = []

for feedback in feedbacks:
    resultado = analisar_feedback(feedback)
    resultados.append(resultado)

salvar_resultados(resultados)

relatorio = gerar_relatorio(resultados)
```

Nesse caso, quem controla o processo é o código.

A IA apenas ajuda em uma etapa: analisar o texto.

Por isso, tecnicamente, esse exercício não precisa obrigatoriamente de um agente.

Ele pode ser resolvido com um workflow simples.

---

# Parte 6 — Então por que falar de agente?

Porque o exercício pode evoluir.

No começo, a IA apenas analisa o texto.

Mas podemos adicionar uma nova responsabilidade:

> Com base no feedback, decidir qual time da empresa deve atender aquele caso.

Agora o sistema não está apenas classificando. Ele está tomando uma decisão operacional.

Exemplo:

| Feedback | Categoria | Time responsável |
|----------|-----------|------------------|
| O app trava quando tento abrir a tela de pagamento | bug | Engenharia |
| O sistema está muito lento | performance | Engenharia |
| Não consegui finalizar minha compra | pagamento | Pagamentos |
| Atendimento excelente | elogio | Atendimento |
| Gostei muito da nova interface | elogio | Produto |

Agora a pergunta muda.

Antes era:

> Qual é a categoria desse feedback?

Agora é:

> Quem deve resolver esse feedback?

Essa decisão torna o exercício mais próximo de um agente.

---

# Parte 7 — Workflow vs Agente

## Workflow

No workflow, o código decide tudo.

```text
Código decide:
1. Ler feedbacks
2. Analisar
3. Salvar
4. Gerar relatório
```

A IA apenas executa uma tarefa específica.

Exemplo:

```text
Classifique este feedback.
```

## Agente

No agente, damos uma missão para a IA e ferramentas que ela pode usar.

```text
Agente, sua missão é analisar os feedbacks da empresa.
Você pode usar estas ferramentas:

- ler_feedbacks
- analisar_feedback
- salvar_resultados
- gerar_relatorio
- definir_time_responsavel
- criar_chamado
```

O agente usa as ferramentas para completar a tarefa.

A diferença principal é:

```text
Workflow:
o código controla o passo a passo.

Agente:
a IA coordena ou escolhe ações usando ferramentas.
```

---

# Parte 8 — Analogia simples

Imagine que você tem uma receita de bolo.

## Workflow

```text
1. Misture os ovos.
2. Adicione farinha.
3. Coloque no forno.
4. Espere 40 minutos.
```

Tudo já está definido.

Não precisa de agente.

## Agente

Agora imagine um atendente recebendo mensagens diferentes:

```text
- Quero cancelar minha compra.
- Meu app travou.
- Gostei do atendimento.
- Meu pagamento não passou.
- Meu pedido atrasou.
```

Nesse caso, o sistema precisa entender a situação e decidir o próximo passo.

Isso parece mais com um agente.

---

# Parte 9 — Como transformar o exercício em agente

Para transformar este exercício em agente, podemos adicionar ferramentas.

## Ferramenta 1 — ler_feedbacks

Responsável por buscar os feedbacks no banco.

```python
def ler_feedbacks():
    # busca feedbacks no banco
    return feedbacks
```

## Ferramenta 2 — analisar_feedback

Responsável por classificar categoria, sentimento e resumo.

```python
def analisar_feedback(feedback):
    # usa OpenAI para analisar texto
    return {
        "feedback_id": feedback["id"],
        "categoria": "bug",
        "sentimento": "negativo",
        "resumo": "Usuário relatou falha no app."
    }
```

## Ferramenta 3 — definir_time_responsavel

Responsável por decidir qual time deve tratar o feedback.

```python
def definir_time_responsavel(categoria, resumo):
    if categoria in ["bug", "performance"]:
        return "Engenharia"
    elif categoria == "pagamento":
        return "Pagamentos"
    elif categoria == "atendimento":
        return "Atendimento"
    elif categoria == "elogio":
        return "Produto"
    else:
        return "Suporte"
```

## Ferramenta 4 — salvar_resultados

Responsável por salvar os dados estruturados.

```python
def salvar_resultados(resultados):
    # salva em arquivo ou banco
    return "Resultados salvos com sucesso."
```

## Ferramenta 5 — gerar_relatorio

Responsável por consolidar números e gerar texto executivo.

```python
def gerar_relatorio(resultados):
    # conta categorias, sentimentos e times
    return relatorio
```

---

# Parte 10 — Saída esperada com time responsável

Agora cada feedback pode gerar uma saída assim:

```json
{
  "feedback_id": 1,
  "categoria": "bug",
  "sentimento": "negativo",
  "time_responsavel": "Engenharia",
  "resumo": "Usuário relatou falha ao acessar a tela de pagamento."
}
```

E o relatório final pode incluir também os times:

```json
{
  "total_feedbacks": 5,
  "categorias": {
    "bug": 1,
    "elogio": 2,
    "pagamento": 1,
    "performance": 1
  },
  "sentimentos": {
    "positivo": 2,
    "negativo": 3,
    "neutro": 0
  },
  "times_responsaveis": {
    "Engenharia": 2,
    "Produto": 1,
    "Pagamentos": 1,
    "Atendimento": 1
  },
  "principais_pontos": [
    "Engenharia deve investigar problemas de travamento e lentidão.",
    "Pagamentos deve analisar falhas no processo de compra.",
    "Produto recebeu feedback positivo sobre a interface.",
    "Atendimento recebeu avaliação positiva."
  ]
}
```

---

# Parte 11 — Discussão para a turma

Depois do exercício, responda:

## 1. Esse problema precisava ser um agente?

Resposta possível:

```text
Não necessariamente.
A primeira versão poderia ser resolvida com um workflow simples.
```

## 2. Quando começa a fazer sentido falar em agente?

Resposta possível:

```text
Quando o sistema precisa decidir qual ação tomar, qual ferramenta usar ou qual time acionar.
```

## 3. Qual é a diferença entre classificar e agir?

Classificar:

```text
Este feedback é sobre pagamento.
```

Agir:

```text
Este feedback deve ser encaminhado para o time de Pagamentos.
```

A segunda resposta já envolve uma decisão operacional.

---

# Parte 12 — Mensagem principal da aula

A principal lição não é apenas usar OpenAI.

A principal lição é entender quando usar cada abordagem.

```text
Se o passo a passo é fixo:
use workflow.

Se o sistema precisa decidir o próximo passo:
considere um agente.
```

Ou seja:

```text
Nem todo problema precisa de agente.
Agente não substitui arquitetura.
Prompt não substitui processo.
```

---

# Parte 13 — Desafio extra

Modifique o exercício para que o sistema também indique prioridade.

Sugestão de prioridade:

| Situação | Prioridade |
|----------|------------|
| App trava, compra falha ou pagamento não funciona | Alta |
| Sistema lento | Média |
| Elogio | Baixa |
| Comentário genérico | Baixa |

Exemplo de saída:

```json
{
  "feedback_id": 1,
  "categoria": "bug",
  "sentimento": "negativo",
  "time_responsavel": "Engenharia",
  "prioridade": "Alta",
  "resumo": "Usuário relatou falha ao acessar a tela de pagamento."
}
```

Pergunta final:

> Agora que o sistema decide categoria, sentimento, time e prioridade, ele parece mais com um workflow ou com um agente?

A resposta pode ser discutida.

O importante é perceber que quanto mais decisões variáveis entram no processo, mais o conceito de agente começa a fazer sentido.

---

# Conclusão

Este exercício começa simples:

```text
Ler feedbacks → Analisar → Gerar relatório
```

Depois evolui para:

```text
Ler feedbacks → Analisar → Decidir time responsável → Gerar relatório → Sugerir ações
```

A primeira versão é um workflow com LLM.

A segunda versão começa a se aproximar de um agente, porque envolve decisão e uso de ferramentas.

O objetivo da aula é mostrar que IA aplicada não é apenas chamar um modelo.

É desenhar um processo inteligente, controlável e útil para o negócio.