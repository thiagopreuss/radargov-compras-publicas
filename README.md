# RadarGov — Compras Públicas RJ

## Sobre o projeto

O RadarGov é um MVP de análise de compras públicas a partir de dados do [Portal Nacional de Contratações Públicas](https://www.gov.br/pncp/pt-br).

Como estudo de caso inicial, foi selecionado o mercado de luvas para entender como dados públicos de contratações podem ser transformados em informações para análise de demanda e mercado.

## Objetivo

Construir um pipeline de dados capaz de:

- coletar contratações públicas;
- consultar os itens associados às contratações;
- armazenar os dados em banco de dados;
- tratar e organizar os dados com SQL;
- disponibilizar os dados para análise no Power BI.

## Recorte do estudo

- Estado: Rio de Janeiro
- Período: janeiro a março de 2026
- Modalidades: Pregão Eletrônico e Dispensa
- Categoria analisada: luvas

## Resultados da amostra

- 45 contratações encontradas
- 222 itens de luvas identificados
- 25 órgãos compradores
- 14 municípios compradores
- R$ 18,89 milhões em valor total estimado
- Aproximadamente 13 milhões em demanda informada

> Os valores apresentados representam valores estimados das contratações, e não necessariamente valores efetivamente gastos.

## Pipeline

PNCP → Python → MySQL → SQL/Views → Power BI

### 1. Coleta de contratações

O primeiro processo (`coletar_contratacoes_consulta_v2.py`)consulta o PNCP e coleta as contratações correspondentes ao recorte definido.

### 2. Coleta de itens

A partir das contratações selecionadas, o segundo processo (`coletar_itens_pncp_v2.py`) consulta os itens associados e armazena os dados para posterior tratamento e filtragem da categoria analisada.

### 3. Banco de dados

Os dados são armazenados em tabelas de staging no MySQL.

A tabela `stg_pncp_contratacoes_consulta` recebe as contratações coletadas pelo script Python `coletar_contratacoes_consulta_v2.py`.

A tabela `stg_pncp_itens recebe os itens` das contratações selecionadas pelo script Python `coletar_itens_pncp_v2.py`.

A tabela `log_pncp_coleta_itens` registra o resultado do processamento de cada contratação, incluindo status da coleta, quantidade de itens e mensagem de retorno. Esse log também é utilizado para evitar o reprocessamento de contratações que já foram coletadas.

### 4. Configuração da conexão

Os scripts Python utilizam um arquivo .env para armazenar as informações de conexão com o MySQL, evitando deixar credenciais diretamente no código.

As variáveis utilizadas são:

MYSQL_HOST=seu_host
MYSQL_USER=seu_usuario
MYSQL_PASSWORD=sua_senha
MYSQL_DATABASE=sua_base

O arquivo .env utilizado durante a execução local não deve ser versionado no repositório. O arquivo disponibilizado no projeto serve apenas como exemplo da estrutura necessária para a configuração.

### 5. Tratamento e modelagem

Views SQL consolidam os dados de contratação e itens e aplicam as regras necessárias para a análise.

### 6. Power BI

Os dados tratados são utilizados para construção dos dashboards, permitindo analisar demanda, valores estimados, municípios, órgãos compradores e tipos de luvas.

## Estrutura do projeto

```text
radargov-compras-publicas/
├── README.md
├── python/
│   ├── coletar_contratacoes_consulta_v2.py
│   ├── coletar_itens_pncp_v2.py
│   └── .env
├── sql/
│   ├── tabelas/
│   │   ├── stg_pncp_contratacoes_consulta.sql
│   │   ├── stg_pncp_itens.sql
│   │   └── log_pncp_coleta_itens.sql
│   └── views/
│       ├── vw_itens_contratacoes.sql
│       ├── vw_radar_luvas.sql
│       └── vw_radar_luvas_analitica.sql
└── powerbi/
    └── imagens/
```

## Tecnologias

- Python
- MySQL
- SQL
- Power BI
- API do PNCP

## Dashboard

### Visão Geral do Mercado



### Detalhamento do Valor Estimado

<!-- inserir imagem aqui -->

### Itens Detalhados

<!-- inserir imagem aqui -->

## Próximos passos

O projeto foi desenvolvido como MVP. Futuras versões podem ampliar o período analisado, incluir novas categorias de produtos e permitir análises mais abrangentes das compras públicas.
