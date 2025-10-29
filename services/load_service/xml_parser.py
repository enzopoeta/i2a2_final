# xml_parser.py
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Tuple

# Namespace da NFe
NS = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

def parse_nfe_xml(xml_content: str) -> Tuple[Dict, List[Dict]]:
    """
    Parse NFe XML and extract data for notasfiscais and itensnotafiscal tables.
    
    Returns:
        Tuple[Dict, List[Dict], Dict, List[Dict]]: (nota_fiscal_data, items_data, impostos_nota, impostos_items)
    """
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML format: {e}")
    
    # Find infNFe element
    inf_nfe = root.find('.//nfe:infNFe', NS)
    if inf_nfe is None:
        raise ValueError("Invalid NFe XML: infNFe element not found")
    
    # Extract chave_acesso from Id attribute
    chave_acesso = inf_nfe.get('Id', '').replace('NFe', '')
    if not chave_acesso:
        raise ValueError("Invalid NFe XML: chave de acesso not found")
    
    # Parse nota fiscal header data
    nota_fiscal_data = extract_nota_fiscal_data(inf_nfe, chave_acesso)
    
    # Parse items data
    items_data = extract_items_data(inf_nfe, chave_acesso, nota_fiscal_data)
    
    # Parse impostos da nota
    impostos_nota = extract_impostos_nota(inf_nfe, chave_acesso)
    
    # Parse impostos dos itens
    impostos_items = extract_impostos_items(inf_nfe, chave_acesso)
    
    return nota_fiscal_data, items_data, impostos_nota, impostos_items


def extract_nota_fiscal_data(inf_nfe: ET.Element, chave_acesso: str) -> Dict:
    """Extract header data from NFe XML"""
    
    # IDE - Identification data
    ide = inf_nfe.find('nfe:ide', NS)
    
    # EMIT - Emitter data
    emit = inf_nfe.find('nfe:emit', NS)
    
    # DEST - Recipient data
    dest = inf_nfe.find('nfe:dest', NS)
    
    # TOTAL - Total values
    total = inf_nfe.find('nfe:total/nfe:ICMSTot', NS)
    
    # Extract modelo
    modelo_code = get_text(ide, 'nfe:mod', NS)
    modelo_map = {
        '55': '55 - NF-E EMITIDA EM SUBSTITUIÇÃO AO MODELO 1 OU 1A',
        '65': '65 - NFC-E'
    }
    modelo = modelo_map.get(modelo_code, modelo_code)
    
    # Extract data_emissao
    dh_emi = get_text(ide, 'nfe:dhEmi', NS)
    data_emissao = parse_nfe_date(dh_emi)
    
    # Extract emitente data
    cnpj_emit = get_text(emit, 'nfe:CNPJ', NS)
    cpf_emit = get_text(emit, 'nfe:CPF', NS)
    cpf_cnpj_emitente = cnpj_emit if cnpj_emit else cpf_emit
    
    razao_social_emitente = get_text(emit, 'nfe:xNome', NS)
    inscricao_estadual_emitente = get_text(emit, 'nfe:IE', NS)
    
    # Extract emitente address
    ender_emit = emit.find('nfe:enderEmit', NS) if emit is not None else None
    uf_emitente = get_text(ender_emit, 'nfe:UF', NS)
    municipio_emitente = get_text(ender_emit, 'nfe:xMun', NS)
    
    # Extract destinatario data
    cnpj_dest = get_text(dest, 'nfe:CNPJ', NS) if dest is not None else None
    nome_destinatario = get_text(dest, 'nfe:xNome', NS) if dest is not None else None
    
    # Extract destinatario address
    ender_dest = dest.find('nfe:enderDest', NS) if dest is not None else None
    uf_destinatario = get_text(ender_dest, 'nfe:UF', NS) if ender_dest is not None else None
    
    # Extract indicador IE destinatario
    ind_ie_dest = get_text(dest, 'nfe:indIEDest', NS) if dest is not None else None
    indicador_ie_map = {
        '1': '1 - Contribuinte ICMS',
        '2': '2 - Contribuinte isento de Inscrição no cadastro de Contribuintes',
        '9': '9 - Não Contribuinte'
    }
    indicador_ie_destinatario = indicador_ie_map.get(ind_ie_dest, ind_ie_dest)
    
    # Extract destino operacao
    id_dest = get_text(ide, 'nfe:idDest', NS)
    destino_operacao_map = {
        '1': '1 - Interna',
        '2': '2 - Interestadual',
        '3': '3 - Exterior'
    }
    destino_operacao = destino_operacao_map.get(id_dest, id_dest)
    
    # Extract consumidor final
    ind_final = get_text(ide, 'nfe:indFinal', NS)
    consumidor_final_map = {
        '0': '0 - Não',
        '1': '1 - Sim'
    }
    consumidor_final = consumidor_final_map.get(ind_final, ind_final)
    
    # Extract presenca comprador
    ind_pres = get_text(ide, 'nfe:indPres', NS)
    presenca_comprador_map = {
        '0': '0 - Não se aplica',
        '1': '1 - Operação presencial',
        '2': '2 - Operação não presencial, pela Internet',
        '3': '3 - Operação não presencial, Teleatendimento',
        '4': '4 - NFC-e em operação com entrega a domicílio',
        '5': '5 - Operação presencial, fora do estabelecimento',
        '9': '9 - Operação não presencial, outros'
    }
    presenca_comprador = presenca_comprador_map.get(ind_pres, ind_pres)
    
    # Extract valor nota fiscal
    valor_nota_fiscal = get_decimal(total, 'nfe:vNF', NS)
    
    nota_fiscal_data = {
        'chave_acesso': chave_acesso,
        'modelo': modelo,
        'serie_nf': get_text(ide, 'nfe:serie', NS),
        'numero_nf': get_text(ide, 'nfe:nNF', NS),
        'natureza_operacao': get_text(ide, 'nfe:natOp', NS),
        'data_emissao': data_emissao,
        'evento_mais_recente': None,  # XML doesn't have this info - comes from eventos externos
        'data_hora_evento_mais_recente': None,  # XML doesn't have this info
        'cpf_cnpj_emitente': cpf_cnpj_emitente,
        'razao_social_emitente': razao_social_emitente,
        'inscricao_estadual_emitente': inscricao_estadual_emitente,
        'uf_emitente': uf_emitente,
        'municipio_emitente': municipio_emitente,
        'cnpj_destinatario': cnpj_dest,
        'nome_destinatario': nome_destinatario,
        'uf_destinatario': uf_destinatario,
        'indicador_ie_destinatario': indicador_ie_destinatario,
        'destino_operacao': destino_operacao,
        'consumidor_final': consumidor_final,
        'presenca_comprador': presenca_comprador,
        'valor_nota_fiscal': valor_nota_fiscal,
        'classificacao': None  # Will be set later by classification service
    }
    
    return nota_fiscal_data


