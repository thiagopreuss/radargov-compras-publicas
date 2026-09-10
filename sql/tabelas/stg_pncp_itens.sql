CREATE TABLE IF NOT EXISTS stg_pncp_itens (
    id_item_composto VARCHAR(150) PRIMARY KEY,

    numero_controle_pncp VARCHAR(100),
    orgao_cnpj VARCHAR(20),
    ano_compra INT,
    sequencial_compra VARCHAR(50),

    numero_item INT,
    descricao TEXT,

    material_ou_servico VARCHAR(20),
    material_ou_servico_nome VARCHAR(100),

    valor_unitario_estimado DECIMAL(20,4),
    valor_total DECIMAL(20,4),
    quantidade DECIMAL(20,4),
    unidade_medida VARCHAR(100),

    orcamento_sigiloso BOOLEAN,

    item_categoria_id INT,
    item_categoria_nome VARCHAR(150),

    patrimonio VARCHAR(255),
    codigo_registro_imobiliario VARCHAR(255),

    criterio_julgamento_id INT,
    criterio_julgamento_nome VARCHAR(150),

    situacao_compra_item INT,
    situacao_compra_item_nome VARCHAR(150),

    tipo_beneficio INT,
    tipo_beneficio_nome VARCHAR(150),

    incentivo_produtivo_basico BOOLEAN,

    data_inclusao DATETIME NULL,
    data_atualizacao DATETIME NULL,

    tem_resultado BOOLEAN,
    imagem INT,

    aplicabilidade_margem_preferencia_normal BOOLEAN,
    aplicabilidade_margem_preferencia_adicional BOOLEAN,

    percentual_margem_preferencia_normal DECIMAL(10,4),
    percentual_margem_preferencia_adicional DECIMAL(10,4),

    ncm_nbs_codigo VARCHAR(100),
    ncm_nbs_descricao TEXT,

    catalogo JSON,
    categoria_item_catalogo JSON,
    catalogo_codigo_item VARCHAR(100),

    informacao_complementar TEXT,
    tipo_margem_preferencia VARCHAR(100),
    exigencia_conteudo_nacional BOOLEAN,

    data_carga DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_itens_numero_controle (numero_controle_pncp),
    INDEX idx_itens_descricao (descricao(255)),
    INDEX idx_itens_orgao (orgao_cnpj),
    INDEX idx_itens_ano_seq (ano_compra, sequencial_compra)
);