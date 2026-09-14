CREATE OR REPLACE VIEW vw_radar_luvas AS
SELECT 
    id_item_composto,
    numero_controle_pncp,
    numero_item,
    descricao_item,
    material_ou_servico_nome,
    quantidade,
    unidade_medida,
    valor_unitario_estimado,
    valor_total,
    orcamento_sigiloso,
    orgao_cnpj,
    orgao_razao_social,
    unidade_nome,
    unidade_municipio_nome,
    unidade_uf_sigla,
    modalidade_nome,
    situacao_compra_nome,
    objeto_compra,
    data_publicacao_pncp,
    data_abertura_proposta,
    data_encerramento_proposta,
    link_sistema_origem,
    'Luvas' AS categoria_produto
FROM vw_itens_contratacoes
WHERE material_ou_servico_nome = 'Material'
  AND descricao_item LIKE '%luva%';