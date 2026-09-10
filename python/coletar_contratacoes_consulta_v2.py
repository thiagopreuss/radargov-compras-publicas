import os
import json
import time
from datetime import datetime
from typing import Any, Optional

import mysql.connector
from dotenv import load_dotenv
from curl_cffi import requests


load_dotenv()


URL = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"


DATA_INICIAL = "20260111"
DATA_FINAL = "20260331"
UF = "RJ"
MODALIDADE = 8
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
    """
    Converte uma data/hora vinda da API para o formato aceito pelo MySQL.

    Exemplo de entrada:
    2026-01-02T10:23:09

    Exemplo de saída:
    2026-01-02 10:23:09
    """
    if not value:
        return None

    try:
        dt = datetime.fromisoformat(value.replace("Z", ""))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def parse_date_yyyymmdd(value: str) -> Optional[str]:
    """
    Converte uma data no formato AAAAMMDD para o formato DATE do MySQL.

    Exemplo:
    20260101 -> 2026-01-01
    """
    if not value:
        return None

    try:
        dt = datetime.strptime(value, "%Y%m%d")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


def to_json_or_none(value: Any) -> Optional[str]:
    """
    Converte listas/dicionários em texto JSON para gravar em coluna JSON do MySQL.
    Se vier None, mantém None.
    """
    if value is None:
        return None

    return json.dumps(value, ensure_ascii=False)


def buscar_pagina(pagina: int, tentativas: int = 3) -> dict:
    """Busca uma página da API oficial de Consulta do PNCP, com tentativas em caso de erro."""
    params = {
        "dataInicial": DATA_INICIAL,
        "dataFinal": DATA_FINAL,
        "codigoModalidadeContratacao": MODALIDADE,
        "uf": UF,
        "pagina": pagina,
        "tamanhoPagina": TAMANHO_PAGINA,
    }

    headers = {
        "Accept": "*/*",
        "Referer": "https://pncp.gov.br/",
    }

    for tentativa in range(1, tentativas + 1):
        print(f"\nPágina {pagina} | Tentativa {tentativa} de {tentativas}")

        try:
            response = requests.get(
                URL,
                params=params,
                headers=headers,
                impersonate="chrome",
                timeout=60,
            )

            print("URL chamada:", response.url)
            print("Status code:", response.status_code)
            print("Content-Type:", response.headers.get("Content-Type"))

            if response.status_code == 200:
                try:
                    return response.json()
                except Exception as erro_json:
                    print("Erro ao converter resposta para JSON.")
                    print("Erro:", erro_json)
                    print("Resposta bruta:")
                    print(response.text[:500])

            else:
                print("Erro na requisição.")
                print("Resposta bruta:")
                print(response.text[:500])

        except Exception as erro_requisicao:
            print("Erro ao fazer requisição.")
            print("Erro:", erro_requisicao)

        if tentativa < tentativas:
            tempo_espera = tentativa * 5
            print(f"Aguardando {tempo_espera} segundos antes de tentar novamente...")
            time.sleep(tempo_espera)

    print(f"Falha ao buscar página {pagina} após {tentativas} tentativas.")
    return {}


