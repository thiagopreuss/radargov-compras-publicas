import os
import json
import time
from datetime import datetime
from typing import Any, Optional

import mysql.connector
from dotenv import load_dotenv
from curl_cffi import requests


load_dotenv()


BASE_URL = "https://pncp.gov.br/api/pncp/v1"

LIMITE_CONTRATACOES = 300
TAMANHO_PAGINA = 50


def get_mysql_connection():
    """Cria conexão com o MySQL usando as informações do arquivo .env."""
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
    )


def parse_datetime(value: Optional[str]) -> Optional[str]:
    """Converte data/hora da API para formato DATETIME do MySQL."""
    if not value:
        return None

    try:
        dt = datetime.fromisoformat(value.replace("Z", ""))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def to_json_or_none(value: Any) -> Optional[str]:
    """Converte dict/list em JSON para salvar no MySQL."""
    if value is None:
        return None

    return json.dumps(value, ensure_ascii=False)


def buscar_contratacoes_para_teste() -> list[dict]:
    """
    Busca uma amostra de contratações na tabela de contratações.

    Nesta versão, ela ignora contratações que já aparecem no log de coleta de itens.
    Ou seja: evita reprocessar contratações já coletadas anteriormente.
    """
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)

    sql = """
        SELECT
            c.numero_controle_pncp,
            c.orgao_cnpj,
            c.ano_compra,
            c.sequencial_compra,
            c.modalidade_nome,
            c.objeto_compra
        FROM stg_pncp_contratacoes_consulta c
        LEFT JOIN log_pncp_coleta_itens l
            ON c.numero_controle_pncp = l.numero_controle_pncp
        WHERE l.numero_controle_pncp IS NULL
            AND (
                 LOWER(c.objeto_compra) LIKE '%luva%'
                OR LOWER(c.objeto_compra) LIKE '%epi%'
                OR LOWER(c.objeto_compra) LIKE '%uniforme%'
                OR LOWER(c.objeto_compra) LIKE '%fardamento%'
                OR LOWER(c.objeto_compra) LIKE '%equipamento de proteção%'
                OR LOWER(c.objeto_compra) LIKE '%equipamento de protecao%'
                OR LOWER(c.objeto_compra) LIKE '%proteção individual%'
                OR LOWER(c.objeto_compra) LIKE '%protecao individual%'
                OR LOWER(c.objeto_compra) LIKE '%material hospitalar%'
                OR LOWER(c.objeto_compra) LIKE '%materiais hospitalares%'
                OR LOWER(c.objeto_compra) LIKE '%insumo hospitalar%'
                OR LOWER(c.objeto_compra) LIKE '%insumos hospitalares%'
                OR LOWER(c.objeto_compra) LIKE '%material médico%'
                OR LOWER(c.objeto_compra) LIKE '%material medico%'
                OR LOWER(c.objeto_compra) LIKE '%materiais médicos%'
                OR LOWER(c.objeto_compra) LIKE '%materiais medicos%'
                OR LOWER(c.objeto_compra) LIKE '%médico-hospitalar%'
                OR LOWER(c.objeto_compra) LIKE '%medico-hospitalar%'
            )
        ORDER BY c.data_publicacao_pncp DESC
        LIMIT %s;
    """

    cursor.execute(sql, (LIMITE_CONTRATACOES,))
    resultados = cursor.fetchall()

    cursor.close()
    conn.close()

    print(f"Contratações selecionadas para teste: {len(resultados)}")

    return resultados

def montar_urls_itens(cnpj: str, ano: int, sequencial: str) -> list[str]:
    """
    Monta duas possibilidades de URL:
    - sequencial original
    - sequencial com zero à esquerda até 6 dígitos

    Alguns endpoints funcionam com 454; outros podem aparecer como 000454.
    """
    sequencial_original = str(sequencial)
    sequencial_formatado = str(sequencial).zfill(6)

    urls = [
        f"{BASE_URL}/orgaos/{cnpj}/compras/{ano}/{sequencial_original}/itens",
        f"{BASE_URL}/orgaos/{cnpj}/compras/{ano}/{sequencial_formatado}/itens",
    ]

    return list(dict.fromkeys(urls))


