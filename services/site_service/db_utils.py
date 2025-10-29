# db_utils.py
import asyncpg
from config import DATABASE_URL


async def get_all_notas_fiscais():
    """Get all notas fiscais with basic information and item count"""
    conn = None
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        query = """
        SELECT 
            nf.chave_acesso,
            nf.numero_nf,
            nf.data_emissao,
            nf.razao_social_emitente as emit_xnome,
            nf.cpf_cnpj_emitente as emit_cnpj,
            nf.nome_destinatario as dest_xnome,
            nf.cnpj_destinatario as dest_cnpj,
            nf.valor_nota_fiscal as valor_total,
            nf.classificacao,
            COUNT(i.id_item_nf) as total_items
        FROM notasfiscais nf
        LEFT JOIN itensnotafiscal i ON nf.chave_acesso = i.chave_acesso_nf
        GROUP BY nf.chave_acesso
        ORDER BY nf.data_emissao DESC
        """
        
        rows = await conn.fetch(query)
        
        notas = []
        for row in rows:
            notas.append({
                "chave_acesso": row["chave_acesso"],
                "numero_nf": row["numero_nf"],
                "data_emissao": row["data_emissao"].isoformat() if row["data_emissao"] else None,
                "emit_xnome": row["emit_xnome"],
                "emit_cnpj": row["emit_cnpj"],
                "dest_xnome": row["dest_xnome"],
                "dest_cnpj": row["dest_cnpj"],
                "valor_total": float(row["valor_total"]) if row["valor_total"] else 0.0,
                "classificacao": row["classificacao"],
                "total_items": row["total_items"]
            })
        
        return notas
        
    except Exception as e:
        print(f"Error getting all notas fiscais: {e}")
        raise
    finally:
        if conn:
            await conn.close()


async def get_nota_fiscal_by_chave(chave_acesso: str):
    """Get detailed information about a specific nota fiscal including its items"""
    conn = None
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Get nota fiscal
        nota_query = """
        SELECT 
            chave_acesso,
            modelo,
            serie_nf as serie,
            numero_nf,
            natureza_operacao,
            data_emissao,
            evento_mais_recente,
            data_hora_evento_mais_recente,
            cpf_cnpj_emitente as emit_cnpj,
            razao_social_emitente as emit_xnome,
            inscricao_estadual_emitente as emit_ie,
            uf_emitente as emit_uf,
            municipio_emitente as emit_xmun,
            cnpj_destinatario as dest_cnpj,
            nome_destinatario as dest_xnome,
            uf_destinatario as dest_uf,
            indicador_ie_destinatario as dest_indieiedest,
            destino_operacao,
            consumidor_final,
            presenca_comprador,
            valor_nota_fiscal as valor_total,
            classificacao
        FROM notasfiscais
        WHERE chave_acesso = $1
        """
        
        nota_row = await conn.fetchrow(nota_query, chave_acesso)
        
        if not nota_row:
            return None
        
        # Get items
        items_query = """
        SELECT 
            numero_produto as nitem,
            descricao_produto as xprod,
            codigo_ncm_sh as ncm,
            cfop,
            quantidade as qcom,
            unidade as ucom,
            valor_unitario as vuncom,
            valor_total as vprod,
            descricao_produto as cprod
        FROM itensnotafiscal
        WHERE chave_acesso_nf = $1
        ORDER BY numero_produto
        """
        
        items_rows = await conn.fetch(items_query, chave_acesso)
        
        # Format nota
        nota = {
            "chave_acesso": nota_row["chave_acesso"],
            "modelo": nota_row["modelo"],
            "serie": nota_row["serie"],
            "numero_nf": nota_row["numero_nf"],
            "natureza_operacao": nota_row["natureza_operacao"],
            "data_emissao": nota_row["data_emissao"].isoformat() if nota_row["data_emissao"] else None,
            "emit_cnpj": nota_row["emit_cnpj"],
            "emit_xnome": nota_row["emit_xnome"],
            "emit_ie": nota_row["emit_ie"],
            "emit_uf": nota_row["emit_uf"],
            "emit_xmun": nota_row["emit_xmun"],
            "dest_cnpj": nota_row["dest_cnpj"],
            "dest_xnome": nota_row["dest_xnome"],
            "dest_uf": nota_row["dest_uf"],
            "dest_indieiedest": nota_row["dest_indieiedest"],
            "destino_operacao": nota_row["destino_operacao"],
            "consumidor_final": nota_row["consumidor_final"],
            "presenca_comprador": nota_row["presenca_comprador"],
            "valor_total": float(nota_row["valor_total"]) if nota_row["valor_total"] else 0.0,
            "classificacao": nota_row["classificacao"],
            "icmstot_vprod": float(nota_row["valor_total"]) if nota_row["valor_total"] else 0.0,
            "icmstot_vfrete": 0.0,
            "icmstot_vdesc": 0.0
        }
        
        # Format items
        items = []
        for item_row in items_rows:
            items.append({
                "nitem": item_row["nitem"],
                "xprod": item_row["xprod"],
                "ncm": item_row["ncm"],
                "cfop": item_row["cfop"],
                "qcom": float(item_row["qcom"]) if item_row["qcom"] else 0.0,
                "ucom": item_row["ucom"],
                "vuncom": float(item_row["vuncom"]) if item_row["vuncom"] else 0.0,
                "vprod": float(item_row["vprod"]) if item_row["vprod"] else 0.0,
                "cprod": item_row["cprod"]
            })
        
        return {
            "nota": nota,
            "itens": items
        }
        
    except Exception as e:
        print(f"Error getting nota fiscal by chave: {e}")
        raise
    finally:
        if conn:
            await conn.close()


async def get_database_statistics():
    """Get database statistics"""
    conn = None
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        query = """
        SELECT 
            (SELECT COUNT(*) FROM notasfiscais) as notas_fiscais,
            (SELECT COUNT(*) FROM itensnotafiscal) as itens_nota_fiscal,
            (SELECT SUM(valor_nota_fiscal) FROM notasfiscais) as total_value,
            (SELECT MAX(data_emissao) FROM notasfiscais) as last_upload
        """
        
        stats = await conn.fetchrow(query)
        
        if stats:
            return {
                "notas_fiscais": stats["notas_fiscais"] or 0,
                "itens_nota_fiscal": stats["itens_nota_fiscal"] or 0,
                "total_records": (stats["notas_fiscais"] or 0) + (stats["itens_nota_fiscal"] or 0),
                "total_value": float(stats["total_value"]) if stats["total_value"] else 0.0,
                "last_upload": stats["last_upload"].isoformat() if stats["last_upload"] else None
            }
        else:
            return {
                "notas_fiscais": 0,
                "itens_nota_fiscal": 0,
                "total_records": 0,
                "total_value": 0.0,
                "last_upload": None
            }
    except Exception as e:
        print(f"Error getting database statistics: {e}")
        return {
            "notas_fiscais": 0,
            "itens_nota_fiscal": 0,
            "total_records": 0,
            "total_value": 0.0,
            "last_upload": None
        }
    finally:
        if conn:
            await conn.close()