def coletar_todas_paginas() -> list[dict]:
    """
    Coleta todas as páginas de contratações para o filtro configurado.

    Agora com controle de páginas que falharam:
    - tenta coletar normalmente;
    - guarda páginas com erro;
    - tenta recuperar no final;
    - avisa se a coleta ficou incompleta.
    """
    primeira_pagina = buscar_pagina(1)

    if not primeira_pagina:
        print("Não foi possível buscar a primeira página.")
        return []

    total_registros = primeira_pagina.get("totalRegistros", 0)
    total_paginas = primeira_pagina.get("totalPaginas", 0)

    todos_registros = primeira_pagina.get("data", [])

    paginas_com_erro = []

    print("\nResumo inicial:")
    print("Total registros informado:", total_registros)
    print("Total páginas informado:", total_paginas)
    print("Registros na página 1:", len(todos_registros))

    for pagina in range(2, total_paginas + 1):
        time.sleep(1)

        dados_pagina = buscar_pagina(pagina)

        if not dados_pagina:
            print(f"Página {pagina} falhou e será tentada novamente no final.")
            paginas_com_erro.append(pagina)
            continue

        registros_pagina = dados_pagina.get("data", [])

        if len(registros_pagina) == 0:
            print(f"Página {pagina} voltou com 0 registros. Será tentada novamente no final.")
            paginas_com_erro.append(pagina)
            continue

        print(f"Registros na página {pagina}: {len(registros_pagina)}")

        todos_registros.extend(registros_pagina)

    if paginas_com_erro:
        print("\nTentando recuperar páginas com erro...")
        print("Páginas com erro:", paginas_com_erro)

        paginas_ainda_com_erro = []

        for pagina in paginas_com_erro:
            time.sleep(3)

            print(f"\nRecuperando página {pagina}...")
            dados_pagina = buscar_pagina(pagina, tentativas=5)

            if not dados_pagina:
                print(f"Página {pagina} continuou falhando.")
                paginas_ainda_com_erro.append(pagina)
                continue

            registros_pagina = dados_pagina.get("data", [])

            if len(registros_pagina) == 0:
                print(f"Página {pagina} voltou com 0 registros na recuperação.")
                paginas_ainda_com_erro.append(pagina)
                continue

            print(f"Página {pagina} recuperada com {len(registros_pagina)} registros.")
            todos_registros.extend(registros_pagina)

        paginas_com_erro = paginas_ainda_com_erro

    print("\nColeta finalizada.")
    print("Total informado pela API:", total_registros)
    print("Total coletado pelo Python:", len(todos_registros))

    if len(todos_registros) != total_registros:
        print("\nATENÇÃO: coleta incompleta.")
        print("Diferença:", total_registros - len(todos_registros))

        if paginas_com_erro:
            print("Páginas que continuaram com erro:", paginas_com_erro)
        else:
            print("Nenhuma página ficou marcada como erro, mas o total não bateu.")
    else:
        print("\nColeta completa. Total coletado bate com o total informado pela API.")

    return todos_registros


def preparar_registro(item: dict) -> dict:
    """
    Transforma um registro bruto da API em um dicionário compatível com a tabela MySQL.

    Aqui é onde a gente pega campos aninhados, como:
    orgaoEntidade.cnpj
    unidadeOrgao.ufSigla
    amparoLegal.codigo
    """
    orgao = item.get("orgaoEntidade") or {}
    unidade = item.get("unidadeOrgao") or {}
    amparo = item.get("amparoLegal") or {}

    return {
        "numero_controle_pncp": item.get("numeroControlePNCP"),

        "data_inicial_busca": parse_date_yyyymmdd(DATA_INICIAL),
        "data_final_busca": parse_date_yyyymmdd(DATA_FINAL),
        "uf_busca": UF,
        "modalidade_busca_id": MODALIDADE,

        "numero_compra": item.get("numeroCompra"),
        "ano_compra": item.get("anoCompra"),
        "sequencial_compra": str(item.get("sequencialCompra")) if item.get("sequencialCompra") is not None else None,
        "processo": item.get("processo"),

        "tipo_instrumento_convocatorio_codigo": item.get("tipoInstrumentoConvocatorioCodigo"),
        "tipo_instrumento_convocatorio_nome": item.get("tipoInstrumentoConvocatorioNome"),

        "modalidade_id": item.get("modalidadeId"),
        "modalidade_nome": item.get("modalidadeNome"),

        "modo_disputa_id": item.get("modoDisputaId"),
        "modo_disputa_nome": item.get("modoDisputaNome"),

        "situacao_compra_id": item.get("situacaoCompraId"),
        "situacao_compra_nome": item.get("situacaoCompraNome"),

        "objeto_compra": item.get("objetoCompra"),
        "informacao_complementar": item.get("informacaoComplementar"),

        "srp": item.get("srp"),

        "amparo_legal_codigo": amparo.get("codigo"),
        "amparo_legal_nome": amparo.get("nome"),
        "amparo_legal_descricao": amparo.get("descricao"),

        "valor_total_estimado": item.get("valorTotalEstimado"),
        "valor_total_homologado": item.get("valorTotalHomologado"),

        "data_abertura_proposta": parse_datetime(item.get("dataAberturaProposta")),
        "data_encerramento_proposta": parse_datetime(item.get("dataEncerramentoProposta")),
        "data_publicacao_pncp": parse_datetime(item.get("dataPublicacaoPncp")),
        "data_inclusao": parse_datetime(item.get("dataInclusao")),
        "data_atualizacao": parse_datetime(item.get("dataAtualizacao")),
        "data_atualizacao_global": parse_datetime(item.get("dataAtualizacaoGlobal")),

        "orgao_cnpj": orgao.get("cnpj"),
        "orgao_razao_social": orgao.get("razaoSocial"),
        "orgao_poder_id": orgao.get("poderId"),
        "orgao_esfera_id": orgao.get("esferaId"),

        "unidade_codigo": unidade.get("codigoUnidade"),
        "unidade_nome": unidade.get("nomeUnidade"),
        "unidade_codigo_ibge": str(unidade.get("codigoIbge")) if unidade.get("codigoIbge") is not None else None,
        "unidade_municipio_nome": unidade.get("municipioNome"),
        "unidade_uf_sigla": unidade.get("ufSigla"),
        "unidade_uf_nome": unidade.get("ufNome"),

        "usuario_nome": item.get("usuarioNome"),
        "link_sistema_origem": item.get("linkSistemaOrigem"),
        "link_processo_eletronico": item.get("linkProcessoEletronico"),
        "justificativa_presencial": item.get("justificativaPresencial"),

        "fontes_orcamentarias": to_json_or_none(item.get("fontesOrcamentarias")),
        "emenda_parlamentar": to_json_or_none(item.get("emendaParlamentar")),
        "orgao_subrogado": to_json_or_none(item.get("orgaoSubRogado")),
        "unidade_subrogada": to_json_or_none(item.get("unidadeSubRogada")),
    }