def buscar_itens_url(url: str, pagina: int = 1, tentativas: int = 3):
    """
    Busca itens em uma URL específica.

    Retornos possíveis:
    - list: lista de itens
    - None: erro ou contratação não encontrada
    - "404": contratação não cadastrada
    """
    params = {
        "pagina": pagina,
        "tamanhoPagina": TAMANHO_PAGINA,
    }

    headers = {
        "Accept": "*/*",
        "Referer": "https://pncp.gov.br/",
    }

    for tentativa in range(1, tentativas + 1):
        print(f"    Página de itens {pagina} | tentativa {tentativa} de {tentativas}")

        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                impersonate="chrome",
                timeout=60,
            )

            print("    Status:", response.status_code)
            print("    Content-Type:", response.headers.get("Content-Type"))

            if response.status_code == 404:
                print("    Contratação não cadastrada nesse endpoint.")
                print("    Resposta:", response.text[:300])
                return "404"

            if response.status_code != 200:
                print("    Erro diferente de 200.")
                print("    Resposta:", response.text[:300])

            else:
                try:
                    dados = response.json()

                    if isinstance(dados, list):
                        return dados

                    print("    JSON veio, mas não veio como lista.")
                    print("    Tipo:", type(dados))
                    print("    Resposta:", str(dados)[:300])
                    return None

                except Exception as erro_json:
                    print("    Erro ao converter para JSON.")
                    print("    Erro:", erro_json)
                    print("    Resposta:", response.text[:300])

        except Exception as erro:
            print("    Erro na requisição.")
            print("    Erro:", erro)

        if tentativa < tentativas:
            espera = tentativa * 5
            print(f"    Aguardando {espera} segundos...")
            time.sleep(espera)

    return None


def buscar_itens_contratacao(contratacao: dict) -> tuple[str, list[dict], str]:
    """
    Busca os itens de uma contratação.

    Retorna:
    - status_coleta
    - lista de itens
    - mensagem
    """
    numero_controle = contratacao["numero_controle_pncp"]
    cnpj = contratacao["orgao_cnpj"]
    ano = contratacao["ano_compra"]
    sequencial = contratacao["sequencial_compra"]

    print("\n==================================================")
    print("Buscando itens da contratação:")
    print("Número controle:", numero_controle)
    print("CNPJ:", cnpj)
    print("Ano:", ano)
    print("Sequencial:", sequencial)
    print("Objeto:", contratacao.get("objeto_compra"))

    urls = montar_urls_itens(cnpj, ano, sequencial)

    houve_404 = False

    for url in urls:
        print("\n  Testando URL:")
        print(" ", url)

        itens = buscar_itens_url(url, pagina=1)

        if itens == "404":
            houve_404 = True
            continue

        if itens is None:
            continue

        if len(itens) == 0:
            return "sem_itens", [], "Endpoint retornou lista vazia."

        # Por enquanto estamos assumindo que até 50 itens basta.
        # Depois vamos tratar paginação de itens se encontrarmos casos com 50 itens cravados.
        return "coletado", itens, f"Itens coletados com sucesso. Qtd: {len(itens)}"

    if houve_404:
        return "contratacao_nao_cadastrada", [], "Endpoint retornou 404 para as URLs testadas."

    return "erro_requisicao", [], "Não foi possível coletar itens nas URLs testadas."


def preparar_item_para_mysql(item: dict, contratacao: dict) -> dict:
    """Transforma um item da API em dicionário compatível com a tabela MySQL."""
    numero_controle = contratacao["numero_controle_pncp"]
    numero_item = item.get("numeroItem")

    id_item_composto = f"{numero_controle}-{numero_item}"

    return {
        "id_item_composto": id_item_composto,

        "numero_controle_pncp": numero_controle,
        "orgao_cnpj": contratacao["orgao_cnpj"],
        "ano_compra": contratacao["ano_compra"],
        "sequencial_compra": str(contratacao["sequencial_compra"]),

        "numero_item": numero_item,
        "descricao": item.get("descricao"),

        "material_ou_servico": item.get("materialOuServico"),
        "material_ou_servico_nome": item.get("materialOuServicoNome"),

        "valor_unitario_estimado": item.get("valorUnitarioEstimado"),
        "valor_total": item.get("valorTotal"),
        "quantidade": item.get("quantidade"),
        "unidade_medida": item.get("unidadeMedida"),

        "orcamento_sigiloso": item.get("orcamentoSigiloso"),

        "item_categoria_id": item.get("itemCategoriaId"),
        "item_categoria_nome": item.get("itemCategoriaNome"),

        "patrimonio": item.get("patrimonio"),
        "codigo_registro_imobiliario": item.get("codigoRegistroImobiliario"),

        "criterio_julgamento_id": item.get("criterioJulgamentoId"),
        "criterio_julgamento_nome": item.get("criterioJulgamentoNome"),

        "situacao_compra_item": item.get("situacaoCompraItem"),
        "situacao_compra_item_nome": item.get("situacaoCompraItemNome"),

        "tipo_beneficio": item.get("tipoBeneficio"),
        "tipo_beneficio_nome": item.get("tipoBeneficioNome"),

        "incentivo_produtivo_basico": item.get("incentivoProdutivoBasico"),

        "data_inclusao": parse_datetime(item.get("dataInclusao")),
        "data_atualizacao": parse_datetime(item.get("dataAtualizacao")),

        "tem_resultado": item.get("temResultado"),
        "imagem": item.get("imagem"),

        "aplicabilidade_margem_preferencia_normal": item.get("aplicabilidadeMargemPreferenciaNormal"),
        "aplicabilidade_margem_preferencia_adicional": item.get("aplicabilidadeMargemPreferenciaAdicional"),

        "percentual_margem_preferencia_normal": item.get("percentualMargemPreferenciaNormal"),
        "percentual_margem_preferencia_adicional": item.get("percentualMargemPreferenciaAdicional"),

        "ncm_nbs_codigo": item.get("ncmNbsCodigo"),
        "ncm_nbs_descricao": item.get("ncmNbsDescricao"),

        "catalogo": to_json_or_none(item.get("catalogo")),
        "categoria_item_catalogo": to_json_or_none(item.get("categoriaItemCatalogo")),
        "catalogo_codigo_item": item.get("catalogoCodigoItem"),

        "informacao_complementar": item.get("informacaoComplementar"),
        "tipo_margem_preferencia": item.get("tipoMargemPreferencia"),
        "exigencia_conteudo_nacional": item.get("exigenciaConteudoNacional"),
    }


