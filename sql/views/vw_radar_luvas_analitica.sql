CREATE OR REPLACE VIEW vw_radar_luvas_analitica AS
SELECT
    *,

    CASE
    WHEN LOWER(descricao_item) LIKE '%procedimento%'
		THEN 'Luva procedimento não cirúrgico'

    WHEN (
            LOWER(descricao_item) LIKE '%cirúrg%'
         OR LOWER(descricao_item) LIKE '%cirurg%'
         )
         AND LOWER(descricao_item) NOT LIKE '%não cirúrg%'
         AND LOWER(descricao_item) NOT LIKE '%nao cirurg%'
         AND LOWER(descricao_item) NOT LIKE '%não cirurg%'
         AND LOWER(descricao_item) NOT LIKE '%nao cirúrg%'
      THEN 'Luva cirúrgica'

    WHEN LOWER(descricao_item) LIKE '%nitril%'
      THEN 'Luva nitrílica'

    WHEN LOWER(descricao_item) LIKE '%raspa%'
      THEN 'Luva de raspa'

    WHEN LOWER(descricao_item) LIKE '%soldador%'
      THEN 'Luva para soldador'

    WHEN LOWER(descricao_item) LIKE '%térmica%'
      OR LOWER(descricao_item) LIKE '%termica%'
      THEN 'Luva térmica'

    WHEN LOWER(descricao_item) LIKE '%látex%'
      OR LOWER(descricao_item) LIKE '%latex%'
      THEN 'Luva de látex'

    WHEN LOWER(descricao_item) LIKE '%segurança%'
    OR LOWER(descricao_item) LIKE '%seguranca%'
      OR LOWER(descricao_item) LIKE '%proteção%'
      OR LOWER(descricao_item) LIKE '%protecao%'
      THEN 'Luva de proteção'

    ELSE 'Luva - outros'
END AS tipo_luva,

    CASE
        WHEN orcamento_sigiloso = 1 THEN 'Orçamento sigiloso'
        WHEN valor_total IS NULL OR valor_total = 0 THEN 'Sem valor estimado'
        WHEN valor_unitario_estimado IS NULL OR valor_unitario_estimado = 0 THEN 'Sem valor unitário'
        WHEN valor_unitario_estimado > 50 THEN 'Preço unitário acima do padrão'
        ELSE 'Preço aparentemente válido'
    END AS qualidade_preco,

    CASE
    WHEN UPPER(TRIM(unidade_medida)) IN ('UNIDADE', 'UN', 'UND', 'UNID')
      THEN 'Unidade'

    WHEN UPPER(TRIM(unidade_medida)) IN ('PAR', 'PARES')
      THEN 'Par'

    WHEN UPPER(TRIM(unidade_medida)) IN ('CAIXA', 'CX')
         AND (
              LOWER(descricao_item) LIKE '%caixa com 100%'
           OR LOWER(descricao_item) LIKE '%100 unidades%'
           OR LOWER(descricao_item) LIKE '%100 unidade%'
         )
      THEN 'Caixa 100 UN'

    WHEN UPPER(TRIM(unidade_medida)) IN ('CAIXA', 'CX')
      THEN 'Caixa - qtd não identificada'

    WHEN UPPER(TRIM(unidade_medida)) LIKE '%100%'
      THEN 'Caixa 100 UN'

    WHEN UPPER(TRIM(unidade_medida)) IN ('PC', 'PÇ', 'PEÇA', 'PECA')
      THEN 'Peça'

    ELSE TRIM(unidade_medida)
    END AS unidade_medida_padronizada

FROM vw_radar_luvas;