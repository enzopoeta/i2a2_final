# db_utils.py
import asyncpg
import logging
import json
from typing import Dict, List, Optional
from datetime import datetime, date

from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

logger = logging.getLogger(__name__)

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


async def get_nota_fiscal_by_chave(chave_acesso: str) -> Optional[Dict]:
    """
    Retrieve nota fiscal and its items from database by chave_acesso
    
    Args:
        chave_acesso: Access key of the nota fiscal
        
    Returns:
        Dict with 'nota_fiscal' and 'items' keys, or None if not found
    """
    conn = None
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Query nota fiscal header
        nf_query = """
        SELECT 
            chave_acesso, modelo, serie_nf, numero_nf, natureza_operacao, data_emissao,
            evento_mais_recente, data_hora_evento_mais_recente, cpf_cnpj_emitente, 
            razao_social_emitente, inscricao_estadual_emitente, uf_emitente, 
            municipio_emitente, cnpj_destinatario, nome_destinatario, uf_destinatario, 
            indicador_ie_destinatario, destino_operacao, consumidor_final, 
            presenca_comprador, valor_nota_fiscal, classificacao
        FROM notasfiscais
        WHERE chave_acesso = $1
        """
        
        nf_row = await conn.fetchrow(nf_query, chave_acesso)
        
        if not nf_row:
            logger.warning(f"Nota fiscal not found: {chave_acesso}")
            return None
        
        # Convert nota fiscal row to dict
        nota_fiscal = {
            'chave_acesso': nf_row['chave_acesso'],
            'modelo': nf_row['modelo'],
            'serie_nf': nf_row['serie_nf'],
            'numero_nf': nf_row['numero_nf'],
            'natureza_operacao': nf_row['natureza_operacao'],
            'data_emissao': nf_row['data_emissao'].isoformat() if nf_row['data_emissao'] else None,
            'evento_mais_recente': nf_row['evento_mais_recente'],
            'data_hora_evento_mais_recente': nf_row['data_hora_evento_mais_recente'].isoformat() if nf_row['data_hora_evento_mais_recente'] else None,
            'cpf_cnpj_emitente': nf_row['cpf_cnpj_emitente'],
            'razao_social_emitente': nf_row['razao_social_emitente'],
            'inscricao_estadual_emitente': nf_row['inscricao_estadual_emitente'],
            'uf_emitente': nf_row['uf_emitente'],
            'municipio_emitente': nf_row['municipio_emitente'],
            'cnpj_destinatario': nf_row['cnpj_destinatario'],
            'nome_destinatario': nf_row['nome_destinatario'],
            'uf_destinatario': nf_row['uf_destinatario'],
            'indicador_ie_destinatario': nf_row['indicador_ie_destinatario'],
            'destino_operacao': nf_row['destino_operacao'],
            'consumidor_final': nf_row['consumidor_final'],
            'presenca_comprador': nf_row['presenca_comprador'],
            'valor_nota_fiscal': float(nf_row['valor_nota_fiscal']) if nf_row['valor_nota_fiscal'] else None,
            'classificacao': nf_row['classificacao']
        }
        
        # Query impostos totais da nota
        impostos_nota_query = """
        SELECT 
            v_bc_icms, v_icms, v_icms_deson, v_fcp_uf_dest, v_icms_uf_dest, v_icms_uf_remet,
            v_bc_st, v_st, v_ipi, v_ipi_devol, v_pis, v_cofins, v_ii, v_tot_trib,
            v_prod, v_frete, v_seg, v_desc, v_outro, v_nf
        FROM impostos_nota_fiscal
        WHERE chave_acesso_nf = $1
        """
        
        impostos_nota_row = await conn.fetchrow(impostos_nota_query, chave_acesso)
        
        # Add impostos to nota_fiscal if available
        if impostos_nota_row:
            nota_fiscal['impostos'] = {
                'v_bc_icms': float(impostos_nota_row['v_bc_icms']) if impostos_nota_row['v_bc_icms'] else None,
                'v_icms': float(impostos_nota_row['v_icms']) if impostos_nota_row['v_icms'] else None,
                'v_icms_deson': float(impostos_nota_row['v_icms_deson']) if impostos_nota_row['v_icms_deson'] else None,
                'v_fcp_uf_dest': float(impostos_nota_row['v_fcp_uf_dest']) if impostos_nota_row['v_fcp_uf_dest'] else None,
                'v_icms_uf_dest': float(impostos_nota_row['v_icms_uf_dest']) if impostos_nota_row['v_icms_uf_dest'] else None,
                'v_icms_uf_remet': float(impostos_nota_row['v_icms_uf_remet']) if impostos_nota_row['v_icms_uf_remet'] else None,
                'v_bc_st': float(impostos_nota_row['v_bc_st']) if impostos_nota_row['v_bc_st'] else None,
                'v_st': float(impostos_nota_row['v_st']) if impostos_nota_row['v_st'] else None,
                'v_ipi': float(impostos_nota_row['v_ipi']) if impostos_nota_row['v_ipi'] else None,
                'v_ipi_devol': float(impostos_nota_row['v_ipi_devol']) if impostos_nota_row['v_ipi_devol'] else None,
                'v_pis': float(impostos_nota_row['v_pis']) if impostos_nota_row['v_pis'] else None,
                'v_cofins': float(impostos_nota_row['v_cofins']) if impostos_nota_row['v_cofins'] else None,
                'v_ii': float(impostos_nota_row['v_ii']) if impostos_nota_row['v_ii'] else None,
                'v_tot_trib': float(impostos_nota_row['v_tot_trib']) if impostos_nota_row['v_tot_trib'] else None,
                'v_prod': float(impostos_nota_row['v_prod']) if impostos_nota_row['v_prod'] else None,
                'v_frete': float(impostos_nota_row['v_frete']) if impostos_nota_row['v_frete'] else None,
                'v_seg': float(impostos_nota_row['v_seg']) if impostos_nota_row['v_seg'] else None,
                'v_desc': float(impostos_nota_row['v_desc']) if impostos_nota_row['v_desc'] else None,
                'v_outro': float(impostos_nota_row['v_outro']) if impostos_nota_row['v_outro'] else None,
                'v_nf': float(impostos_nota_row['v_nf']) if impostos_nota_row['v_nf'] else None
            }
        
        # Query items with tax data
        items_query = """
        SELECT 
            i.chave_acesso_nf, i.modelo, i.serie_nf, i.numero_nf, i.natureza_operacao, i.data_emissao,
            i.cpf_cnpj_emitente, i.razao_social_emitente, i.inscricao_estadual_emitente, 
            i.uf_emitente, i.municipio_emitente, i.cnpj_destinatario, i.nome_destinatario, 
            i.uf_destinatario, i.indicador_ie_destinatario, i.destino_operacao, 
            i.consumidor_final, i.presenca_comprador, i.numero_produto, i.descricao_produto, 
            i.codigo_ncm_sh, i.ncm_sh_tipo_produto, i.cfop, i.quantidade, i.unidade, 
            i.valor_unitario, i.valor_total,
            imp.v_tot_trib, imp.icms_orig, imp.icms_cst, imp.icms_mod_bc, imp.icms_v_bc, 
            imp.icms_p_icms, imp.icms_v_icms,
            imp.icms_uf_v_bc_uf_dest, imp.icms_uf_v_bc_fcp_uf_dest, imp.icms_uf_p_fcp_uf_dest,
            imp.icms_uf_p_icms_uf_dest, imp.icms_uf_p_icms_inter, imp.icms_uf_p_icms_inter_part,
            imp.icms_uf_v_fcp_uf_dest, imp.icms_uf_v_icms_uf_dest, imp.icms_uf_v_icms_uf_remet,
            imp.ipi_c_enq, imp.ipi_cst, imp.ipi_v_bc, imp.ipi_p_ipi, imp.ipi_v_ipi,
            imp.pis_cst, imp.pis_v_bc, imp.pis_p_pis, imp.pis_v_pis,
            imp.cofins_cst, imp.cofins_v_bc, imp.cofins_p_cofins, imp.cofins_v_cofins
        FROM itensnotafiscal i
        LEFT JOIN impostos_item imp ON i.id_item_nf = imp.id_item_nf
        WHERE i.chave_acesso_nf = $1
        ORDER BY i.numero_produto
        """
        
        items_rows = await conn.fetch(items_query, chave_acesso)
        
        # Convert items to list of dicts
        items = []
        for item_row in items_rows:
            item = {
                'chave_acesso_nf': item_row['chave_acesso_nf'],
                'modelo': item_row['modelo'],
                'serie_nf': item_row['serie_nf'],
                'numero_nf': item_row['numero_nf'],
                'natureza_operacao': item_row['natureza_operacao'],
                'data_emissao': item_row['data_emissao'].isoformat() if item_row['data_emissao'] else None,
                'cpf_cnpj_emitente': item_row['cpf_cnpj_emitente'],
                'razao_social_emitente': item_row['razao_social_emitente'],
                'inscricao_estadual_emitente': item_row['inscricao_estadual_emitente'],
                'uf_emitente': item_row['uf_emitente'],
                'municipio_emitente': item_row['municipio_emitente'],
                'cnpj_destinatario': item_row['cnpj_destinatario'],
                'nome_destinatario': item_row['nome_destinatario'],
                'uf_destinatario': item_row['uf_destinatario'],
                'indicador_ie_destinatario': item_row['indicador_ie_destinatario'],
                'destino_operacao': item_row['destino_operacao'],
                'consumidor_final': item_row['consumidor_final'],
                'presenca_comprador': item_row['presenca_comprador'],
                'numero_produto': item_row['numero_produto'],
                'descricao_produto': item_row['descricao_produto'],
                'codigo_ncm_sh': item_row['codigo_ncm_sh'],
                'ncm_sh_tipo_produto': item_row['ncm_sh_tipo_produto'],
                'cfop': item_row['cfop'],
                'quantidade': float(item_row['quantidade']) if item_row['quantidade'] else None,
                'unidade': item_row['unidade'],
                'valor_unitario': float(item_row['valor_unitario']) if item_row['valor_unitario'] else None,
                'valor_total': float(item_row['valor_total']) if item_row['valor_total'] else None
            }
            
            # Add tax data if available (LEFT JOIN may return NULL)
            if item_row['v_tot_trib'] is not None:
                item['impostos'] = {
                    'v_tot_trib': float(item_row['v_tot_trib']) if item_row['v_tot_trib'] else None,
                    'icms': {
                        'orig': item_row['icms_orig'],
                        'cst': item_row['icms_cst'],
                        'mod_bc': item_row['icms_mod_bc'],
                        'v_bc': float(item_row['icms_v_bc']) if item_row['icms_v_bc'] else None,
                        'p_icms': float(item_row['icms_p_icms']) if item_row['icms_p_icms'] else None,
                        'v_icms': float(item_row['icms_v_icms']) if item_row['icms_v_icms'] else None
                    },
                    'icms_uf_dest': {
                        'v_bc_uf_dest': float(item_row['icms_uf_v_bc_uf_dest']) if item_row['icms_uf_v_bc_uf_dest'] else None,
                        'v_bc_fcp_uf_dest': float(item_row['icms_uf_v_bc_fcp_uf_dest']) if item_row['icms_uf_v_bc_fcp_uf_dest'] else None,
                        'p_fcp_uf_dest': float(item_row['icms_uf_p_fcp_uf_dest']) if item_row['icms_uf_p_fcp_uf_dest'] else None,
                        'p_icms_uf_dest': float(item_row['icms_uf_p_icms_uf_dest']) if item_row['icms_uf_p_icms_uf_dest'] else None,
                        'p_icms_inter': float(item_row['icms_uf_p_icms_inter']) if item_row['icms_uf_p_icms_inter'] else None,
                        'p_icms_inter_part': float(item_row['icms_uf_p_icms_inter_part']) if item_row['icms_uf_p_icms_inter_part'] else None,
                        'v_fcp_uf_dest': float(item_row['icms_uf_v_fcp_uf_dest']) if item_row['icms_uf_v_fcp_uf_dest'] else None,
                        'v_icms_uf_dest': float(item_row['icms_uf_v_icms_uf_dest']) if item_row['icms_uf_v_icms_uf_dest'] else None,
                        'v_icms_uf_remet': float(item_row['icms_uf_v_icms_uf_remet']) if item_row['icms_uf_v_icms_uf_remet'] else None
                    },
                    'ipi': {
                        'c_enq': item_row['ipi_c_enq'],
                        'cst': item_row['ipi_cst'],
                        'v_bc': float(item_row['ipi_v_bc']) if item_row['ipi_v_bc'] else None,
                        'p_ipi': float(item_row['ipi_p_ipi']) if item_row['ipi_p_ipi'] else None,
                        'v_ipi': float(item_row['ipi_v_ipi']) if item_row['ipi_v_ipi'] else None
                    },
                    'pis': {
                        'cst': item_row['pis_cst'],
                        'v_bc': float(item_row['pis_v_bc']) if item_row['pis_v_bc'] else None,
                        'p_pis': float(item_row['pis_p_pis']) if item_row['pis_p_pis'] else None,
                        'v_pis': float(item_row['pis_v_pis']) if item_row['pis_v_pis'] else None
                    },
                    'cofins': {
                        'cst': item_row['cofins_cst'],
                        'v_bc': float(item_row['cofins_v_bc']) if item_row['cofins_v_bc'] else None,
                        'p_cofins': float(item_row['cofins_p_cofins']) if item_row['cofins_p_cofins'] else None,
                        'v_cofins': float(item_row['cofins_v_cofins']) if item_row['cofins_v_cofins'] else None
                    }
                }
            
            items.append(item)
        
        logger.info(f"Retrieved nota fiscal {chave_acesso} with {len(items)} items")
        
        return {
            'nota_fiscal': nota_fiscal,
            'items': items
        }
        
    except Exception as e:
        logger.error(f"Error retrieving nota fiscal from database: {e}", exc_info=True)
        return None
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
            (SELECT COUNT(*) FROM itensnotafiscal) as itens_nota_fiscal
        """
        
        stats = await conn.fetchrow(stats_query)
        
        if stats:
            return {
                "notas_fiscais": stats["notas_fiscais"] or 0,
                "itens_nota_fiscal": stats["itens_nota_fiscal"] or 0
            }
        else:
            return {
                "notas_fiscais": 0,
                "itens_nota_fiscal": 0
            }
    except Exception as e:
        logger.error(f"Error getting database statistics: {e}")
        return {
            "notas_fiscais": 0,
            "itens_nota_fiscal": 0
        }
    finally:
        if conn:
            await conn.close()


async def ensure_analise_fiscal_table():
    """Create analise_fiscal table if it doesn't exist"""
    conn = None
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        create_table_query = """
        CREATE TABLE IF NOT EXISTS analise_fiscal (
            id SERIAL PRIMARY KEY,
            chave_acesso VARCHAR(44) NOT NULL UNIQUE,
            numero_nota VARCHAR(50),
            data_emissao DATE,
            cnpj_emitente VARCHAR(18),
            razao_social_emitente TEXT,
            uf_emitente VARCHAR(2),
            crt INTEGER,
            regime_tributario_inferido VARCHAR(100),
            cnpj_destinatario VARCHAR(18),
            razao_social_destinatario TEXT,
            uf_destinatario VARCHAR(2),
            ind_ie_dest VARCHAR(50),
            valor_produtos DECIMAL(15,2),
            valor_total_nfe DECIMAL(15,2),
            valor_total_icms_destacado DECIMAL(15,2),
            regime_pis_cofins VARCHAR(100),
            base_calculo_pis_cofins DECIMAL(15,2),
            aliquota_pis DECIMAL(5,2),
            aliquota_cofins DECIMAL(5,2),
            valor_pis_estimado DECIMAL(15,2),
            valor_cofins_estimado DECIMAL(15,2),
            observacoes_pis_cofins TEXT,
            icms_por_item JSONB,
            potencial_difal BOOLEAN,
            observacoes_difal TEXT,
            recuperacao_credito JSONB,
            dados_completos JSONB,
            em_processamento BOOLEAN DEFAULT FALSE,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chave_acesso) REFERENCES notasfiscais(chave_acesso) ON DELETE CASCADE
        );
        
        CREATE INDEX IF NOT EXISTS idx_analise_fiscal_processamento ON analise_fiscal(em_processamento);
        
        -- Alter columns if table already exists with wrong sizes
        DO $$ 
        BEGIN
            -- Increase ind_ie_dest from VARCHAR(1) to VARCHAR(50)
            ALTER TABLE analise_fiscal ALTER COLUMN ind_ie_dest TYPE VARCHAR(50);
        EXCEPTION
            WHEN others THEN NULL;
        END $$;
        
        DO $$ 
        BEGIN
            -- Increase numero_nota from VARCHAR(20) to VARCHAR(50)
            ALTER TABLE analise_fiscal ALTER COLUMN numero_nota TYPE VARCHAR(50);
        EXCEPTION
            WHEN others THEN NULL;
        END $$;
        
        DO $$ 
        BEGIN
            -- Change razao_social_emitente to TEXT
            ALTER TABLE analise_fiscal ALTER COLUMN razao_social_emitente TYPE TEXT;
        EXCEPTION
            WHEN others THEN NULL;
        END $$;
        
        DO $$ 
        BEGIN
            -- Change razao_social_destinatario to TEXT
            ALTER TABLE analise_fiscal ALTER COLUMN razao_social_destinatario TYPE TEXT;
        EXCEPTION
            WHEN others THEN NULL;
        END $$;
        
        DO $$ 
        BEGIN
            -- Increase regime_tributario_inferido from VARCHAR(50) to VARCHAR(100)
            ALTER TABLE analise_fiscal ALTER COLUMN regime_tributario_inferido TYPE VARCHAR(100);
        EXCEPTION
            WHEN others THEN NULL;
        END $$;
        
        DO $$ 
        BEGIN
            -- Increase regime_pis_cofins from VARCHAR(50) to VARCHAR(100)
            ALTER TABLE analise_fiscal ALTER COLUMN regime_pis_cofins TYPE VARCHAR(100);
        EXCEPTION
            WHEN others THEN NULL;
        END $$;
        """
        
        await conn.execute(create_table_query)
        logger.info("Table analise_fiscal created or already exists")
        
    except Exception as e:
        logger.error(f"Error creating analise_fiscal table: {e}")
        raise
    finally:
        if conn:
            await conn.close()


