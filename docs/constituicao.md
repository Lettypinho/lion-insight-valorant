# Constituição do Projeto

## 1. Objetivo

Estabelecer os princípios obrigatórios que orientam decisões de produto, análise, desenvolvimento e apresentação do Lion Insight.

Estas regras têm prioridade sobre sugestões de implementação que aumentem o escopo ou comprometam a confiabilidade dos dados.

## 2. Princípios

### 2.1 Dados reais como fonte de verdade

Toda análise deve ser derivada exclusivamente dos arquivos fornecidos pelo Hackathon.

Não utilizar APIs externas, scraping ou bases de partidas externas para enriquecer métricas de desempenho.

### 2.2 Pós-partida

A solução é destinada a análise pós-partida.

Nenhuma funcionalidade deve oferecer vantagem competitiva em tempo real durante uma partida.

### 2.3 Métricas reproduzíveis

Toda métrica apresentada deve possuir:

- definição clara;
- regra de cálculo;
- numerador, quando aplicável;
- denominador, quando aplicável;
- tamanho da amostra;
- referência aos rounds ou partidas utilizados.

### 2.4 Insights explicáveis

Nenhum diagnóstico pode ser uma afirmação sem evidência.

Todo insight deve estar ligado a uma ou mais métricas e, quando possível, permitir que o usuário consulte os rounds que sustentam a conclusão.

### 2.5 Benchmark contextual

Comparações com a competição devem utilizar situações comparáveis.

Quando aplicável, considerar contexto como:

- competição;
- classificatória;
- mapa;
- lado;
- situação tática.

### 2.6 Não inventar informação

Se um dado não estiver disponível ou não puder ser calculado com confiabilidade, o sistema deve informar a limitação em vez de estimar ou inventar.

### 2.7 MVP antes de expansão

O objetivo do Hackathon é provar valor com poucas análises bem executadas.

Funcionalidades futuras não devem atrasar o caminho crítico do MVP.

### 2.8 Simplicidade técnica

Priorizar uma solução simples, legível e demonstrável.

Evitar:

- arquitetura distribuída;
- autenticação;
- banco de dados complexo;
- múltiplos serviços;
- dependências sem necessidade;
- microserviços;
- uso de LLM para tarefas que podem ser resolvidas por regras determinísticas.

### 2.9 Português na documentação

Toda documentação e definições funcionais devem ser escritas em português.

Termos consagrados do VALORANT e nomes técnicos podem permanecer em inglês quando isso melhorar a clareza.

## 3. Critério de decisão

Quando houver dúvida entre duas implementações, escolher a opção que:

1. usa melhor os dados fornecidos;
2. é mais fácil de validar;
3. é mais fácil de demonstrar;
4. reduz risco de erro;
5. aproxima o projeto do MVP funcional.
