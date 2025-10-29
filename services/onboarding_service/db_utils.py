# db_utils.py
import asyncpg
import logging
from typing import Dict, List
from datetime import datetime, date

from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

logger = logging.getLogger(__name__)

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def parse_date(value):
    """Parse date from string or return as is if already a date object"""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except:
            try:
                return datetime.strptime(value, '%Y-%m-%d').date()
            except:
                return None
    return None


def parse_datetime(value):
    """Parse datetime from string or return as is if already a datetime object"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except:
            try:
                return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except:
                return None
    return None


async def insert_nota_fiscal_from_json(nota_fiscal_data: Dict, items_data: List[Dict], impostos_nota: Dict = None, impostos_items: List[Dict] = None) -> bool:
    """
    Insert nota fiscal, its items, and tax information into database
    
    Args:
        nota_fiscal_data: Dictionary with nota fiscal header data
        items_data: List of dictionaries with items data
        impostos_nota: Dictionary with total tax data for the nota fiscal (optional)
        impostos_items: List of dictionaries with tax data for each item (optional)
        
    Returns:
        bool: True if inserted successfully, False otherwise
    """
    conn = None
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Insert nota fiscal
        if nota_fiscal_data and nota_fiscal_data.get('chave_acesso'):
            insert_nf_sql = """
            INSERT INTO notasfiscais (
                chave_acesso, modelo, serie_nf, numero_nf, natureza_operacao, data_emissao,
                evento_mais_recente, data_hora_evento_mais_recente, cpf_cnpj_emitente, razao_social_emitente,
                inscricao_estadual_emitente, uf_emitente, municipio_emitente, cnpj_destinatario,
                nome_destinatario, uf_destinatario, indicador_ie_destinatario, destino_operacao,
                consumidor_final, presenca_comprador, valor_nota_fiscal, classificacao
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22
            )
            ON CONFLICT (chave_acesso) DO UPDATE SET
                classificacao = EXCLUDED.classificacao,
                evento_mais_recente = EXCLUDED.evento_mais_recente,
                data_hora_evento_mais_recente = EXCLUDED.data_hora_evento_mais_recente;
            """
            
            await conn.execute(insert_nf_sql,
                nota_fiscal_data.get('chave_acesso'),
                nota_fiscal_data.get('modelo'),
                nota_fiscal_data.get('serie_nf'),
                nota_fiscal_data.get('numero_nf'),
                nota_fiscal_data.get('natureza_operacao'),
                parse_date(nota_fiscal_data.get('data_emissao')),
                nota_fiscal_data.get('evento_mais_recente'),
                parse_datetime(nota_fiscal_data.get('data_hora_evento_mais_recente')),
                nota_fiscal_data.get('cpf_cnpj_emitente'),
                nota_fiscal_data.get('razao_social_emitente'),
                nota_fiscal_data.get('inscricao_estadual_emitente'),
                nota_fiscal_data.get('uf_emitente'),
                nota_fiscal_data.get('municipio_emitente'),
                nota_fiscal_data.get('cnpj_destinatario'),
                nota_fiscal_data.get('nome_destinatario'),
                nota_fiscal_data.get('uf_destinatario'),
                nota_fiscal_data.get('indicador_ie_destinatario'),
                nota_fiscal_data.get('destino_operacao'),
                nota_fiscal_data.get('consumidor_final'),
                nota_fiscal_data.get('presenca_comprador'),
                nota_fiscal_data.get('valor_nota_fiscal'),
                nota_fiscal_data.get('classificacao')
            )
            logger.info(f"Inserted nota fiscal: {nota_fiscal_data.get('chave_acesso')}")
        
        # Insert impostos_nota_fiscal if provided
        if impostos_nota and nota_fiscal_data.get('chave_acesso'):
            insert_impostos_nota_sql = """
            INSERT INTO impostos_nota_fiscal (
                chave_acesso_nf, v_bc_icms, v_icms, v_icms_deson, v_fcp_uf_dest, v_icms_uf_dest, v_icms_uf_remet,
                v_bc_st, v_st, v_ipi, v_ipi_devol, v_pis, v_cofins, v_ii, v_tot_trib,
                v_prod, v_frete, v_seg, v_desc, v_outro, v_nf
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21
            )
            ON CONFLICT (chave_acesso_nf) DO UPDATE SET
                v_bc_icms = EXCLUDED.v_bc_icms,
                v_icms = EXCLUDED.v_icms,
                v_icms_deson = EXCLUDED.v_icms_deson,
                v_fcp_uf_dest = EXCLUDED.v_fcp_uf_dest,
                v_icms_uf_dest = EXCLUDED.v_icms_uf_dest,
                v_icms_uf_remet = EXCLUDED.v_icms_uf_remet,
                v_bc_st = EXCLUDED.v_bc_st,
                v_st = EXCLUDED.v_st,
                v_ipi = EXCLUDED.v_ipi,
                v_ipi_devol = EXCLUDED.v_ipi_devol,
                v_pis = EXCLUDED.v_pis,
                v_cofins = EXCLUDED.v_cofins,
                v_ii = EXCLUDED.v_ii,
                v_tot_trib = EXCLUDED.v_tot_trib,
                v_prod = EXCLUDED.v_prod,
                v_frete = EXCLUDED.v_frete,
                v_seg = EXCLUDED.v_seg,
                v_desc = EXCLUDED.v_desc,
                v_outro = EXCLUDED.v_outro,
                v_nf = EXCLUDED.v_nf;
            """
            
            await conn.execute(insert_impostos_nota_sql,
                nota_fiscal_data.get('chave_acesso'),
                impostos_nota.get('v_bc'),
                impostos_nota.get('v_icms'),
                impostos_nota.get('v_icms_deson'),
                impostos_nota.get('v_fcp_uf_dest'),
                impostos_nota.get('v_icms_uf_dest'),
                impostos_nota.get('v_icms_uf_remet'),
                impostos_nota.get('v_bc_st'),
                impostos_nota.get('v_st'),
                impostos_nota.get('v_ipi'),
                impostos_nota.get('v_ipi_devol'),
                impostos_nota.get('v_pis'),
                impostos_nota.get('v_cofins'),
                impostos_nota.get('v_ii'),
                impostos_nota.get('v_tot_trib'),
                impostos_nota.get('v_prod'),
                impostos_nota.get('v_frete'),
                impostos_nota.get('v_seg'),
                impostos_nota.get('v_desc'),
                impostos_nota.get('v_outro'),
                impostos_nota.get('v_nf')
            )
            logger.info(f"Inserted impostos_nota_fiscal for: {nota_fiscal_data.get('chave_acesso')}")
        
        # Insert items and their tax data
        if items_data:
            insert_item_sql = """
            INSERT INTO itensnotafiscal (
                chave_acesso_nf, modelo, serie_nf, numero_nf, natureza_operacao, data_emissao,
                cpf_cnpj_emitente, razao_social_emitente, inscricao_estadual_emitente, uf_emitente,
                municipio_emitente, cnpj_destinatario, nome_destinatario, uf_destinatario,
                indicador_ie_destinatario, destino_operacao, consumidor_final, presenca_comprador,
                numero_produto, descricao_produto, codigo_ncm_sh, ncm_sh_tipo_produto, cfop,
                quantidade, unidade, valor_unitario, valor_total
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27
            )
            ON CONFLICT DO NOTHING
            RETURNING id_item_nf;
            """
            
            item_ids = []
            for item in items_data:
                result = await conn.fetchrow(insert_item_sql,
                    item.get('chave_acesso_nf'),
                    item.get('modelo'),
                    item.get('serie_nf'),
                    item.get('numero_nf'),
                    item.get('natureza_operacao'),
                    parse_date(item.get('data_emissao')),
                    item.get('cpf_cnpj_emitente'),
                    item.get('razao_social_emitente'),
                    item.get('inscricao_estadual_emitente'),
                    item.get('uf_emitente'),
                    item.get('municipio_emitente'),
                    item.get('cnpj_destinatario'),
                    item.get('nome_destinatario'),
                    item.get('uf_destinatario'),
                    item.get('indicador_ie_destinatario'),
                    item.get('destino_operacao'),
                    item.get('consumidor_final'),
                    item.get('presenca_comprador'),
                    item.get('numero_produto'),
                    item.get('descricao_produto'),
                    item.get('codigo_ncm_sh'),
                    item.get('ncm_sh_tipo_produto'),
                    item.get('cfop'),
                    item.get('quantidade'),
                    item.get('unidade'),
                    item.get('valor_unitario'),
                    item.get('valor_total')
                )
                if result:
                    item_ids.append(result['id_item_nf'])
            logger.info(f"Inserted {len(items_data)} items for nota fiscal")
            
            # Insert tax data for items if provided
            if impostos_items and item_ids:
                insert_impostos_item_sql = """
                INSERT INTO impostos_item (
                    id_item_nf, chave_acesso_nf, numero_item, v_tot_trib,
                    icms_orig, icms_cst, icms_mod_bc, icms_v_bc, icms_p_icms, icms_v_icms,
                    icms_uf_v_bc_uf_dest, icms_uf_v_bc_fcp_uf_dest, icms_uf_p_fcp_uf_dest, icms_uf_p_icms_uf_dest,
                    icms_uf_p_icms_inter, icms_uf_p_icms_inter_part, icms_uf_v_fcp_uf_dest, icms_uf_v_icms_uf_dest, icms_uf_v_icms_uf_remet,
                    ipi_c_enq, ipi_cst, ipi_v_bc, ipi_p_ipi, ipi_v_ipi,
                    pis_cst, pis_v_bc, pis_p_pis, pis_v_pis,
                    cofins_cst, cofins_v_bc, cofins_p_cofins, cofins_v_cofins
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31, $32
                )
                ON CONFLICT DO NOTHING;
                """
                
                for idx, imposto_item in enumerate(impostos_items):
                    if idx < len(item_ids):
                        await conn.execute(insert_impostos_item_sql,
                            item_ids[idx],
                            imposto_item.get('chave_acesso_nf'),
                            imposto_item.get('numero_item'),
                            imposto_item.get('v_tot_trib'),
                            imposto_item.get('icms_orig'),
                            imposto_item.get('icms_cst'),
                            imposto_item.get('icms_mod_bc'),
                            imposto_item.get('icms_v_bc'),
                            imposto_item.get('icms_p_icms'),
                            imposto_item.get('icms_v_icms'),
                            imposto_item.get('icms_v_bc_uf_dest'),
                            imposto_item.get('icms_v_bc_fcp_uf_dest'),
                            imposto_item.get('icms_p_fcp_uf_dest'),
                            imposto_item.get('icms_p_icms_uf_dest'),
                            imposto_item.get('icms_p_icms_inter'),
                            imposto_item.get('icms_p_icms_inter_part'),
                            imposto_item.get('icms_v_fcp_uf_dest'),
                            imposto_item.get('icms_v_icms_uf_dest'),
                            imposto_item.get('icms_v_icms_uf_remet'),
                            imposto_item.get('ipi_c_enq'),
                            imposto_item.get('ipi_cst'),
                            imposto_item.get('ipi_v_bc'),
                            imposto_item.get('ipi_p_ipi'),
                            imposto_item.get('ipi_v_ipi'),
                            imposto_item.get('pis_cst'),
                            imposto_item.get('pis_v_bc'),
                            imposto_item.get('pis_p_pis'),
                            imposto_item.get('pis_v_pis'),
                            imposto_item.get('cofins_cst'),
                            imposto_item.get('cofins_v_bc'),
                            imposto_item.get('cofins_p_cofins'),
                            imposto_item.get('cofins_v_cofins')
                        )
                logger.info(f"Inserted {len(impostos_items)} tax records for items")
        
        return True
        
    except Exception as e:
        logger.error(f"Error inserting data into database: {e}", exc_info=True)
        return False
    finally:
        if conn:
            await conn.close()


async def get_database_statistics():
    """Get database statistics for status reporting"""
    conn = None
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        stats_query = """
        SELECT 
            (SELECT COUNT(*) FROM notasfiscais) as notas_fiscais,
            (SELECT COUNT(*) FROM itensnotafiscal) as itens_nota_fiscal,
            (SELECT SUM(valor_nota_fiscal) FROM notasfiscais) as total_value,
            (SELECT MAX(data_emissao) FROM notasfiscais) as last_upload,
            (SELECT COUNT(*) FROM notasfiscais WHERE classificacao IS NOT NULL) as notas_classificadas
        """
        
        stats = await conn.fetchrow(stats_query)
        
        if stats:
            return {
                "notas_fiscais": stats["notas_fiscais"] or 0,
                "itens_nota_fiscal": stats["itens_nota_fiscal"] or 0,
                "total_records": (stats["notas_fiscais"] or 0) + (stats["itens_nota_fiscal"] or 0),
                "total_value": float(stats["total_value"]) if stats["total_value"] else 0.0,
                "last_upload": stats["last_upload"].isoformat() if stats["last_upload"] else None,
                "notas_classificadas": stats["notas_classificadas"] or 0
            }
        else:
            return {
                "notas_fiscais": 0,
                "itens_nota_fiscal": 0,
                "total_records": 0,
                "total_value": 0.0,
                "last_upload": None,
                "notas_classificadas": 0
            }
    except Exception as e:
        logger.error(f"Error getting database statistics: {e}")
        return {
            "notas_fiscais": 0,
            "itens_nota_fiscal": 0,
            "total_records": 0,
            "total_value": 0.0,
            "last_upload": None,
            "notas_classificadas": 0
        }
    finally:
        if conn:
            await conn.close()

