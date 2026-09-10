CREATE TABLE IF NOT EXISTS log_pncp_coleta_itens (
    id_log INT AUTO_INCREMENT PRIMARY KEY,

    numero_controle_pncp VARCHAR(100),
    orgao_cnpj VARCHAR(20),
    ano_compra INT,
    sequencial_compra VARCHAR(50),

    status_coleta VARCHAR(50),
    qtd_itens INT,
    mensagem TEXT,

    data_coleta DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_log_numero_controle (numero_controle_pncp),
    INDEX idx_log_status (status_coleta)
);