async def save_analise_fiscal(chave_acesso: str, dados_analise: dict, em_processamento: bool = False):
    """Save fiscal analysis data to database"""
    conn = None
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Ensure table exists
        await ensure_analise_fiscal_table()
        
        # Extract data from JSON
        analise = dados_analise.get("analise_fiscal", {})
        info_nfe = analise.get("info_nfe", {})
        emitente = info_nfe.get("emitente", {})
        destinatario = info_nfe.get("destinatario", {})
        valores_totais = info_nfe.get("valores_totais", {})
        tributos = analise.get("tributos_calculados", {})
        pis_cofins = tributos.get("pis_cofins", {})
        icms_geral = tributos.get("icms_geral", {})
        icms_por_item = tributos.get("icms_por_item", [])
        recuperacao = analise.get("recuperacao_credito_expectativa", {})
        
        # Convert date string to date object if needed
        data_emissao = info_nfe.get("data_emissao")
        if data_emissao and isinstance(data_emissao, str):
            try:
                data_emissao = datetime.strptime(data_emissao, "%Y-%m-%d").date()
            except ValueError:
                data_emissao = None
        
        # Convert JSONB fields to JSON strings
        icms_por_item_json = json.dumps(icms_por_item) if icms_por_item else None
        recuperacao_json = json.dumps(recuperacao) if recuperacao else None
        dados_completos_json = json.dumps(dados_analise) if dados_analise else None
        
        # Helper function to safely convert to number (handles both string and numeric inputs)
        def to_number(value, default=None, is_int=False):
            if value is None:
                return default
            try:
                # If already a number, just ensure correct type
                if isinstance(value, (int, float)):
                    return int(value) if is_int else float(value)
                # If string, convert to number
                elif isinstance(value, str):
                    return int(value) if is_int else float(value)
                else:
                    return default
            except (ValueError, TypeError):
                return default
        
        # Helper function to safely convert to string (handles both string and numeric inputs)
        def to_string(value, default=None):
            if value is None:
                return default
            try:
                return str(value)
            except:
                return default
        
        # Insert or update
        query = """
        INSERT INTO analise_fiscal (
            chave_acesso,
            numero_nota,
            data_emissao,
            cnpj_emitente,
            razao_social_emitente,
            uf_emitente,
            crt,
            regime_tributario_inferido,
            cnpj_destinatario,
            razao_social_destinatario,
            uf_destinatario,
            ind_ie_dest,
            valor_produtos,
            valor_total_nfe,
            valor_total_icms_destacado,
            regime_pis_cofins,
            base_calculo_pis_cofins,
            aliquota_pis,
            aliquota_cofins,
            valor_pis_estimado,
            valor_cofins_estimado,
            observacoes_pis_cofins,
            icms_por_item,
            potencial_difal,
            observacoes_difal,
            recuperacao_credito,
            dados_completos,
            em_processamento,
            data_atualizacao
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
            $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28,
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (chave_acesso) 
        DO UPDATE SET
            numero_nota = EXCLUDED.numero_nota,
            data_emissao = EXCLUDED.data_emissao,
            cnpj_emitente = EXCLUDED.cnpj_emitente,
            razao_social_emitente = EXCLUDED.razao_social_emitente,
            uf_emitente = EXCLUDED.uf_emitente,
            crt = EXCLUDED.crt,
            regime_tributario_inferido = EXCLUDED.regime_tributario_inferido,
            cnpj_destinatario = EXCLUDED.cnpj_destinatario,
            razao_social_destinatario = EXCLUDED.razao_social_destinatario,
            uf_destinatario = EXCLUDED.uf_destinatario,
            ind_ie_dest = EXCLUDED.ind_ie_dest,
            valor_produtos = EXCLUDED.valor_produtos,
            valor_total_nfe = EXCLUDED.valor_total_nfe,
            valor_total_icms_destacado = EXCLUDED.valor_total_icms_destacado,
            regime_pis_cofins = EXCLUDED.regime_pis_cofins,
            base_calculo_pis_cofins = EXCLUDED.base_calculo_pis_cofins,
            aliquota_pis = EXCLUDED.aliquota_pis,
            aliquota_cofins = EXCLUDED.aliquota_cofins,
            valor_pis_estimado = EXCLUDED.valor_pis_estimado,
            valor_cofins_estimado = EXCLUDED.valor_cofins_estimado,
            observacoes_pis_cofins = EXCLUDED.observacoes_pis_cofins,
            icms_por_item = EXCLUDED.icms_por_item,
            potencial_difal = EXCLUDED.potencial_difal,
            observacoes_difal = EXCLUDED.observacoes_difal,
            recuperacao_credito = EXCLUDED.recuperacao_credito,
            dados_completos = EXCLUDED.dados_completos,
            em_processamento = EXCLUDED.em_processamento,
            data_atualizacao = CURRENT_TIMESTAMP
        RETURNING id;
        """
        
        result = await conn.fetchval(
            query,
            chave_acesso,
            to_string(info_nfe.get("numero_nota")),
            data_emissao,
            to_string(emitente.get("cnpj")),
            emitente.get("razao_social"),
            emitente.get("uf"),
            to_number(emitente.get("crt"), is_int=True),
            emitente.get("regime_tributario_inferido"),
            to_string(destinatario.get("cnpj")),
            destinatario.get("razao_social"),
            destinatario.get("uf"),
            to_string(destinatario.get("ind_ie_dest")),
            to_number(valores_totais.get("valor_produtos")),
            to_number(valores_totais.get("valor_total_nfe")),
            to_number(valores_totais.get("valor_total_icms_destacado")),
            pis_cofins.get("regime_aplicado"),
            to_number(pis_cofins.get("base_calculo_estimada")),
            to_number(pis_cofins.get("aliquota_pis")),
            to_number(pis_cofins.get("aliquota_cofins")),
            to_number(pis_cofins.get("valor_pis_estimado")),
            to_number(pis_cofins.get("valor_cofins_estimado")),
            pis_cofins.get("observacoes"),
            icms_por_item_json,
            icms_geral.get("potencial_difal"),
            icms_geral.get("observacoes_difal"),
            recuperacao_json,
            dados_completos_json,
            em_processamento
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error saving analise fiscal: {e}")
        raise
    finally:
        if conn:
            await conn.close()


async def update_analise_fiscal_processamento(chave_acesso: str, em_processamento: bool):
    """
    Update em_processamento field for a fiscal analysis.
    If record doesn't exist, creates a new one with minimal data (nota fiscal must exist).
    """
    conn = None
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Ensure table exists
        await ensure_analise_fiscal_table()
        
        # Check if analise_fiscal record exists
        check_analise_query = "SELECT id FROM analise_fiscal WHERE chave_acesso = $1"
        analise_id = await conn.fetchval(check_analise_query, chave_acesso)
        
        if not analise_id:
            # Analise doesn't exist, check if nota fiscal exists
            check_nota_query = "SELECT chave_acesso FROM notasfiscais WHERE chave_acesso = $1"
            nota_exists = await conn.fetchval(check_nota_query, chave_acesso)
            
            if not nota_exists:
                logger.warning(f"Nota fiscal not found for chave_acesso: {chave_acesso}")
                return {
                    "error": "nota_fiscal_not_found",
                    "message": f"Nota fiscal não encontrada para chave_acesso: {chave_acesso}"
                }
            
            # Nota fiscal exists, create analise_fiscal record
            logger.info(f"Analise fiscal not found for chave_acesso: {chave_acesso}, creating new record")
            
            insert_query = """
            INSERT INTO analise_fiscal (
                chave_acesso,
                em_processamento,
                data_criacao,
                data_atualizacao
            ) VALUES (
                $1, $2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            RETURNING id, em_processamento, data_atualizacao
            """
            
            result = await conn.fetchrow(insert_query, chave_acesso, em_processamento)
            
            if result:
                logger.info(f"Created new analise fiscal with em_processamento={em_processamento} for chave_acesso: {chave_acesso}")
                return {
                    "id": result["id"],
                    "chave_acesso": chave_acesso,
                    "em_processamento": result["em_processamento"],
                    "data_atualizacao": result["data_atualizacao"].isoformat() if result["data_atualizacao"] else None,
                    "created": True
                }
        else:
            # Analise exists, update it
            update_query = """
            UPDATE analise_fiscal 
            SET em_processamento = $1, 
                data_atualizacao = CURRENT_TIMESTAMP
            WHERE chave_acesso = $2
            RETURNING id, em_processamento, data_atualizacao
            """
            
            result = await conn.fetchrow(update_query, em_processamento, chave_acesso)
            
            if result:
                logger.info(f"Updated em_processamento to {em_processamento} for chave_acesso: {chave_acesso}")
                return {
                    "id": result["id"],
                    "chave_acesso": chave_acesso,
                    "em_processamento": result["em_processamento"],
                    "data_atualizacao": result["data_atualizacao"].isoformat() if result["data_atualizacao"] else None,
                    "created": False
                }
        
        return None
        
    except Exception as e:
        logger.error(f"Error updating/creating em_processamento: {e}")
        raise
    finally:
        if conn:
            await conn.close()


async def get_analise_fiscal_by_chave(chave_acesso: str):
    """Get fiscal analysis by chave_acesso"""
    conn = None
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        query = """
        SELECT 
            id,
            chave_acesso,
            numero_nota,
            data_emissao,
            cnpj_emitente,
            razao_social_emitente,
            uf_emitente,
            crt,
            regime_tributario_inferido,
            cnpj_destinatario,
            razao_social_destinatario,
            uf_destinatario,
            ind_ie_dest,
            valor_produtos,
            valor_total_nfe,
            valor_total_icms_destacado,
            regime_pis_cofins,
            base_calculo_pis_cofins,
            aliquota_pis,
            aliquota_cofins,
            valor_pis_estimado,
            valor_cofins_estimado,
            observacoes_pis_cofins,
            icms_por_item::text as icms_por_item,
            potencial_difal,
            observacoes_difal,
            recuperacao_credito::text as recuperacao_credito,
            dados_completos::text as dados_completos,
            em_processamento,
            data_criacao,
            data_atualizacao
        FROM analise_fiscal
        WHERE chave_acesso = $1
        """
        
        row = await conn.fetchrow(query, chave_acesso)
        
        if not row:
            logger.info(f"Analise fiscal not found for chave_acesso: {chave_acesso}")
            return None
        
        # Helper function to parse JSON fields
        def parse_json_field(value):
            if value is None:
                return None
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    logger.debug(f"Parsed JSON field from string to {type(parsed)}")
                    return parsed
                except Exception as e:
                    logger.warning(f"Failed to parse JSON field: {e}")
                    return value
            logger.debug(f"JSON field already parsed, type: {type(value)}")
            return value
        
        # Convert row to dict
        analise = {
            "id": row["id"],
            "chave_acesso": row["chave_acesso"],
            "numero_nota": row["numero_nota"],
            "data_emissao": row["data_emissao"].isoformat() if row["data_emissao"] else None,
            "cnpj_emitente": row["cnpj_emitente"],
            "razao_social_emitente": row["razao_social_emitente"],
            "uf_emitente": row["uf_emitente"],
            "crt": row["crt"],
            "regime_tributario_inferido": row["regime_tributario_inferido"],
            "cnpj_destinatario": row["cnpj_destinatario"],
            "razao_social_destinatario": row["razao_social_destinatario"],
            "uf_destinatario": row["uf_destinatario"],
            "ind_ie_dest": row["ind_ie_dest"],
            "valor_produtos": float(row["valor_produtos"]) if row["valor_produtos"] else None,
            "valor_total_nfe": float(row["valor_total_nfe"]) if row["valor_total_nfe"] else None,
            "valor_total_icms_destacado": float(row["valor_total_icms_destacado"]) if row["valor_total_icms_destacado"] else None,
            "regime_pis_cofins": row["regime_pis_cofins"],
            "base_calculo_pis_cofins": float(row["base_calculo_pis_cofins"]) if row["base_calculo_pis_cofins"] else None,
            "aliquota_pis": float(row["aliquota_pis"]) if row["aliquota_pis"] else None,
            "aliquota_cofins": float(row["aliquota_cofins"]) if row["aliquota_cofins"] else None,
            "valor_pis_estimado": float(row["valor_pis_estimado"]) if row["valor_pis_estimado"] else None,
            "valor_cofins_estimado": float(row["valor_cofins_estimado"]) if row["valor_cofins_estimado"] else None,
            "observacoes_pis_cofins": row["observacoes_pis_cofins"],
            "icms_por_item": parse_json_field(row["icms_por_item"]),
            "potencial_difal": row["potencial_difal"],
            "observacoes_difal": row["observacoes_difal"],
            "recuperacao_credito": parse_json_field(row["recuperacao_credito"]),
            "dados_completos": parse_json_field(row["dados_completos"]),
            "em_processamento": row["em_processamento"],
            "data_criacao": row["data_criacao"].isoformat() if row["data_criacao"] else None,
            "data_atualizacao": row["data_atualizacao"].isoformat() if row["data_atualizacao"] else None
        }
        
        logger.info(f"Found analise fiscal for chave_acesso: {chave_acesso}")
        return analise
        
    except Exception as e:
        logger.error(f"Error getting analise fiscal: {e}")
        raise
    finally:
        if conn:
            await conn.close()