def extract_items_data(inf_nfe: ET.Element, chave_acesso: str, nota_fiscal_data: Dict) -> List[Dict]:
    """Extract items data from NFe XML"""
    
    items = []
    
    # Find all det (detail) elements
    det_elements = inf_nfe.findall('nfe:det', NS)
    
    for det in det_elements:
        prod = det.find('nfe:prod', NS)
        if prod is None:
            continue
        
        # Extract numero_produto from nItem attribute
        numero_produto = det.get('nItem')
        
        # Extract product data
        descricao_produto = get_text(prod, 'nfe:xProd', NS)
        codigo_ncm_sh = get_text(prod, 'nfe:NCM', NS)
        cfop = get_text(prod, 'nfe:CFOP', NS)
        quantidade = get_decimal(prod, 'nfe:qCom', NS)
        unidade = get_text(prod, 'nfe:uCom', NS)
        valor_unitario = get_decimal(prod, 'nfe:vUnCom', NS)
        valor_total = get_decimal(prod, 'nfe:vProd', NS)
        
        item_data = {
            'chave_acesso_nf': chave_acesso,
            'modelo': nota_fiscal_data.get('modelo'),
            'serie_nf': nota_fiscal_data.get('serie_nf'),
            'numero_nf': nota_fiscal_data.get('numero_nf'),
            'natureza_operacao': nota_fiscal_data.get('natureza_operacao'),
            'data_emissao': nota_fiscal_data.get('data_emissao'),
            'cpf_cnpj_emitente': nota_fiscal_data.get('cpf_cnpj_emitente'),
            'razao_social_emitente': nota_fiscal_data.get('razao_social_emitente'),
            'inscricao_estadual_emitente': nota_fiscal_data.get('inscricao_estadual_emitente'),
            'uf_emitente': nota_fiscal_data.get('uf_emitente'),
            'municipio_emitente': nota_fiscal_data.get('municipio_emitente'),
            'cnpj_destinatario': nota_fiscal_data.get('cnpj_destinatario'),
            'nome_destinatario': nota_fiscal_data.get('nome_destinatario'),
            'uf_destinatario': nota_fiscal_data.get('uf_destinatario'),
            'indicador_ie_destinatario': nota_fiscal_data.get('indicador_ie_destinatario'),
            'destino_operacao': nota_fiscal_data.get('destino_operacao'),
            'consumidor_final': nota_fiscal_data.get('consumidor_final'),
            'presenca_comprador': nota_fiscal_data.get('presenca_comprador'),
            'numero_produto': int(numero_produto) if numero_produto else None,
            'descricao_produto': descricao_produto,
            'codigo_ncm_sh': codigo_ncm_sh,
            'ncm_sh_tipo_produto': None,  # XML doesn't have this description
            'cfop': cfop,
            'quantidade': quantidade,
            'unidade': unidade,
            'valor_unitario': valor_unitario,
            'valor_total': valor_total
        }
        
        items.append(item_data)
    
    return items


