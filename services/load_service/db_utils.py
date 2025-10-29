# db_utils.py
import asyncpg
import aiosql
import csv
import os
from datetime import datetime

from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

SQL_QUERIES = """
-- name: create_database_if_not_exists!
-- Attempt to create the database. This might require superuser privileges or specific grants.
-- It's often better to ensure the database exists manually or via a separate setup script.
-- For simplicity, we'll try to create it, but catch exceptions if it fails (e.g., due to lack of privileges or if it already exists).
CREATE DATABASE "{db_name}";

-- name: drop_tables!
DROP TABLE IF EXISTS impostos_item;
DROP TABLE IF EXISTS impostos_nota_fiscal;
DROP TABLE IF EXISTS itensnotafiscal;
DROP TABLE IF EXISTS notasfiscais;

-- name: create_notasfiscais_table!
CREATE TABLE IF NOT EXISTS notasfiscais (
    chave_acesso VARCHAR(44) PRIMARY KEY,
    modelo VARCHAR(100),
    serie_nf VARCHAR(10),
    numero_nf VARCHAR(20),
    natureza_operacao VARCHAR(255),
    data_emissao DATE,
    evento_mais_recente VARCHAR(255),
    data_hora_evento_mais_recente TIMESTAMP,
    cpf_cnpj_emitente VARCHAR(20),
    razao_social_emitente VARCHAR(255),
    inscricao_estadual_emitente VARCHAR(20),
    uf_emitente CHAR(2),
    municipio_emitente VARCHAR(100),
    cnpj_destinatario VARCHAR(20),
    nome_destinatario VARCHAR(255),
    uf_destinatario CHAR(2),
    indicador_ie_destinatario VARCHAR(50),
    destino_operacao VARCHAR(100),
    consumidor_final VARCHAR(50),
    presenca_comprador VARCHAR(100),
    valor_nota_fiscal DECIMAL(15,2),
    classificacao VARCHAR(50)
);

-- name: create_itensnotafiscal_table!
CREATE TABLE IF NOT EXISTS itensnotafiscal (
    id_item_nf SERIAL PRIMARY KEY,
    chave_acesso_nf VARCHAR(44) NOT NULL,
    modelo VARCHAR(100),
    serie_nf VARCHAR(10),
    numero_nf VARCHAR(20),
    natureza_operacao VARCHAR(255),
    data_emissao DATE,
    cpf_cnpj_emitente VARCHAR(20),
    razao_social_emitente VARCHAR(255),
    inscricao_estadual_emitente VARCHAR(20),
    uf_emitente CHAR(2),
    municipio_emitente VARCHAR(100),
    cnpj_destinatario VARCHAR(20),
    nome_destinatario VARCHAR(255),
    uf_destinatario CHAR(2),
    indicador_ie_destinatario VARCHAR(50),
    destino_operacao VARCHAR(100),
    consumidor_final VARCHAR(50),
    presenca_comprador VARCHAR(100),
    numero_produto INT,
    descricao_produto VARCHAR(500),
    codigo_ncm_sh VARCHAR(20),
    ncm_sh_tipo_produto VARCHAR(255),
    cfop VARCHAR(10),
    quantidade DECIMAL(15,4),
    unidade VARCHAR(20),
    valor_unitario DECIMAL(15,4),
    valor_total DECIMAL(15,2),
    CONSTRAINT fk_nota_fiscal FOREIGN KEY (chave_acesso_nf) REFERENCES notasfiscais (chave_acesso) ON DELETE CASCADE
);

-- name: create_impostos_nota_fiscal_table!
CREATE TABLE IF NOT EXISTS impostos_nota_fiscal (
    id_impostos_nf SERIAL PRIMARY KEY,
    chave_acesso_nf VARCHAR(44) NOT NULL UNIQUE,
    -- ICMS Totais
    v_bc_icms DECIMAL(15,2),           -- Base de cálculo do ICMS
    v_icms DECIMAL(15,2),              -- Valor do ICMS
    v_icms_deson DECIMAL(15,2),        -- Valor do ICMS desonerado
    v_fcp_uf_dest DECIMAL(15,2),       -- Valor do FCP UF Destino
    v_icms_uf_dest DECIMAL(15,2),      -- Valor do ICMS UF Destino
    v_icms_uf_remet DECIMAL(15,2),     -- Valor do ICMS UF Remetente
    -- Substituição Tributária
    v_bc_st DECIMAL(15,2),             -- Base de cálculo do ICMS ST
    v_st DECIMAL(15,2),                -- Valor do ICMS ST
    -- IPI
    v_ipi DECIMAL(15,2),               -- Valor do IPI
    v_ipi_devol DECIMAL(15,2),         -- Valor do IPI devolvido
    -- PIS
    v_pis DECIMAL(15,2),               -- Valor do PIS
    -- COFINS
    v_cofins DECIMAL(15,2),            -- Valor do COFINS
    -- Importação
    v_ii DECIMAL(15,2),                -- Valor do Imposto de Importação
    -- Outros
    v_tot_trib DECIMAL(15,2),          -- Valor aproximado total de tributos
    -- Valores da Nota
    v_prod DECIMAL(15,2),              -- Valor total dos produtos
    v_frete DECIMAL(15,2),             -- Valor do frete
    v_seg DECIMAL(15,2),               -- Valor do seguro
    v_desc DECIMAL(15,2),              -- Valor do desconto
    v_outro DECIMAL(15,2),             -- Outras despesas acessórias
    v_nf DECIMAL(15,2),                -- Valor total da NF-e
    CONSTRAINT fk_impostos_nota FOREIGN KEY (chave_acesso_nf) REFERENCES notasfiscais (chave_acesso) ON DELETE CASCADE
);

-- name: create_impostos_item_table!
CREATE TABLE IF NOT EXISTS impostos_item (
    id_impostos_item SERIAL PRIMARY KEY,
    id_item_nf INT NOT NULL,
    chave_acesso_nf VARCHAR(44) NOT NULL,
    numero_item INT NOT NULL,
    -- Valor Total de Tributos
    v_tot_trib DECIMAL(15,2),
    -- ICMS
    icms_orig INT,                     -- Origem da mercadoria
    icms_cst VARCHAR(3),               -- CST do ICMS
    icms_mod_bc INT,                   -- Modalidade da base de cálculo
    icms_v_bc DECIMAL(15,2),           -- Base de cálculo do ICMS
    icms_p_icms DECIMAL(5,4),          -- Alíquota do ICMS
    icms_v_icms DECIMAL(15,2),         -- Valor do ICMS
    -- ICMS UF Destino (DIFAL)
    icms_uf_v_bc_uf_dest DECIMAL(15,2),      -- BC ICMS UF Destino
    icms_uf_v_bc_fcp_uf_dest DECIMAL(15,2),  -- BC FCP UF Destino
    icms_uf_p_fcp_uf_dest DECIMAL(5,4),      -- % FCP UF Destino
    icms_uf_p_icms_uf_dest DECIMAL(5,4),     -- % ICMS UF Destino
    icms_uf_p_icms_inter DECIMAL(5,4),       -- % ICMS Interestadual
    icms_uf_p_icms_inter_part DECIMAL(5,4),  -- % ICMS partilha
    icms_uf_v_fcp_uf_dest DECIMAL(15,2),     -- Valor FCP UF Destino
    icms_uf_v_icms_uf_dest DECIMAL(15,2),    -- Valor ICMS UF Destino
    icms_uf_v_icms_uf_remet DECIMAL(15,2),   -- Valor ICMS UF Remetente
    -- IPI
    ipi_c_enq VARCHAR(10),             -- Código de enquadramento do IPI
    ipi_cst VARCHAR(3),                -- CST do IPI
    ipi_v_bc DECIMAL(15,2),            -- Base de cálculo do IPI
    ipi_p_ipi DECIMAL(5,4),            -- Alíquota do IPI
    ipi_v_ipi DECIMAL(15,2),           -- Valor do IPI
    -- PIS
    pis_cst VARCHAR(3),                -- CST do PIS
    pis_v_bc DECIMAL(15,2),            -- Base de cálculo do PIS
    pis_p_pis DECIMAL(5,4),            -- Alíquota do PIS
    pis_v_pis DECIMAL(15,2),           -- Valor do PIS
    -- COFINS
    cofins_cst VARCHAR(3),             -- CST do COFINS
    cofins_v_bc DECIMAL(15,2),         -- Base de cálculo do COFINS
    cofins_p_cofins DECIMAL(5,4),      -- Alíquota do COFINS
    cofins_v_cofins DECIMAL(15,2),     -- Valor do COFINS
    CONSTRAINT fk_impostos_item_nf FOREIGN KEY (id_item_nf) REFERENCES itensnotafiscal (id_item_nf) ON DELETE CASCADE,
    CONSTRAINT fk_impostos_item_nota FOREIGN KEY (chave_acesso_nf) REFERENCES notasfiscais (chave_acesso) ON DELETE CASCADE
);

-- name: insert_nota_fiscal#
INSERT INTO notasfiscais (
    chave_acesso, modelo, serie_nf, numero_nf, natureza_operacao, data_emissao,
    evento_mais_recente, data_hora_evento_mais_recente, cpf_cnpj_emitente, razao_social_emitente,
    inscricao_estadual_emitente, uf_emitente, municipio_emitente, cnpj_destinatario,
    nome_destinatario, uf_destinatario, indicador_ie_destinatario, destino_operacao,
    consumidor_final, presenca_comprador, valor_nota_fiscal, classificacao
) VALUES (
    :chave_acesso, :modelo, :serie_nf, :numero_nf, :natureza_operacao, :data_emissao,
    :evento_mais_recente, :data_hora_evento_mais_recente, :cpf_cnpj_emitente, :razao_social_emitente,
    :inscricao_estadual_emitente, :uf_emitente, :municipio_emitente, :cnpj_destinatario,
    :nome_destinatario, :uf_destinatario, :indicador_ie_destinatario, :destino_operacao,
    :consumidor_final, :presenca_comprador, :valor_nota_fiscal, :classificacao
)
ON CONFLICT (chave_acesso) DO NOTHING;

-- name: insert_item_nota_fiscal#
INSERT INTO itensnotafiscal (
    chave_acesso_nf, modelo, serie_nf, numero_nf, natureza_operacao, data_emissao,
    cpf_cnpj_emitente, razao_social_emitente, inscricao_estadual_emitente, uf_emitente,
    municipio_emitente, cnpj_destinatario, nome_destinatario, uf_destinatario,
    indicador_ie_destinatario, destino_operacao, consumidor_final, presenca_comprador,
    numero_produto, descricao_produto, codigo_ncm_sh, ncm_sh_tipo_produto, cfop,
    quantidade, unidade, valor_unitario, valor_total
) VALUES (
    :chave_acesso_nf, :modelo, :serie_nf, :numero_nf, :natureza_operacao, :data_emissao,
    :cpf_cnpj_emitente, :razao_social_emitente, :inscricao_estadual_emitente, :uf_emitente,
    :municipio_emitente, :cnpj_destinatario, :nome_destinatario, :uf_destinatario,
    :indicador_ie_destinatario, :destino_operacao, :consumidor_final, :presenca_comprador,
    :numero_produto, :descricao_produto, :codigo_ncm_sh, :ncm_sh_tipo_produto, :cfop,
    :quantidade, :unidade, :valor_unitario, :valor_total
);

-- name: insert_impostos_nota_fiscal#
INSERT INTO impostos_nota_fiscal (
    chave_acesso_nf, v_bc_icms, v_icms, v_icms_deson, v_fcp_uf_dest, v_icms_uf_dest, 
    v_icms_uf_remet, v_bc_st, v_st, v_ipi, v_ipi_devol, v_pis, v_cofins, v_ii, 
    v_tot_trib, v_prod, v_frete, v_seg, v_desc, v_outro, v_nf
) VALUES (
    :chave_acesso_nf, :v_bc_icms, :v_icms, :v_icms_deson, :v_fcp_uf_dest, :v_icms_uf_dest,
    :v_icms_uf_remet, :v_bc_st, :v_st, :v_ipi, :v_ipi_devol, :v_pis, :v_cofins, :v_ii,
    :v_tot_trib, :v_prod, :v_frete, :v_seg, :v_desc, :v_outro, :v_nf
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

-- name: insert_impostos_item#
INSERT INTO impostos_item (
    id_item_nf, chave_acesso_nf, numero_item, v_tot_trib,
    icms_orig, icms_cst, icms_mod_bc, icms_v_bc, icms_p_icms, icms_v_icms,
    icms_uf_v_bc_uf_dest, icms_uf_v_bc_fcp_uf_dest, icms_uf_p_fcp_uf_dest,
    icms_uf_p_icms_uf_dest, icms_uf_p_icms_inter, icms_uf_p_icms_inter_part,
    icms_uf_v_fcp_uf_dest, icms_uf_v_icms_uf_dest, icms_uf_v_icms_uf_remet,
    ipi_c_enq, ipi_cst, ipi_v_bc, ipi_p_ipi, ipi_v_ipi,
    pis_cst, pis_v_bc, pis_p_pis, pis_v_pis,
    cofins_cst, cofins_v_bc, cofins_p_cofins, cofins_v_cofins
) VALUES (
    :id_item_nf, :chave_acesso_nf, :numero_item, :v_tot_trib,
    :icms_orig, :icms_cst, :icms_mod_bc, :icms_v_bc, :icms_p_icms, :icms_v_icms,
    :icms_uf_v_bc_uf_dest, :icms_uf_v_bc_fcp_uf_dest, :icms_uf_p_fcp_uf_dest,
    :icms_uf_p_icms_uf_dest, :icms_uf_p_icms_inter, :icms_uf_p_icms_inter_part,
    :icms_uf_v_fcp_uf_dest, :icms_uf_v_icms_uf_dest, :icms_uf_v_icms_uf_remet,
    :ipi_c_enq, :ipi_cst, :ipi_v_bc, :ipi_p_ipi, :ipi_v_ipi,
    :pis_cst, :pis_v_bc, :pis_p_pis, :pis_v_pis,
    :cofins_cst, :cofins_v_bc, :cofins_p_cofins, :cofins_v_cofins
);

-- name: get_database_stats^
SELECT 
    (SELECT COUNT(*) FROM notasfiscais) as notas_fiscais,
    (SELECT COUNT(*) FROM itensnotafiscal) as itens_nota_fiscal,
    (SELECT SUM(valor_nota_fiscal) FROM notasfiscais) as total_value,
    (SELECT MAX(data_emissao) FROM notasfiscais) as last_upload
;
"""