def salvar_itens_mysql(itens: list[dict], contratacao: dict) -> None:
    """Salva itens na tabela stg_pncp_itens."""
    if not itens:
        return

    conn = get_mysql_connection()
    cursor = conn.cursor()

    sql = """
        INSERT INTO stg_pncp_itens (
            id_item_composto,
            numero_controle_pncp,
            orgao_cnpj,
            ano_compra,
            sequencial_compra,
            numero_item,
            descricao,
            material_ou_servico,
            material_ou_servico_nome,
            valor_unitario_estimado,
            valor_total,
            quantidade,
            unidade_medida,
            orcamento_sigiloso,
            item_categoria_id,
            item_categoria_nome,
            patrimonio,
            codigo_registro_imobiliario,
            criterio_julgamento_id,
            criterio_julgamento_nome,
            situacao_compra_item,
            situacao_compra_item_nome,
            tipo_beneficio,
            tipo_beneficio_nome,
            incentivo_produtivo_basico,
            data_inclusao,
            data_atualizacao,
            tem_resultado,
            imagem,
            aplicabilidade_margem_preferencia_normal,
            aplicabilidade_margem_preferencia_adicional,
            percentual_margem_preferencia_normal,
            percentual_margem_preferencia_adicional,
            ncm_nbs_codigo,
            ncm_nbs_descricao,
            catalogo,
            categoria_item_catalogo,
            catalogo_codigo_item,
            informacao_complementar,
            tipo_margem_preferencia,
            exigencia_conteudo_nacional
        )
        VALUES (
            %(id_item_composto)s,
            %(numero_controle_pncp)s,
            %(orgao_cnpj)s,
            %(ano_compra)s,
            %(sequencial_compra)s,
            %(numero_item)s,
            %(descricao)s,
            %(material_ou_servico)s,
            %(material_ou_servico_nome)s,
            %(valor_unitario_estimado)s,
            %(valor_total)s,
            %(quantidade)s,
            %(unidade_medida)s,
            %(orcamento_sigiloso)s,
            %(item_categoria_id)s,
            %(item_categoria_nome)s,
            %(patrimonio)s,
            %(codigo_registro_imobiliario)s,
            %(criterio_julgamento_id)s,
            %(criterio_julgamento_nome)s,
            %(situacao_compra_item)s,
            %(situacao_compra_item_nome)s,
            %(tipo_beneficio)s,
            %(tipo_beneficio_nome)s,
            %(incentivo_produtivo_basico)s,
            %(data_inclusao)s,
            %(data_atualizacao)s,
            %(tem_resultado)s,
            %(imagem)s,
            %(aplicabilidade_margem_preferencia_normal)s,
            %(aplicabilidade_margem_preferencia_adicional)s,
            %(percentual_margem_preferencia_normal)s,
            %(percentual_margem_preferencia_adicional)s,
            %(ncm_nbs_codigo)s,
            %(ncm_nbs_descricao)s,
            %(catalogo)s,
            %(categoria_item_catalogo)s,
            %(catalogo_codigo_item)s,
            %(informacao_complementar)s,
            %(tipo_margem_preferencia)s,
            %(exigencia_conteudo_nacional)s
        )
        ON DUPLICATE KEY UPDATE
            descricao = VALUES(descricao),
            material_ou_servico = VALUES(material_ou_servico),
            material_ou_servico_nome = VALUES(material_ou_servico_nome),
            valor_unitario_estimado = VALUES(valor_unitario_estimado),
            valor_total = VALUES(valor_total),
            quantidade = VALUES(quantidade),
            unidade_medida = VALUES(unidade_medida),
            orcamento_sigiloso = VALUES(orcamento_sigiloso),
            item_categoria_id = VALUES(item_categoria_id),
            item_categoria_nome = VALUES(item_categoria_nome),
            patrimonio = VALUES(patrimonio),
            codigo_registro_imobiliario = VALUES(codigo_registro_imobiliario),
            criterio_julgamento_id = VALUES(criterio_julgamento_id),
            criterio_julgamento_nome = VALUES(criterio_julgamento_nome),
            situacao_compra_item = VALUES(situacao_compra_item),
            situacao_compra_item_nome = VALUES(situacao_compra_item_nome),
            tipo_beneficio = VALUES(tipo_beneficio),
            tipo_beneficio_nome = VALUES(tipo_beneficio_nome),
            incentivo_produtivo_basico = VALUES(incentivo_produtivo_basico),
            data_inclusao = VALUES(data_inclusao),
            data_atualizacao = VALUES(data_atualizacao),
            tem_resultado = VALUES(tem_resultado),
            imagem = VALUES(imagem),
            aplicabilidade_margem_preferencia_normal = VALUES(aplicabilidade_margem_preferencia_normal),
            aplicabilidade_margem_preferencia_adicional = VALUES(aplicabilidade_margem_preferencia_adicional),
            percentual_margem_preferencia_normal = VALUES(percentual_margem_preferencia_normal),
            percentual_margem_preferencia_adicional = VALUES(percentual_margem_preferencia_adicional),
            ncm_nbs_codigo = VALUES(ncm_nbs_codigo),
            ncm_nbs_descricao = VALUES(ncm_nbs_descricao),
            catalogo = VALUES(catalogo),
            categoria_item_catalogo = VALUES(categoria_item_catalogo),
            catalogo_codigo_item = VALUES(catalogo_codigo_item),
            informacao_complementar = VALUES(informacao_complementar),
            tipo_margem_preferencia = VALUES(tipo_margem_preferencia),
            exigencia_conteudo_nacional = VALUES(exigencia_conteudo_nacional),
            data_carga = CURRENT_TIMESTAMP
    """

    registros = [preparar_item_para_mysql(item, contratacao) for item in itens]

    cursor.executemany(sql, registros)
    conn.commit()

    print(f"    Itens salvos no MySQL: {len(registros)}")

    cursor.close()
    conn.close()