def get_text(element: ET.Element, path: str, namespace: dict) -> str:
    """Safely extract text from XML element"""
    if element is None:
        return None
    child = element.find(path, namespace)
    return child.text if child is not None and child.text else None


def get_decimal(element: ET.Element, path: str, namespace: dict) -> float:
    """Safely extract decimal value from XML element"""
    text = get_text(element, path, namespace)
    if text:
        try:
            return float(text)
        except ValueError:
            return None
    return None


def get_percentage_as_decimal(element: ET.Element, path: str, namespace: dict) -> float:
    """
    Safely extract percentage value from XML element and convert to decimal.
    Example: 18.0000 (18%) becomes 0.18
    """
    text = get_text(element, path, namespace)
    if text:
        try:
            return float(text) / 100.0
        except ValueError:
            return None
    return None


def parse_nfe_date(date_str: str) -> datetime:
    """Parse NFe date format (ISO 8601 with timezone)"""
    if not date_str:
        return None
    
    try:
        # NFe dates are in format: 2025-05-19T00:00:00-03:00
        # Remove timezone info for database compatibility
        date_part = date_str.split('T')[0]
        return datetime.strptime(date_part, '%Y-%m-%d').date()
    except (ValueError, IndexError):
        return None


def extract_impostos_nota(inf_nfe: ET.Element, chave_acesso: str) -> Dict:
    """Extract tax totals from NFe XML"""
    
    # Find total/ICMSTot element
    icms_tot = inf_nfe.find('nfe:total/nfe:ICMSTot', NS)
    if icms_tot is None:
        return None
    
    impostos_data = {
        'chave_acesso_nf': chave_acesso,
        # ICMS
        'v_bc_icms': get_decimal(icms_tot, 'nfe:vBC', NS),
        'v_icms': get_decimal(icms_tot, 'nfe:vICMS', NS),
        'v_icms_deson': get_decimal(icms_tot, 'nfe:vICMSDeson', NS),
        'v_fcp_uf_dest': get_decimal(icms_tot, 'nfe:vFCPUFDest', NS),
        'v_icms_uf_dest': get_decimal(icms_tot, 'nfe:vICMSUFDest', NS),
        'v_icms_uf_remet': get_decimal(icms_tot, 'nfe:vICMSUFRemet', NS),
        # Substituição Tributária
        'v_bc_st': get_decimal(icms_tot, 'nfe:vBCST', NS),
        'v_st': get_decimal(icms_tot, 'nfe:vST', NS),
        # IPI
        'v_ipi': get_decimal(icms_tot, 'nfe:vIPI', NS),
        'v_ipi_devol': get_decimal(icms_tot, 'nfe:vIPIDevol', NS),
        # PIS/COFINS
        'v_pis': get_decimal(icms_tot, 'nfe:vPIS', NS),
        'v_cofins': get_decimal(icms_tot, 'nfe:vCOFINS', NS),
        # Importação
        'v_ii': get_decimal(icms_tot, 'nfe:vII', NS),
        # Total tributos
        'v_tot_trib': get_decimal(icms_tot, 'nfe:vTotTrib', NS),
        # Valores da nota
        'v_prod': get_decimal(icms_tot, 'nfe:vProd', NS),
        'v_frete': get_decimal(icms_tot, 'nfe:vFrete', NS),
        'v_seg': get_decimal(icms_tot, 'nfe:vSeg', NS),
        'v_desc': get_decimal(icms_tot, 'nfe:vDesc', NS),
        'v_outro': get_decimal(icms_tot, 'nfe:vOutro', NS),
        'v_nf': get_decimal(icms_tot, 'nfe:vNF', NS)
    }
    
    return impostos_data