queries = aiosql.from_str(SQL_QUERIES, "asyncpg")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@db:{DB_PORT}/{DB_NAME}"
ADMIN_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@db:{DB_PORT}/postgres" # Connect to a default db for creating the target db

def parse_date(date_str):
    if not date_str: return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None

def parse_datetime(datetime_str):
    if not datetime_str: return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue
    return None

def parse_decimal(value_str, default=0.0):
    if not value_str: return default
    try:
        return float(str(value_str).replace(',', '.')) # Handle comma as decimal separator
    except ValueError:
        return default

def parse_int(value_str, default=0):
    if not value_str: return default
    try:
        return int(value_str)
    except ValueError:
        return default

async def create_db_and_tables():
    # Try to create the database itself. This requires connecting to a default database like 'postgres'.
    conn_admin = None
    try:
        conn_admin = await asyncpg.connect(ADMIN_DATABASE_URL)
        # Check if database exists
        db_exists = await conn_admin.fetchval(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        if not db_exists:
            print(f"Database {DB_NAME} does not exist. Attempting to create...")
            await conn_admin.execute(f"CREATE DATABASE \"{DB_NAME}\"") # Use escaped quotes for db name
            print(f"Database {DB_NAME} created successfully or already existed.")
        else:
            print(f"Database {DB_NAME} already exists.")
    except asyncpg.exceptions.DuplicateDatabaseError:
        print(f"Database {DB_NAME} already exists.")
    except Exception as e:
        print(f"Could not create or connect to admin database to create {DB_NAME}: {e}")
        print("Please ensure the database {DB_NAME} exists and the user has connection rights.")
        # Potentially re-raise or handle as a critical failure if DB creation is mandatory here
    finally:
        if conn_admin:
            await conn_admin.close()

    # Connect to the target database to create tables
    conn = None
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await queries.drop_tables(conn) # Drop tables if they exist to start fresh
        await queries.create_notasfiscais_table(conn)
        await queries.create_itensnotafiscal_table(conn)
        await queries.create_impostos_nota_fiscal_table(conn)
        await queries.create_impostos_item_table(conn)
        print("Tables 'notasfiscais', 'itensnotafiscal', 'impostos_nota_fiscal', and 'impostos_item' created successfully.")
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise # Re-raise the exception to be caught by the endpoint handler
    finally:
        if conn:
            await conn.close()


async def ensure_tables_exist():
    """Create tables if they don't exist, WITHOUT dropping existing ones"""
    conn = None
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        # Create tables only if they don't exist (IF NOT EXISTS is in the SQL)
        await queries.create_notasfiscais_table(conn)
        await queries.create_itensnotafiscal_table(conn)
        await queries.create_impostos_nota_fiscal_table(conn)
        await queries.create_impostos_item_table(conn)
        print("✅ All tables verified/created successfully (without dropping data).")
        return {
            "message": "All tables verified/created successfully",
            "tables": ["notasfiscais", "itensnotafiscal", "impostos_nota_fiscal", "impostos_item"]
        }
    except Exception as e:
        print(f"Error ensuring tables exist: {e}")
        raise
    finally:
        if conn:
            await conn.close()

async def load_data_from_csv(cabecalho_path: str, itens_path: str):
    conn = None
    try:
        conn = await asyncpg.connect(DATABASE_URL)

        # Load notasfiscais (cabecalho)
        with open(cabecalho_path, mode='r', encoding='utf-8-sig') as csvfile: # utf-8-sig to handle BOM
            reader = csv.reader(csvfile, delimiter=',')
            next(reader)  # Skip header row
            nf_data = []
            for row in reader:
                if len(row) < 21:  # Ensure we have enough columns
                    continue
                # Use column positions based on the CSV structure
                # 0=CHAVE DE ACESSO, 1=MODELO, 2=SÉRIE, 3=NÚMERO, 4=NATUREZA DA OPERAÇÃO, 5=DATA EMISSÃO
                # 6=EVENTO MAIS RECENTE, 7=DATA/HORA EVENTO MAIS RECENTE, 8=CPF/CNPJ Emitente, 9=RAZÃO SOCIAL EMITENTE
                # 10=INSCRIÇÃO ESTADUAL EMITENTE, 11=UF EMITENTE, 12=MUNICÍPIO EMITENTE, 13=CNPJ DESTINATÁRIO
                # 14=NOME DESTINATÁRIO, 15=UF DESTINATÁRIO, 16=INDICADOR IE DESTINATÁRIO, 17=DESTINO DA OPERAÇÃO
                # 18=CONSUMIDOR FINAL, 19=PRESENÇA DO COMPRADOR, 20=VALOR NOTA FISCAL
                nf_data.append({
                    'chave_acesso': row[0] if len(row) > 0 else None,
                    'modelo': row[1] if len(row) > 1 else None,
                    'serie_nf': row[2] if len(row) > 2 else None,
                    'numero_nf': row[3] if len(row) > 3 else None,
                    'natureza_operacao': row[4] if len(row) > 4 else None,
                    'data_emissao': parse_date(row[5]) if len(row) > 5 else None,
                    'evento_mais_recente': row[6] if len(row) > 6 else None,
                    'data_hora_evento_mais_recente': parse_datetime(row[7]) if len(row) > 7 else None,
                    'cpf_cnpj_emitente': row[8] if len(row) > 8 else None,
                    'razao_social_emitente': row[9] if len(row) > 9 else None,
                    'inscricao_estadual_emitente': row[10] if len(row) > 10 else None,
                    'uf_emitente': row[11] if len(row) > 11 else None,
                    'municipio_emitente': row[12] if len(row) > 12 else None,
                    'cnpj_destinatario': row[13] if len(row) > 13 else None,
                    'nome_destinatario': row[14] if len(row) > 14 else None,
                    'uf_destinatario': row[15] if len(row) > 15 else None,
                    'indicador_ie_destinatario': row[16] if len(row) > 16 else None,
                    'destino_operacao': row[17] if len(row) > 17 else None,
                    'consumidor_final': row[18] if len(row) > 18 else None,
                    'presenca_comprador': row[19] if len(row) > 19 else None,
                    'valor_nota_fiscal': parse_decimal(row[20]) if len(row) > 20 else None
                })
            # Filter out rows where chave_acesso is None or empty, as it's a PRIMARY KEY
            nf_data_valid = [r for r in nf_data if r['chave_acesso']]
            if nf_data_valid:
                insert_sql = """
                INSERT INTO notasfiscais (
                    chave_acesso, modelo, serie_nf, numero_nf, natureza_operacao, data_emissao,
                    evento_mais_recente, data_hora_evento_mais_recente, cpf_cnpj_emitente, razao_social_emitente,
                    inscricao_estadual_emitente, uf_emitente, municipio_emitente, cnpj_destinatario,
                    nome_destinatario, uf_destinatario, indicador_ie_destinatario, destino_operacao,
                    consumidor_final, presenca_comprador, valor_nota_fiscal
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21
                )
                ON CONFLICT (chave_acesso) DO NOTHING;
                """
                for nf_record in nf_data_valid:
                    await conn.execute(insert_sql, 
                        nf_record['chave_acesso'], nf_record['modelo'], nf_record['serie_nf'], 
                        nf_record['numero_nf'], nf_record['natureza_operacao'], nf_record['data_emissao'],
                        nf_record['evento_mais_recente'], nf_record['data_hora_evento_mais_recente'], 
                        nf_record['cpf_cnpj_emitente'], nf_record['razao_social_emitente'],
                        nf_record['inscricao_estadual_emitente'], nf_record['uf_emitente'], 
                        nf_record['municipio_emitente'], nf_record['cnpj_destinatario'],
                        nf_record['nome_destinatario'], nf_record['uf_destinatario'], 
                        nf_record['indicador_ie_destinatario'], nf_record['destino_operacao'],
                        nf_record['consumidor_final'], nf_record['presenca_comprador'], 
                        nf_record['valor_nota_fiscal']
                    )
            print(f"Loaded {len(nf_data_valid)} records into notasfiscais.")

        # Load itensnotafiscal
        with open(itens_path, mode='r', encoding='utf-8-sig') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            next(reader)  # Skip header row
            item_data = []
            for row in reader:
                if len(row) < 27:  # Ensure we have enough columns
                    continue
                # Use column positions based on the CSV structure
                # 0=CHAVE DE ACESSO, 1=MODELO, 2=SÉRIE, 3=NÚMERO, 4=NATUREZA DA OPERAÇÃO, 5=DATA EMISSÃO
                # 6=CPF/CNPJ Emitente, 7=RAZÃO SOCIAL EMITENTE, 8=INSCRIÇÃO ESTADUAL EMITENTE, 9=UF EMITENTE
                # 10=MUNICÍPIO EMITENTE, 11=CNPJ DESTINATÁRIO, 12=NOME DESTINATÁRIO, 13=UF DESTINATÁRIO
                # 14=INDICADOR IE DESTINATÁRIO, 15=DESTINO DA OPERAÇÃO, 16=CONSUMIDOR FINAL, 17=PRESENÇA DO COMPRADOR
                # 18=NÚMERO PRODUTO, 19=DESCRIÇÃO DO PRODUTO/SERVIÇO, 20=CÓDIGO NCM/SH, 21=NCM/SH (TIPO DE PRODUTO)
                # 22=CFOP, 23=QUANTIDADE, 24=UNIDADE, 25=VALOR UNITÁRIO, 26=VALOR TOTAL
                item_data.append({
                    'chave_acesso_nf': row[0] if len(row) > 0 else None,
                    'modelo': row[1] if len(row) > 1 else None,
                    'serie_nf': row[2] if len(row) > 2 else None,
                    'numero_nf': row[3] if len(row) > 3 else None,
                    'natureza_operacao': row[4] if len(row) > 4 else None,
                    'data_emissao': parse_date(row[5]) if len(row) > 5 else None,
                    'cpf_cnpj_emitente': row[6] if len(row) > 6 else None,
                    'razao_social_emitente': row[7] if len(row) > 7 else None,
                    'inscricao_estadual_emitente': row[8] if len(row) > 8 else None,
                    'uf_emitente': row[9] if len(row) > 9 else None,
                    'municipio_emitente': row[10] if len(row) > 10 else None,
                    'cnpj_destinatario': row[11] if len(row) > 11 else None,
                    'nome_destinatario': row[12] if len(row) > 12 else None,
                    'uf_destinatario': row[13] if len(row) > 13 else None,
                    'indicador_ie_destinatario': row[14] if len(row) > 14 else None,
                    'destino_operacao': row[15] if len(row) > 15 else None,
                    'consumidor_final': row[16] if len(row) > 16 else None,
                    'presenca_comprador': row[17] if len(row) > 17 else None,
                    'numero_produto': parse_int(row[18]) if len(row) > 18 else None,
                    'descricao_produto': row[19] if len(row) > 19 else None,
                    'codigo_ncm_sh': row[20] if len(row) > 20 else None,
                    'ncm_sh_tipo_produto': row[21] if len(row) > 21 else None,
                    'cfop': row[22] if len(row) > 22 else None,
                    'quantidade': parse_decimal(row[23]) if len(row) > 23 else None,
                    'unidade': row[24] if len(row) > 24 else None,
                    'valor_unitario': parse_decimal(row[25]) if len(row) > 25 else None,
                    'valor_total': parse_decimal(row[26]) if len(row) > 26 else None
                })
            # Filter out rows where chave_acesso_nf is None or empty
            item_data_valid = [r for r in item_data if r['chave_acesso_nf']]
            if item_data_valid:
                insert_sql = """
                INSERT INTO itensnotafiscal (
                    chave_acesso_nf, modelo, serie_nf, numero_nf, natureza_operacao, data_emissao,
                    cpf_cnpj_emitente, razao_social_emitente, inscricao_estadual_emitente, uf_emitente,
                    municipio_emitente, cnpj_destinatario, nome_destinatario, uf_destinatario,
                    indicador_ie_destinatario, destino_operacao, consumidor_final, presenca_comprador,
                    numero_produto, descricao_produto, codigo_ncm_sh, ncm_sh_tipo_produto, cfop,
                    quantidade, unidade, valor_unitario, valor_total
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27
                );
                """
                for item_record in item_data_valid:
                    await conn.execute(insert_sql,
                        item_record['chave_acesso_nf'], item_record['modelo'], item_record['serie_nf'],
                        item_record['numero_nf'], item_record['natureza_operacao'], item_record['data_emissao'],
                        item_record['cpf_cnpj_emitente'], item_record['razao_social_emitente'],
                        item_record['inscricao_estadual_emitente'], item_record['uf_emitente'],
                        item_record['municipio_emitente'], item_record['cnpj_destinatario'],
                        item_record['nome_destinatario'], item_record['uf_destinatario'],
                        item_record['indicador_ie_destinatario'], item_record['destino_operacao'],
                        item_record['consumidor_final'], item_record['presenca_comprador'],
                        item_record['numero_produto'], item_record['descricao_produto'],
                        item_record['codigo_ncm_sh'], item_record['ncm_sh_tipo_produto'],
                        item_record['cfop'], item_record['quantidade'], item_record['unidade'],
                        item_record['valor_unitario'], item_record['valor_total']
                    )
            print(f"Loaded {len(item_data_valid)} records into itensnotafiscal.")

    except FileNotFoundError as e:
        print(f"Error: CSV file not found - {e}")
        raise
    except Exception as e:
        print(f"Error loading data from CSV: {e}")
        raise # Re-raise for endpoint to handle
    finally:
        if conn:
            await conn.close()

async def load_data_from_xml(nota_fiscal_data: dict, items_data: list, impostos_nota: dict = None, impostos_items: list = None):
    """Load data from parsed XML into database including tax information"""
    conn = None
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Insert nota fiscal
        if nota_fiscal_data and nota_fiscal_data.get('chave_acesso'):
            insert_sql = """
            INSERT INTO notasfiscais (
                chave_acesso, modelo, serie_nf, numero_nf, natureza_operacao, data_emissao,
                evento_mais_recente, data_hora_evento_mais_recente, cpf_cnpj_emitente, razao_social_emitente,
                inscricao_estadual_emitente, uf_emitente, municipio_emitente, cnpj_destinatario,
                nome_destinatario, uf_destinatario, indicador_ie_destinatario, destino_operacao,
                consumidor_final, presenca_comprador, valor_nota_fiscal, classificacao
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22
            )
            ON CONFLICT (chave_acesso) DO NOTHING;
            """
            await conn.execute(insert_sql,
                nota_fiscal_data['chave_acesso'], nota_fiscal_data['modelo'], nota_fiscal_data['serie_nf'],
                nota_fiscal_data['numero_nf'], nota_fiscal_data['natureza_operacao'], nota_fiscal_data['data_emissao'],
                nota_fiscal_data['evento_mais_recente'], nota_fiscal_data['data_hora_evento_mais_recente'],
                nota_fiscal_data['cpf_cnpj_emitente'], nota_fiscal_data['razao_social_emitente'],
                nota_fiscal_data['inscricao_estadual_emitente'], nota_fiscal_data['uf_emitente'],
                nota_fiscal_data['municipio_emitente'], nota_fiscal_data['cnpj_destinatario'],
                nota_fiscal_data['nome_destinatario'], nota_fiscal_data['uf_destinatario'],
                nota_fiscal_data['indicador_ie_destinatario'], nota_fiscal_data['destino_operacao'],
                nota_fiscal_data['consumidor_final'], nota_fiscal_data['presenca_comprador'],
                nota_fiscal_data['valor_nota_fiscal'], nota_fiscal_data.get('classificacao')
            )
            print(f"Loaded nota fiscal with chave_acesso: {nota_fiscal_data['chave_acesso']}")
        
        # Insert tax totals for nota fiscal
        if impostos_nota and impostos_nota.get('chave_acesso_nf'):
            insert_sql = """
            INSERT INTO impostos_nota_fiscal (
                chave_acesso_nf, v_bc_icms, v_icms, v_icms_deson, v_fcp_uf_dest, v_icms_uf_dest,
                v_icms_uf_remet, v_bc_st, v_st, v_ipi, v_ipi_devol, v_pis, v_cofins, v_ii,
                v_tot_trib, v_prod, v_frete, v_seg, v_desc, v_outro, v_nf
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21
            )
            ON CONFLICT (chave_acesso_nf) DO UPDATE SET
                v_bc_icms = EXCLUDED.v_bc_icms, v_icms = EXCLUDED.v_icms, v_icms_deson = EXCLUDED.v_icms_deson,
                v_fcp_uf_dest = EXCLUDED.v_fcp_uf_dest, v_icms_uf_dest = EXCLUDED.v_icms_uf_dest,
                v_icms_uf_remet = EXCLUDED.v_icms_uf_remet, v_bc_st = EXCLUDED.v_bc_st, v_st = EXCLUDED.v_st,
                v_ipi = EXCLUDED.v_ipi, v_ipi_devol = EXCLUDED.v_ipi_devol, v_pis = EXCLUDED.v_pis,
                v_cofins = EXCLUDED.v_cofins, v_ii = EXCLUDED.v_ii, v_tot_trib = EXCLUDED.v_tot_trib,
                v_prod = EXCLUDED.v_prod, v_frete = EXCLUDED.v_frete, v_seg = EXCLUDED.v_seg,
                v_desc = EXCLUDED.v_desc, v_outro = EXCLUDED.v_outro, v_nf = EXCLUDED.v_nf;
            """
            await conn.execute(insert_sql,
                impostos_nota['chave_acesso_nf'], impostos_nota.get('v_bc_icms'), impostos_nota.get('v_icms'),
                impostos_nota.get('v_icms_deson'), impostos_nota.get('v_fcp_uf_dest'), impostos_nota.get('v_icms_uf_dest'),
                impostos_nota.get('v_icms_uf_remet'), impostos_nota.get('v_bc_st'), impostos_nota.get('v_st'),
                impostos_nota.get('v_ipi'), impostos_nota.get('v_ipi_devol'), impostos_nota.get('v_pis'),
                impostos_nota.get('v_cofins'), impostos_nota.get('v_ii'), impostos_nota.get('v_tot_trib'),
                impostos_nota.get('v_prod'), impostos_nota.get('v_frete'), impostos_nota.get('v_seg'),
                impostos_nota.get('v_desc'), impostos_nota.get('v_outro'), impostos_nota.get('v_nf')
            )
            print(f"Loaded tax totals for nota fiscal: {impostos_nota['chave_acesso_nf']}")
        
        # Insert items and their tax data
        if items_data:
            insert_sql = """
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
            RETURNING id_item_nf;
            """
            
            # Map to store item_id by numero_produto for tax insertion
            item_id_map = {}
            
            for item in items_data:
                item_id = await conn.fetchval(insert_sql,
                    item['chave_acesso_nf'], item['modelo'], item['serie_nf'],
                    item['numero_nf'], item['natureza_operacao'], item['data_emissao'],
                    item['cpf_cnpj_emitente'], item['razao_social_emitente'],
                    item['inscricao_estadual_emitente'], item['uf_emitente'],
                    item['municipio_emitente'], item['cnpj_destinatario'],
                    item['nome_destinatario'], item['uf_destinatario'],
                    item['indicador_ie_destinatario'], item['destino_operacao'],
                    item['consumidor_final'], item['presenca_comprador'],
                    item['numero_produto'], item['descricao_produto'],
                    item['codigo_ncm_sh'], item['ncm_sh_tipo_produto'],
                    item['cfop'], item['quantidade'], item['unidade'],
                    item['valor_unitario'], item['valor_total']
                )
                item_id_map[item['numero_produto']] = item_id
            
            print(f"Loaded {len(items_data)} items for nota fiscal")
            
            # Insert tax data for items
            if impostos_items:
                insert_tax_sql = """
                INSERT INTO impostos_item (
                    id_item_nf, chave_acesso_nf, numero_item, v_tot_trib,
                    icms_orig, icms_cst, icms_mod_bc, icms_v_bc, icms_p_icms, icms_v_icms,
                    icms_uf_v_bc_uf_dest, icms_uf_v_bc_fcp_uf_dest, icms_uf_p_fcp_uf_dest,
                    icms_uf_p_icms_uf_dest, icms_uf_p_icms_inter, icms_uf_p_icms_inter_part,
                    icms_uf_v_fcp_uf_dest, icms_uf_v_icms_uf_dest, icms_uf_v_icms_uf_remet,
                    ipi_c_enq, ipi_cst, ipi_v_bc, ipi_p_ipi, ipi_v_ipi,
                    pis_cst, pis_v_bc, pis_p_pis, pis_v_pis,
                    cofins_cst, cofins_v_bc, cofins_p_cofins, cofins_v_cofins
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19,
                    $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31, $32
                );
                """
                
                for imp_item in impostos_items:
                    numero_item = imp_item.get('numero_item')
                    if numero_item in item_id_map:
                        id_item_nf = item_id_map[numero_item]
                        await conn.execute(insert_tax_sql,
                            id_item_nf, imp_item['chave_acesso_nf'], imp_item['numero_item'], imp_item.get('v_tot_trib'),
                            imp_item.get('icms_orig'), imp_item.get('icms_cst'), imp_item.get('icms_mod_bc'),
                            imp_item.get('icms_v_bc'), imp_item.get('icms_p_icms'), imp_item.get('icms_v_icms'),
                            imp_item.get('icms_uf_v_bc_uf_dest'), imp_item.get('icms_uf_v_bc_fcp_uf_dest'),
                            imp_item.get('icms_uf_p_fcp_uf_dest'), imp_item.get('icms_uf_p_icms_uf_dest'),
                            imp_item.get('icms_uf_p_icms_inter'), imp_item.get('icms_uf_p_icms_inter_part'),
                            imp_item.get('icms_uf_v_fcp_uf_dest'), imp_item.get('icms_uf_v_icms_uf_dest'),
                            imp_item.get('icms_uf_v_icms_uf_remet'),
                            imp_item.get('ipi_c_enq'), imp_item.get('ipi_cst'), imp_item.get('ipi_v_bc'),
                            imp_item.get('ipi_p_ipi'), imp_item.get('ipi_v_ipi'),
                            imp_item.get('pis_cst'), imp_item.get('pis_v_bc'), imp_item.get('pis_p_pis'),
                            imp_item.get('pis_v_pis'),
                            imp_item.get('cofins_cst'), imp_item.get('cofins_v_bc'), imp_item.get('cofins_p_cofins'),
                            imp_item.get('cofins_v_cofins')
                        )
                
                print(f"Loaded {len(impostos_items)} tax items for nota fiscal")
        
    except Exception as e:
        print(f"Error loading data from XML: {e}")
        raise
    finally:
        if conn:
            await conn.close()


async def get_database_statistics():
    """Get database statistics for status reporting"""
    conn = None
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        stats = await queries.get_database_stats(conn)
        
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
        
        # Get items with tax data
        items_query = """
        SELECT 
            inf.id_item_nf,
            inf.numero_produto as nitem,
            inf.descricao_produto as xprod,
            inf.codigo_ncm_sh as ncm,
            inf.cfop,
            inf.quantidade as qcom,
            inf.unidade as ucom,
            inf.valor_unitario as vuncom,
            inf.valor_total as vprod,
            inf.descricao_produto as cprod,
            -- Tax data
            ii.v_tot_trib,
            ii.icms_orig,
            ii.icms_cst,
            ii.icms_mod_bc,
            ii.icms_v_bc,
            ii.icms_p_icms,
            ii.icms_v_icms,
            ii.icms_uf_v_bc_uf_dest,
            ii.icms_uf_p_icms_uf_dest,
            ii.icms_uf_p_icms_inter,
            ii.icms_uf_v_icms_uf_dest,
            ii.ipi_cst,
            ii.ipi_v_bc,
            ii.ipi_p_ipi,
            ii.ipi_v_ipi,
            ii.pis_cst,
            ii.pis_v_bc,
            ii.pis_p_pis,
            ii.pis_v_pis,
            ii.cofins_cst,
            ii.cofins_v_bc,
            ii.cofins_p_cofins,
            ii.cofins_v_cofins
        FROM itensnotafiscal inf
        LEFT JOIN impostos_item ii ON inf.id_item_nf = ii.id_item_nf
        WHERE inf.chave_acesso_nf = $1
        ORDER BY inf.numero_produto
        """
        
        items_rows = await conn.fetch(items_query, chave_acesso)
        
        # Get nota fiscal tax totals
        impostos_nota_query = """
        SELECT 
            v_bc_icms, v_icms, v_icms_uf_dest, v_bc_st, v_st,
            v_ipi, v_pis, v_cofins, v_ii, v_tot_trib,
            v_prod, v_frete, v_seg, v_desc, v_outro, v_nf
        FROM impostos_nota_fiscal
        WHERE chave_acesso_nf = $1
        """
        
        impostos_nota_row = await conn.fetchrow(impostos_nota_query, chave_acesso)
        
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
        
        # Add tax totals to nota if available
        if impostos_nota_row:
            nota["impostos"] = {
                "v_bc_icms": float(impostos_nota_row["v_bc_icms"]) if impostos_nota_row["v_bc_icms"] else None,
                "v_icms": float(impostos_nota_row["v_icms"]) if impostos_nota_row["v_icms"] else None,
                "v_icms_uf_dest": float(impostos_nota_row["v_icms_uf_dest"]) if impostos_nota_row["v_icms_uf_dest"] else None,
                "v_bc_st": float(impostos_nota_row["v_bc_st"]) if impostos_nota_row["v_bc_st"] else None,
                "v_st": float(impostos_nota_row["v_st"]) if impostos_nota_row["v_st"] else None,
                "v_ipi": float(impostos_nota_row["v_ipi"]) if impostos_nota_row["v_ipi"] else None,
                "v_pis": float(impostos_nota_row["v_pis"]) if impostos_nota_row["v_pis"] else None,
                "v_cofins": float(impostos_nota_row["v_cofins"]) if impostos_nota_row["v_cofins"] else None,
                "v_ii": float(impostos_nota_row["v_ii"]) if impostos_nota_row["v_ii"] else None,
                "v_tot_trib": float(impostos_nota_row["v_tot_trib"]) if impostos_nota_row["v_tot_trib"] else None,
                "v_prod": float(impostos_nota_row["v_prod"]) if impostos_nota_row["v_prod"] else None,
                "v_frete": float(impostos_nota_row["v_frete"]) if impostos_nota_row["v_frete"] else None,
                "v_seg": float(impostos_nota_row["v_seg"]) if impostos_nota_row["v_seg"] else None,
                "v_desc": float(impostos_nota_row["v_desc"]) if impostos_nota_row["v_desc"] else None,
                "v_outro": float(impostos_nota_row["v_outro"]) if impostos_nota_row["v_outro"] else None,
                "v_nf": float(impostos_nota_row["v_nf"]) if impostos_nota_row["v_nf"] else None
            }
        
        # Format items with tax data
        items = []
        for item_row in items_rows:
            item = {
                "nitem": item_row["nitem"],
                "xprod": item_row["xprod"],
                "ncm": item_row["ncm"],
                "cfop": item_row["cfop"],
                "qcom": float(item_row["qcom"]) if item_row["qcom"] else 0.0,
                "ucom": item_row["ucom"],
                "vuncom": float(item_row["vuncom"]) if item_row["vuncom"] else 0.0,
                "vprod": float(item_row["vprod"]) if item_row["vprod"] else 0.0,
                "cprod": item_row["cprod"]
            }
            
            # Add tax data if available
            if item_row["icms_cst"] or item_row["pis_cst"] or item_row["cofins_cst"]:
                item["impostos"] = {
                    "v_tot_trib": float(item_row["v_tot_trib"]) if item_row["v_tot_trib"] else None,
                    "icms": {
                        "orig": item_row["icms_orig"],
                        "cst": item_row["icms_cst"],
                        "mod_bc": item_row["icms_mod_bc"],
                        "v_bc": float(item_row["icms_v_bc"]) if item_row["icms_v_bc"] else None,
                        "p_icms": float(item_row["icms_p_icms"]) if item_row["icms_p_icms"] else None,
                        "v_icms": float(item_row["icms_v_icms"]) if item_row["icms_v_icms"] else None,
                        "uf_dest": {
                            "v_bc_uf_dest": float(item_row["icms_uf_v_bc_uf_dest"]) if item_row["icms_uf_v_bc_uf_dest"] else None,
                            "p_icms_uf_dest": float(item_row["icms_uf_p_icms_uf_dest"]) if item_row["icms_uf_p_icms_uf_dest"] else None,
                            "p_icms_inter": float(item_row["icms_uf_p_icms_inter"]) if item_row["icms_uf_p_icms_inter"] else None,
                            "v_icms_uf_dest": float(item_row["icms_uf_v_icms_uf_dest"]) if item_row["icms_uf_v_icms_uf_dest"] else None
                        }
                    } if item_row["icms_cst"] else None,
                    "ipi": {
                        "cst": item_row["ipi_cst"],
                        "v_bc": float(item_row["ipi_v_bc"]) if item_row["ipi_v_bc"] else None,
                        "p_ipi": float(item_row["ipi_p_ipi"]) if item_row["ipi_p_ipi"] else None,
                        "v_ipi": float(item_row["ipi_v_ipi"]) if item_row["ipi_v_ipi"] else None
                    } if item_row["ipi_cst"] else None,
                    "pis": {
                        "cst": item_row["pis_cst"],
                        "v_bc": float(item_row["pis_v_bc"]) if item_row["pis_v_bc"] else None,
                        "p_pis": float(item_row["pis_p_pis"]) if item_row["pis_p_pis"] else None,
                        "v_pis": float(item_row["pis_v_pis"]) if item_row["pis_v_pis"] else None
                    } if item_row["pis_cst"] else None,
                    "cofins": {
                        "cst": item_row["cofins_cst"],
                        "v_bc": float(item_row["cofins_v_bc"]) if item_row["cofins_v_bc"] else None,
                        "p_cofins": float(item_row["cofins_p_cofins"]) if item_row["cofins_p_cofins"] else None,
                        "v_cofins": float(item_row["cofins_v_cofins"]) if item_row["cofins_v_cofins"] else None
                    } if item_row["cofins_cst"] else None
                }
            
            items.append(item)
        
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

async def clear_all_tables():
    """Clear all data from all tables in the database"""
    conn = None
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        tables_cleared = []
        
        # Delete in order to respect foreign key constraints
        # First, delete from tables that reference others
        # Check if table exists before trying to delete
        
        # Try to delete from impostos_item
        try:
            await conn.execute("DELETE FROM impostos_item;")
            tables_cleared.append("impostos_item")
        except asyncpg.exceptions.UndefinedTableError:
            print("Table impostos_item does not exist, skipping")
        
        # Try to delete from impostos_nota_fiscal
        try:
            await conn.execute("DELETE FROM impostos_nota_fiscal;")
            tables_cleared.append("impostos_nota_fiscal")
        except asyncpg.exceptions.UndefinedTableError:
            print("Table impostos_nota_fiscal does not exist, skipping")
        
        # Try to delete from itensnotafiscal
        try:
            await conn.execute("DELETE FROM itensnotafiscal;")
            tables_cleared.append("itensnotafiscal")
        except asyncpg.exceptions.UndefinedTableError:
            print("Table itensnotafiscal does not exist, skipping")
        
        # Try to delete from notasfiscais
        try:
            await conn.execute("DELETE FROM notasfiscais;")
            tables_cleared.append("notasfiscais")
        except asyncpg.exceptions.UndefinedTableError:
            print("Table notasfiscais does not exist, skipping")
        
        print(f"Tables cleared successfully: {tables_cleared}")
        
        return {
            "message": "All data cleared successfully",
            "tables_cleared": tables_cleared
        }
        
    except Exception as e:
        print(f"Error clearing tables: {e}")
        raise
    finally:
        if conn:
            await conn.close()

