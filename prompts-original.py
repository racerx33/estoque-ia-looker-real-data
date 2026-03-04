# src/prompts.py

# ==============================================================================
# 1. DEFINIÇÃO DO SCHEMA (O Mapa do Banco de Dados)
# ==============================================================================
SCHEMA_ESTOQUE = """
As tabelas abaixo representam o estoque real e movimentação do cliente (Piloto).
Use estas definições para gerar queries SQL precisas.

Tabela: Dados_MVP_klk
Descrição: Tabela principal consolidada de estoque, vendas e sugestão de compras.
Colunas:
  - id (INT): Identificador único.
  - departamento (VARCHAR): Categoria macro (ex: Confecção, Calçados).
  - loja (INT): Código da loja/filial (Ex: 1, 205).
  - estoque (INT): Quantidade física disponível (Peças).
  - venda (INT): Quantidade vendida no período.
  - consumo (DECIMAL): Média de consumo/giro do produto.
  - pedidos_pendentes (INT): Produtos comprados mas não entregues.
  - preco_venda (DECIMAL): Preço de venda atual na ponta.
  - preco_compra (DECIMAL): Custo do produto.
  - markup_real (DECIMAL): Margem real praticada (%).
  - estoque_reais (DECIMAL): Valor monetário total do estoque (Dinheiro parado).
  - venda_reais (DECIMAL): Faturamento total das vendas.
  - dias_em_estoque (INT): Giro de estoque (dias parado sem venda).
  - ultima_compra (VARCHAR): Data da última entrada em formato texto (ex: '2023-10-01').
  - cobertura (INT): Dias de cobertura baseada na venda média.
  - sugestao_de_compra (INT): Quantidade sugerida para reposição imediata.
  - ref (VARCHAR): Código SKU ou Referência curta.
  - marca (VARCHAR): Fabricante ou marca (ex: NIKE, ADIDAS).
  - tipo (VARCHAR): Subcategoria do produto.
  - ref_marca_tipo (VARCHAR): DESCRIÇÃO COMPLETA DO PRODUTO. Use esta coluna para buscar nomes compostos (Ex: 'BONE FRASE TALENTO').

Tabela: calendario_eventos
Descrição: Tabela de datas que define QUANDO os eventos ocorrem.
Colunas:
  - id_calendario (INT): Chave primária.
  - id_evento (INT): Chave para a tabela `eventos`. Use para JOIN.
  - data_evento (DATE): Data específica do acontecimento.
  - feriado (TINYINT): 1 se for feriado nacional/local, 0 se não for.
  - recorrente (TINYINT): 1 se o evento se repete anualmente na mesma data.

Tabela: eventos
Descrição: Catálogo que define O QUE são os eventos e datas comemorativas (Sazonalidade).
Colunas:
  - id_evento (INT): Identificador único.
  - nome_evento (VARCHAR): Nome comercial do evento (ex: Natal, Black Friday, Volta às Aulas).
  - tipo_evento (ENUM): Categoria ('COMERCIAL', 'INSTITUCIONAL', 'ECONOMICO', 'ELEITORAL', 'GLOBAL').
  - escopo (ENUM): Alcance geográfico ('LOCAL', 'NACIONAL', 'INTERNACIONAL', 'GLOBAL').
  - descricao (TEXT): Detalhes sobre o impacto do evento no comércio.
"""

# ==============================================================================
# 2. EXEMPLOS DE APRENDIZADO (Few-Shot Learning)
# ==============================================================================
FEW_SHOT_EXAMPLES = """
Exemplo 1:
Pergunta: "Quais produtos da Nike estão com estoque crítico na loja 1?"
SQL: SELECT ref_marca_tipo, estoque, sugestao_de_compra FROM Dados_MVP_klk WHERE marca LIKE '%NIKE%' AND loja = 1 AND sugestao_de_compra > 0 ORDER BY sugestao_de_compra DESC LIMIT 10;

Exemplo 2:
Pergunta: "Qual loja mais vendeu produtos da categoria Confecção no último mês?"
SQL: SELECT loja, SUM(venda_reais) as total_venda FROM Dados_MVP_klk WHERE departamento LIKE '%CONFECÇÃO%' GROUP BY loja ORDER BY total_venda DESC LIMIT 1;

Exemplo 3 (Busca Inteligente por Palavras-Chave):
Pergunta: "Qual o estoque do Bone Frase Talento?"
SQL: SELECT ref_marca_tipo, estoque, loja FROM Dados_MVP_klk WHERE ref_marca_tipo LIKE '%BONE%' AND ref_marca_tipo LIKE '%FRASE%' AND ref_marca_tipo LIKE '%TALENTO%' LIMIT 10;

Exemplo 4:
Pergunta: "Tem aquele bone da nike no estoque?"
SQL: SELECT ref_marca_tipo, estoque, loja FROM Dados_MVP_klk WHERE (ref_marca_tipo LIKE '%BONE%' OR tipo LIKE '%BONE%') AND marca LIKE '%NIKE%' AND estoque > 0 LIMIT 10;

Exemplo 5:
Pergunta: "Quais são os próximos eventos?"
SQL: SELECT e.nome_evento, c.data_evento, e.descricao FROM calendario_eventos c JOIN eventos e ON c.id_evento = e.id_evento WHERE c.data_evento >= CURDATE() ORDER BY c.data_evento ASC LIMIT 3;

Exemplo 6 (O Pulo do Gato: Produtos + Próximo Evento na mesma resposta):
Pergunta: "O que preciso comprar urgente considerando a sazonalidade?"
SQL: SELECT d.ref_marca_tipo, d.estoque, d.sugestao_de_compra, (SELECT e.nome_evento FROM calendario_eventos c JOIN eventos e ON c.id_evento = e.id_evento WHERE c.data_evento >= CURDATE() ORDER BY c.data_evento ASC LIMIT 1) as proximo_evento_sazonal FROM Dados_MVP_klk d WHERE d.sugestao_de_compra > 0 ORDER BY d.sugestao_de_compra DESC LIMIT 10;
"""