def registrar_log(contratacao: dict, status: str, qtd_itens: int, mensagem: str) -> None:
    """Registra resultado da coleta na tabela de log."""
    conn = get_mysql_connection()
    cursor = conn.cursor()

    sql = """
        INSERT INTO log_pncp_coleta_itens (
            numero_controle_pncp,
            orgao_cnpj,
            ano_compra,
            sequencial_compra,
            status_coleta,
            qtd_itens,
            mensagem
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s);
    """

    cursor.execute(
        sql,
        (
            contratacao["numero_controle_pncp"],
            contratacao["orgao_cnpj"],
            contratacao["ano_compra"],
            str(contratacao["sequencial_compra"]),
            status,
            qtd_itens,
            mensagem,
        ),
    )

    conn.commit()
    cursor.close()
    conn.close()


def main():
    inicio = time.time()

    contratacoes = buscar_contratacoes_para_teste()

    total_itens = 0

    for i, contratacao in enumerate(contratacoes, start=1):
        print(f"\n### Contratação {i} de {len(contratacoes)} ###")

        status, itens, mensagem = buscar_itens_contratacao(contratacao)

        print("Status coleta:", status)
        print("Mensagem:", mensagem)
        print("Qtd itens:", len(itens))

        if status == "coletado":
            salvar_itens_mysql(itens, contratacao)
            total_itens += len(itens)

        registrar_log(
            contratacao=contratacao,
            status=status,
            qtd_itens=len(itens),
            mensagem=mensagem,
        )

        time.sleep(1)

    fim = time.time()

    print("\n==================================================")
    print("Coleta de itens finalizada.")
    print("Contratações processadas:", len(contratacoes))
    print("Total de itens coletados:", total_itens)
    print(f"Tempo total: {fim - inicio:.2f} segundos")


if __name__ == "__main__":
    main()