def extract_impostos_items(inf_nfe: ET.Element, chave_acesso: str) -> List[Dict]:
    """Extract tax data from each item in NFe XML"""
    
    impostos_items = []
    
    # Find all det (detail) elements
    det_elements = inf_nfe.findall('nfe:det', NS)
    
    for idx, det in enumerate(det_elements, start=1):
        numero_item = det.get('nItem')
        imposto = det.find('nfe:imposto', NS)
        
        if imposto is None:
            continue
        
        # Extract vTotTrib
        v_tot_trib = get_decimal(imposto, 'nfe:vTotTrib', NS)
        
        # Extract ICMS data
        icms = imposto.find('nfe:ICMS', NS)
        icms_data = extract_icms_item(icms) if icms is not None else {}
        
        # Extract ICMSUFDest (DIFAL)
        icms_uf_dest = imposto.find('nfe:ICMSUFDest', NS)
        icms_uf_data = extract_icms_uf_dest(icms_uf_dest) if icms_uf_dest is not None else {}
        
        # Extract IPI data
        ipi = imposto.find('nfe:IPI', NS)
        ipi_data = extract_ipi_item(ipi) if ipi is not None else {}
        
        # Extract PIS data
        pis = imposto.find('nfe:PIS', NS)
        pis_data = extract_pis_item(pis) if pis is not None else {}
        
        # Extract COFINS data
        cofins = imposto.find('nfe:COFINS', NS)
        cofins_data = extract_cofins_item(cofins) if cofins is not None else {}
        
        # Combine all tax data
        # Use idx as fallback if numero_item is not provided
        item_impostos = {
            'chave_acesso_nf': chave_acesso,
            'numero_item': int(numero_item) if numero_item else idx,
            'v_tot_trib': v_tot_trib,
            **icms_data,
            **icms_uf_data,
            **ipi_data,
            **pis_data,
            **cofins_data
        }
        
        impostos_items.append(item_impostos)
    
    return impostos_items


def extract_icms_item(icms: ET.Element) -> Dict:
    """Extract ICMS data from item"""
    # ICMS can have multiple types (ICMS00, ICMS10, ICMS20, etc.)
    # We'll try to find the first one
    icms_types = ['ICMS00', 'ICMS10', 'ICMS20', 'ICMS30', 'ICMS40', 'ICMS51', 'ICMS60', 'ICMS70', 'ICMS90',
                  'ICMSSN101', 'ICMSSN102', 'ICMSSN201', 'ICMSSN202', 'ICMSSN500', 'ICMSSN900']
    
    icms_element = None
    for icms_type in icms_types:
        icms_element = icms.find(f'nfe:{icms_type}', NS)
        if icms_element is not None:
            break
    
    if icms_element is None:
        return {}
    
    return {
        'icms_orig': get_int(icms_element, 'nfe:orig', NS),
        'icms_cst': get_text(icms_element, 'nfe:CST', NS) or get_text(icms_element, 'nfe:CSOSN', NS),
        'icms_mod_bc': get_int(icms_element, 'nfe:modBC', NS),
        'icms_v_bc': get_decimal(icms_element, 'nfe:vBC', NS),
        'icms_p_icms': get_percentage_as_decimal(icms_element, 'nfe:pICMS', NS),
        'icms_v_icms': get_decimal(icms_element, 'nfe:vICMS', NS)
    }