def salvar_no_mysql(registros: list[dict]) -> None:
    """Insere ou atualiza os registros coletados na tabela MySQL."""
    if not registros:
        print("Nenhum registro para salvar.")
        return

    conn = get_mysql_connection()
    cursor = conn.cursor()

    sql = """
        INSERT INTO stg_pncp_contratacoes_consulta (
            numero_controle_pncp,
            data_inicial_busca,
            data_final_busca,
            uf_busca,
            modalidade_busca_id,
            numero_compra,
            ano_compra,
            sequencial_compra,
            processo,
            tipo_instrumento_convocatorio_codigo,
            tipo_instrumento_convocatorio_nome,
            modalidade_id,
            modalidade_nome,
            modo_disputa_id,
            modo_disputa_nome,
            situacao_compra_id,
            situacao_compra_nome,
            objeto_compra,
            informacao_complementar,
            srp,
            amparo_legal_codigo,
            amparo_legal_nome,
            amparo_legal_descricao,
            valor_total_estimado,
            valor_total_homologado,
            data_abertura_proposta,
            data_encerramento_proposta,
            data_publicacao_pncp,
            data_inclusao,
            data_atualizacao,
            data_atualizacao_global,
            orgao_cnpj,
            orgao_razao_social,
            orgao_poder_id,
            orgao_esfera_id,
            unidade_codigo,
            unidade_nome,
            unidade_codigo_ibge,
            unidade_municipio_nome,
            unidade_uf_sigla,
            unidade_uf_nome,
            usuario_nome,
            link_sistema_origem,
            link_processo_eletronico,
            justificativa_presencial,
            fontes_orcamentarias,
            emenda_parlamentar,
            orgao_subrogado,
            unidade_subrogada
        )
        VALUES (
            %(numero_controle_pncp)s,
            %(data_inicial_busca)s,
            %(data_final_busca)s,
            %(uf_busca)s,
            %(modalidade_busca_id)s,
            %(numero_compra)s,
            %(ano_compra)s,
            %(sequencial_compra)s,
            %(processo)s,
            %(tipo_instrumento_convocatorio_codigo)s,
            %(tipo_instrumento_convocatorio_nome)s,
            %(modalidade_id)s,
            %(modalidade_nome)s,
            %(modo_disputa_id)s,
            %(modo_disputa_nome)s,
            %(situacao_compra_id)s,
            %(situacao_compra_nome)s,
            %(objeto_compra)s,
            %(informacao_complementar)s,
            %(srp)s,
            %(amparo_legal_codigo)s,
            %(amparo_legal_nome)s,
            %(amparo_legal_descricao)s,
            %(valor_total_estimado)s,
            %(valor_total_homologado)s,
            %(data_abertura_proposta)s,
            %(data_encerramento_proposta)s,
            %(data_publicacao_pncp)s,
            %(data_inclusao)s,
            %(data_atualizacao)s,
            %(data_atualizacao_global)s,
            %(orgao_cnpj)s,
            %(orgao_razao_social)s,
            %(orgao_poder_id)s,
            %(orgao_esfera_id)s,
            %(unidade_codigo)s,
            %(unidade_nome)s,
            %(unidade_codigo_ibge)s,
            %(unidade_municipio_nome)s,
            %(unidade_uf_sigla)s,
            %(unidade_uf_nome)s,
            %(usuario_nome)s,
            %(link_sistema_origem)s,
            %(link_processo_eletronico)s,
            %(justificativa_presencial)s,
            %(fontes_orcamentarias)s,
            %(emenda_parlamentar)s,
            %(orgao_subrogado)s,
            %(unidade_subrogada)s
        )
        ON DUPLICATE KEY UPDATE
            data_inicial_busca = VALUES(data_inicial_busca),
            data_final_busca = VALUES(data_final_busca),
            uf_busca = VALUES(uf_busca),
            modalidade_busca_id = VALUES(modalidade_busca_id),
            numero_compra = VALUES(numero_compra),
            ano_compra = VALUES(ano_compra),
            sequencial_compra = VALUES(sequencial_compra),
            processo = VALUES(processo),
            tipo_instrumento_convocatorio_codigo = VALUES(tipo_instrumento_convocatorio_codigo),
            tipo_instrumento_convocatorio_nome = VALUES(tipo_instrumento_convocatorio_nome),
            modalidade_id = VALUES(modalidade_id),
            modalidade_nome = VALUES(modalidade_nome),
            modo_disputa_id = VALUES(modo_disputa_id),
            modo_disputa_nome = VALUES(modo_disputa_nome),
            situacao_compra_id = VALUES(situacao_compra_id),
            situacao_compra_nome = VALUES(situacao_compra_nome),
            objeto_compra = VALUES(objeto_compra),
            informacao_complementar = VALUES(informacao_complementar),
            srp = VALUES(srp),
            amparo_legal_codigo = VALUES(amparo_legal_codigo),
            amparo_legal_nome = VALUES(amparo_legal_nome),
            amparo_legal_descricao = VALUES(amparo_legal_descricao),
            valor_total_estimado = VALUES(valor_total_estimado),
            valor_total_homologado = VALUES(valor_total_homologado),
            data_abertura_proposta = VALUES(data_abertura_proposta),
            data_encerramento_proposta = VALUES(data_encerramento_proposta),
            data_publicacao_pncp = VALUES(data_publicacao_pncp),
            data_inclusao = VALUES(data_inclusao),
            data_atualizacao = VALUES(data_atualizacao),
            data_atualizacao_global = VALUES(data_atualizacao_global),
            orgao_cnpj = VALUES(orgao_cnpj),
            orgao_razao_social = VALUES(orgao_razao_social),
            orgao_poder_id = VALUES(orgao_poder_id),
            orgao_esfera_id = VALUES(orgao_esfera_id),
            unidade_codigo = VALUES(unidade_codigo),
            unidade_nome = VALUES(unidade_nome),
            unidade_codigo_ibge = VALUES(unidade_codigo_ibge),
            unidade_municipio_nome = VALUES(unidade_municipio_nome),
            unidade_uf_sigla = VALUES(unidade_uf_sigla),
            unidade_uf_nome = VALUES(unidade_uf_nome),
            usuario_nome = VALUES(usuario_nome),
            link_sistema_origem = VALUES(link_sistema_origem),
            link_processo_eletronico = VALUES(link_processo_eletronico),
            justificativa_presencial = VALUES(justificativa_presencial),
            fontes_orcamentarias = VALUES(fontes_orcamentarias),
            emenda_parlamentar = VALUES(emenda_parlamentar),
            orgao_subrogado = VALUES(orgao_subrogado),
            unidade_subrogada = VALUES(unidade_subrogada),
            data_carga = CURRENT_TIMESTAMP
    """

    registros_preparados = [preparar_registro(item) for item in registros]

    cursor.executemany(sql, registros_preparados)
    conn.commit()

    print(f"\nRegistros enviados para o MySQL: {len(registros_preparados)}")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    inicio = time.time()

    registros_coletados = coletar_todas_paginas()

    if registros_coletados:
        salvar_no_mysql(registros_coletados)
    else:
        print("Nenhum registro foi coletado. Nada será salvo no MySQL.")

    fim = time.time()
    tempo_total = fim - inicio

    print(f"\nTempo total de execução: {tempo_total:.2f} segundos")