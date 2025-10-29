import zipfile
import os
import shutil
import re
import csv
from typing import Tuple, Dict, List
from datetime import datetime
from fastapi import HTTPException, status

from config import UPLOAD_DIR

CABECALHO_SUFFIX = "_NFs_Cabecalho.csv"
ITENS_SUFFIX = "_NFs_Itens.csv" # Corrected from _Nfs_Itens.csv to _NFs_Itens.csv based on user query

def ensure_upload_dir_exists():
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

def clean_upload_dir():
    """Clean up previous uploads in the upload directory"""
    if os.path.exists(UPLOAD_DIR):
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')

def process_zip_file(file_path: str) -> tuple[str, str]:
    # Only ensure directory exists, don't clean it
    ensure_upload_dir_exists()
    extracted_files = []
    cabecalho_file = None
    itens_file = None

    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            # Check for invalid characters in filenames within the zip
            for member_name in zip_ref.namelist():
                if '..' in member_name or member_name.startswith('/'):
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Zip file contains invalid or malicious file paths.")
            
            zip_ref.extractall(UPLOAD_DIR)
            # Get only the extracted files, not including the original zip file
            all_files = [os.path.join(UPLOAD_DIR, f) for f in os.listdir(UPLOAD_DIR) if os.path.isfile(os.path.join(UPLOAD_DIR, f))]
            # Filter out the original zip file from the list
            extracted_files = [f for f in all_files if not f.endswith('.zip')]
            
    except zipfile.BadZipFile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ZIP file.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing ZIP file: {e}")

    if len(extracted_files) != 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail=f"Expected 2 files in the ZIP, but found {len(extracted_files)}.")

    for f_path in extracted_files:
        filename = os.path.basename(f_path)
        if filename.endswith(CABECALHO_SUFFIX):
            if cabecalho_file:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Multiple Cabecalho files found.")
            cabecalho_file = f_path
        elif filename.endswith(ITENS_SUFFIX):
            if itens_file:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Multiple Itens files found.")
            itens_file = f_path
        else:
            # This check is a bit redundant given the exact match logic, but good for robustness
            # or if suffix matching becomes more complex.
            # For now, if it doesn't match either, it's an unexpected file.
            pass # Let the later checks for None handle missing specific files

    if not cabecalho_file or not itens_file:
        missing = []
        if not cabecalho_file: missing.append("Cabecalho file (e.g., *" + CABECALHO_SUFFIX + ")")
        if not itens_file: missing.append("Itens file (e.g., *" + ITENS_SUFFIX + ")")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail=f"Missing required files: {', '.join(missing)}.")

    # Check if files are empty
    if os.path.getsize(cabecalho_file) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cabecalho file is empty.")
    if os.path.getsize(itens_file) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Itens file is empty.")

    return cabecalho_file, itens_file


def parse_date(date_str):
    """Parse date from CSV format"""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def parse_datetime(datetime_str):
    """Parse datetime from CSV format"""
    if not datetime_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue
    return None


def parse_decimal(value_str, default=None):
    """Parse decimal value from CSV"""
    if not value_str:
        return default
    try:
        return float(str(value_str).replace(',', '.'))
    except ValueError:
        return default


def parse_int(value_str, default=None):
    """Parse integer value from CSV"""
    if not value_str:
        return default
    try:
        return int(value_str)
    except ValueError:
        return default


def parse_csv_to_data(cabecalho_path: str, itens_path: str) -> List[Tuple[Dict, List[Dict]]]:
    """
    Parse CSV files and return list of (nota_fiscal_data, items_data) tuples.
    Each tuple represents one nota fiscal with its items.
    
    Args:
        cabecalho_path: Path to the cabecalho CSV file
        itens_path: Path to the itens CSV file
        
    Returns:
        List of tuples (nota_fiscal_data, items_data)
    """
    # Read cabecalho (notas fiscais)
    notas_fiscais = {}
    
    with open(cabecalho_path, mode='r', encoding='utf-8-sig') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)  # Skip header
        
        for row in reader:
            if len(row) < 21:
                continue
                
            chave_acesso = row[0] if len(row) > 0 else None
            if not chave_acesso:
                continue
                
            nota_fiscal_data = {
                'chave_acesso': chave_acesso,
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
                'valor_nota_fiscal': parse_decimal(row[20]) if len(row) > 20 else None,
                'classificacao': None  # Will be set later by classification service
            }
            
            notas_fiscais[chave_acesso] = {
                'nota_fiscal': nota_fiscal_data,
                'items': []
            }
    
    # Read itens
    with open(itens_path, mode='r', encoding='utf-8-sig') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)  # Skip header
        
        for row in reader:
            if len(row) < 27:
                continue
                
            chave_acesso_nf = row[0] if len(row) > 0 else None
            if not chave_acesso_nf or chave_acesso_nf not in notas_fiscais:
                continue
                
            item_data = {
                'chave_acesso_nf': chave_acesso_nf,
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
            }
            
            notas_fiscais[chave_acesso_nf]['items'].append(item_data)
    
    # Convert to list of tuples
    result = [(nf['nota_fiscal'], nf['items']) for nf in notas_fiscais.values()]
    
    return result 