def extract_icms_uf_dest(icms_uf: ET.Element) -> Dict:
    """Extract ICMS UF Destino (DIFAL) data"""
    return {
        'icms_uf_v_bc_uf_dest': get_decimal(icms_uf, 'nfe:vBCUFDest', NS),
        'icms_uf_v_bc_fcp_uf_dest': get_decimal(icms_uf, 'nfe:vBCFCPUFDest', NS),
        'icms_uf_p_fcp_uf_dest': get_percentage_as_decimal(icms_uf, 'nfe:pFCPUFDest', NS),
        'icms_uf_p_icms_uf_dest': get_percentage_as_decimal(icms_uf, 'nfe:pICMSUFDest', NS),
        'icms_uf_p_icms_inter': get_percentage_as_decimal(icms_uf, 'nfe:pICMSInter', NS),
        'icms_uf_p_icms_inter_part': get_percentage_as_decimal(icms_uf, 'nfe:pICMSInterPart', NS),
        'icms_uf_v_fcp_uf_dest': get_decimal(icms_uf, 'nfe:vFCPUFDest', NS),
        'icms_uf_v_icms_uf_dest': get_decimal(icms_uf, 'nfe:vICMSUFDest', NS),
        'icms_uf_v_icms_uf_remet': get_decimal(icms_uf, 'nfe:vICMSUFRemet', NS)
    }


def extract_ipi_item(ipi: ET.Element) -> Dict:
    """Extract IPI data from item"""
    # Get cEnq
    c_enq = get_text(ipi, 'nfe:cEnq', NS)
    
    # IPI can be IPITrib or IPINT
    ipi_trib = ipi.find('nfe:IPITrib', NS)
    ipi_nt = ipi.find('nfe:IPINT', NS)
    
    ipi_element = ipi_trib if ipi_trib is not None else ipi_nt
    
    if ipi_element is None:
        return {'ipi_c_enq': c_enq}
    
    return {
        'ipi_c_enq': c_enq,
        'ipi_cst': get_text(ipi_element, 'nfe:CST', NS),
        'ipi_v_bc': get_decimal(ipi_element, 'nfe:vBC', NS),
        'ipi_p_ipi': get_percentage_as_decimal(ipi_element, 'nfe:pIPI', NS),
        'ipi_v_ipi': get_decimal(ipi_element, 'nfe:vIPI', NS)
    }


def extract_pis_item(pis: ET.Element) -> Dict:
    """Extract PIS data from item"""
    # PIS can be PISAliq, PISNT, PISOutr, etc.
    pis_types = ['PISAliq', 'PISQtde', 'PISNT', 'PISOutr']
    
    pis_element = None
    for pis_type in pis_types:
        pis_element = pis.find(f'nfe:{pis_type}', NS)
        if pis_element is not None:
            break
    
    if pis_element is None:
        return {}
    
    return {
        'pis_cst': get_text(pis_element, 'nfe:CST', NS),
        'pis_v_bc': get_decimal(pis_element, 'nfe:vBC', NS),
        'pis_p_pis': get_percentage_as_decimal(pis_element, 'nfe:pPIS', NS),
        'pis_v_pis': get_decimal(pis_element, 'nfe:vPIS', NS)
    }


def extract_cofins_item(cofins: ET.Element) -> Dict:
    """Extract COFINS data from item"""
    # COFINS can be COFINSAliq, COFINSNT, COFINSOutr, etc.
    cofins_types = ['COFINSAliq', 'COFINSQtde', 'COFINSNT', 'COFINSOutr']
    
    cofins_element = None
    for cofins_type in cofins_types:
        cofins_element = cofins.find(f'nfe:{cofins_type}', NS)
        if cofins_element is not None:
            break
    
    if cofins_element is None:
        return {}
    
    return {
        'cofins_cst': get_text(cofins_element, 'nfe:CST', NS),
        'cofins_v_bc': get_decimal(cofins_element, 'nfe:vBC', NS),
        'cofins_p_cofins': get_percentage_as_decimal(cofins_element, 'nfe:pCOFINS', NS),
        'cofins_v_cofins': get_decimal(cofins_element, 'nfe:vCOFINS', NS)
    }


def get_int(element: ET.Element, path: str, namespace: dict) -> int:
    """Safely extract integer value from XML element"""
    text = get_text(element, path, namespace)
    if text:
        try:
            return int(text)
        except ValueError:
            return None
    return None