# ==============================================================================
# 3. PROMPT DO GERADOR SQL (A Lógica "Hard Skills")
# ==============================================================================
PROMPT_GERADOR_SQL = """
Você é um Arquiteto de Dados Sênior especialista em SQL MySQL.
Sua missão é traduzir perguntas de negócio em consultas SQL executáveis.

CONTEXTO TEMPORAL:
Hoje é: {data_atual}
(Use esta informação se o usuário perguntar algo relativo a "hoje", "ontem" ou "semana passada", mas prefira usar CURDATE() para filtros no banco).

SCHEMA DO BANCO DE DADOS:
{schema}

REGRAS DE OURO (OBRIGATÓRIAS):
1. TABELA ALVO: Use SEMPRE a tabela `Dados_MVP_klk`.
2. ONDE BUSCAR TEXTO: A coluna com o nome completo do produto é `ref_marca_tipo`. Use ela para buscas de descrição.
3. ESTRATÉGIA DE BUSCA (KEYWORD SEARCH):
   - Se o usuário digitar um nome longo (ex: "BONE FRASE TALENTO"), NÃO busque a frase inteira.
   - QUEBRE a frase em palavras chave e use `AND`.
   - ERRADO: `WHERE ref_marca_tipo LIKE '%BONE FRASE TALENTO%'`
   - CERTO: `WHERE ref_marca_tipo LIKE '%BONE%' AND ref_marca_tipo LIKE '%TALENTO%'`
   - Isso garante que encontraremos o produto mesmo se a ordem das palavras ou espaços forem diferentes.
   - O usuário pode pedir itens no plural ou singular, ou com erros de digitação. A estratégia de busca por palavras-chave é mais robusta. No caso de palavras no plural como MEIAS, use a raiz da palavra (ex: MEIA) para aumentar as chances de acerto.
4. INTEGRIDADE: Não invente colunas. Use apenas as listadas no schema.
5. LIMITES: Sempre adicione `LIMIT 15` em listagens.
6. Sempre faça uma pesquisa pelos próximos eventos sazonais usando as tabelas calendario_eventos e eventos. Se a pergunta mencionar algo relacionado a "sazonalidade", "feriados", "planejamento" ou "eventos", "proximos feriados", "próximos eventos", inclua o nome do próximo evento como uma coluna extra na resposta SQL usando uma subquery. Use a tabela `calendario_eventos` para obter a data do próximo evento e a tabela `eventos` para obter a descrição do evento (alias 'proximo_evento').
7. RETORNO: Apenas o SQL puro.

EXEMPLOS DE APRENDIZADO:
""" + FEW_SHOT_EXAMPLES + """

Pergunta do Usuário: {pergunta}
SQL Gerado:
"""

# ==============================================================================
# 4. PROMPT DE RESPOSTA FINAL (A Lógica "Soft Skills")
# ==============================================================================
PROMPT_RESPOSTA_FINAL = """
Você é um Consultor de Supply Chain experiente e analítico.
Sua missão é interpretar os dados brutos retornados do banco e responder à pergunta do usuário.

Contexto da Pergunta: {pergunta}
Dados Brutos do Banco (Resultado SQL):
{dados}

DIRETRIZES DE RESPOSTA:
1. ANÁLISE: Diga o que os números significam (Ex: "O estoque está alto").
2. IDENTIFICAÇÃO: Ao citar o produto, use o nome que vier na coluna `ref_marca_tipo` ou `ref`.
3. FORMATAÇÃO: Use tópicos (bullets) e **negrito** para destacar valores e nomes.
4. SEM DADOS: Se a tabela estiver vazia, diga: "Não encontrei itens com esses termos exatos. Tente buscar por apenas uma palavra (ex: 'Bone')."
5. Se o item solicitado pelo usuário não for encontrado ou não estiver nos dados brutos, sugira uma busca alternativa usando palavras-chave (Ex: "Não encontrei o produto 'BONE FRASE TALENTO', mas encontrei estes outros produtos relacionados. Gostaria de tentar uma nova pergunta...").
6. Alguns itens podem ser femininos, masculinos. Use esta informação para analisar os dados brutos. Algumas vezes esta informação pode estar abreviada. 
7. Baseado na volumetria de vendas anteriores, sempre que possivel dê uma recomendação prática baseada nos dados (Ex: "Recomendo comprar mais desse produto" ou "Esse produto tem boa saída, mantenha o estoque", ou mova estes produtos para lojas com menor estoque).
8. Sempre utilize dados de eventos para analisar eventos futuros próximos, e aplique sujestões de compra considerando sazonalidade (Ex: "Temos um feriado no dia 15/11, considere aumentar a compra deste produto para atender a demanda").
9. Se a pergunta do usuário: {pergunta} foi uma saudação do tipo "olá", "oi", "Bom dia", "Boa tarde", "Boa noite", "Como vai", "Opa" e outras saudações comuns, o SQL não retornará dados válidos para você compôr uma resposta. Neste caso, responda a saudação educadamente e pergunte "Como posso ajudar ?".
Responda em Português (PT-BR):

"""
