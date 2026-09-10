CREATE TABLE IF NOT EXISTS stg_pncp_contratacoes_consulta (
    numero_controle_pncp VARCHAR(100) PRIMARY KEY,

    -- Rastreabilidade da busca
    data_inicial_busca DATE,
    data_final_busca DATE,
    uf_busca CHAR(2),
    modalidade_busca_id INT,

    -- Identificação da contratação
    numero_compra VARCHAR(100),
    ano_compra INT,
    sequencial_compra VARCHAR(50),
    processo VARCHAR(100),

    -- Instrumento convocatório
    tipo_instrumento_convocatorio_codigo INT,
    tipo_instrumento_convocatorio_nome VARCHAR(150),

    -- Modalidade / modo disputa / situação
    modalidade_id INT,
    modalidade_nome VARCHAR(150),

    modo_disputa_id INT,
    modo_disputa_nome VARCHAR(150),

    situacao_compra_id INT,
    situacao_compra_nome VARCHAR(150),

    -- Objeto
    objeto_compra TEXT,
    informacao_complementar TEXT,

    -- SRP e amparo legal
    srp BOOLEAN,

    amparo_legal_codigo INT,
    amparo_legal_nome VARCHAR(255),
    amparo_legal_descricao TEXT,

    -- Valores
    valor_total_estimado DECIMAL(18,4),
    valor_total_homologado DECIMAL(18,4),

    -- Datas
    data_abertura_proposta DATETIME NULL,
    data_encerramento_proposta DATETIME NULL,
    data_publicacao_pncp DATETIME NULL,
    data_inclusao DATETIME NULL,
    data_atualizacao DATETIME NULL,
    data_atualizacao_global DATETIME NULL,

    -- Órgão
    orgao_cnpj VARCHAR(20),
    orgao_razao_social VARCHAR(255),
    orgao_poder_id VARCHAR(10),
    orgao_esfera_id VARCHAR(10),

    -- Unidade
    unidade_codigo VARCHAR(100),
    unidade_nome VARCHAR(255),
    unidade_codigo_ibge VARCHAR(20),
    unidade_municipio_nome VARCHAR(150),
    unidade_uf_sigla CHAR(2),
    unidade_uf_nome VARCHAR(100),

    -- Links e usuário
    usuario_nome VARCHAR(255),
    link_sistema_origem TEXT,
    link_processo_eletronico TEXT,
    justificativa_presencial TEXT,

    -- Campos variáveis/aninhados
    fontes_orcamentarias JSON,
    emenda_parlamentar JSON,
    orgao_subrogado JSON,
    unidade_subrogada JSON,

    -- Controle da carga
    data_carga DATETIME DEFAULT CURRENT_TIMESTAMP
);