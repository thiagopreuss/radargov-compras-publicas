CREATE OR REPLACE VIEW vw_itens_contratacoes AS
SELECT 
    i.id_item_composto,
    i.numero_controle_pncp,
    i.numero_item,
    i.descricao AS descricao_item,
    i.material_ou_servico_nome,
    i.quantidade,
    i.unidade_medida,
    i.valor_unitario_estimado,
    i.valor_total,
    i.orcamento_sigiloso,
    c.orgao_cnpj,
    c.orgao_razao_social,
    c.unidade_nome,
    c.unidade_municipio_nome,
    c.unidade_uf_sigla,
    c.modalidade_nome,
    c.situacao_compra_nome,
    c.objeto_compra,
    c.data_publicacao_pncp,
    c.data_abertura_proposta,
    c.data_encerramento_proposta,
    c.link_sistema_origem
FROM stg_pncp_itens i
JOIN stg_pncp_contratacoes_consulta c 
    ON i.numero_controle_pncp = c.numero_controle_pncp;