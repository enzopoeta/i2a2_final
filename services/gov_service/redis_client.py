# redis_client.py
import redis
import json
import random
import hashlib
import requests
from config import REDIS_HOST, REDIS_PORT, REDIS_DB

# Create Redis client
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True
)


def generate_consistent_seed(key: str) -> int:
    """Generate a consistent seed from a string key"""
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (10 ** 8)


def fetch_ncm_description(ncm: str) -> str:
    """Fetch NCM description from BrasilAPI"""
    try:
        url = f"https://brasilapi.com.br/api/ncm/v1/{ncm}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('descricao', f"Produto classificado no NCM {ncm}")
    except Exception as e:
        print(f"Error fetching NCM description from BrasilAPI: {e}")
        return f"Produto classificado no NCM {ncm}"


def get_or_generate_ncm_data(ncm: str) -> dict:
    """Get or generate NCM data with consistent values"""
    cache_key = f"ncm:{ncm}"
    
    # Try to get from cache
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    
    # Fetch real NCM description from BrasilAPI
    descricao = fetch_ncm_description(ncm)
    
    # Generate new data with consistent random values based on NCM
    seed = generate_consistent_seed(ncm)
    random.seed(seed)
    
    # Possible regimes
    regimes = ["Nenhum", "Monofasico", "Aliquota_Zero", "Substituicao_Tributaria"]
    
    data = {
        "ncm": ncm,
        "descricao": descricao,
        "tributacao_pis_cofins": {
            "regime_especial": random.choice(regimes),
            "aliquota_pis_padrao": round(random.uniform(0.65, 2.1), 2),
            "aliquota_cofins_padrao": round(random.uniform(3.0, 8.6), 2)
        },
        "aliquota_ipi_padrao": round(random.choice([0, 5, 10, 15, 20, 25]), 1)
    }
    
    # Cache for 30 days
    redis_client.setex(cache_key, 30 * 24 * 60 * 60, json.dumps(data))
    
    return data


def get_or_generate_icms_data(uf_origem: str, uf_destino: str, ncm: str) -> dict:
    """Get or generate ICMS data with consistent values"""
    cache_key = f"icms:{uf_origem}:{uf_destino}:{ncm}"
    
    # Try to get from cache
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    
    # Generate new data with consistent random values
    seed = generate_consistent_seed(cache_key)
    random.seed(seed)
    
    # Alíquotas internas típicas por UF (valores aproximados reais)
    aliquotas_internas = {
        "AC": 17.0, "AL": 18.0, "AP": 18.0, "AM": 18.0, "BA": 18.0,
        "CE": 18.0, "DF": 18.0, "ES": 17.0, "GO": 17.0, "MA": 18.0,
        "MT": 17.0, "MS": 17.0, "MG": 18.0, "PA": 17.0, "PB": 18.0,
        "PR": 18.0, "PE": 18.0, "PI": 18.0, "RJ": 20.0, "RN": 18.0,
        "RS": 18.0, "RO": 17.5, "RR": 17.0, "SC": 17.0, "SP": 18.0,
        "SE": 18.0, "TO": 18.0
    }
    
    aliquota_interna_origem = aliquotas_internas.get(uf_origem.upper(), 17.0)
    aliquota_interna_destino = aliquotas_internas.get(uf_destino.upper(), 18.0)
    
    # Alíquota interestadual (normalmente 7% ou 12% dependendo das UFs)
    if uf_origem.upper() in ["SP", "RJ", "MG", "PR", "SC", "RS", "ES"]:
        aliquota_interestadual = 12.0 if uf_destino.upper() in ["SP", "RJ", "MG", "PR", "SC", "RS", "ES"] else 7.0
    else:
        aliquota_interestadual = 7.0 if uf_destino.upper() in ["SP", "RJ", "MG", "PR", "SC", "RS", "ES"] else 12.0
    
    # ST aplicável em ~40% dos casos
    icms_st_aplicavel = random.random() < 0.4
    
    # Regimes possíveis
    regimes = ["TRIBUTADO_NORMAL", "SUBSTITUICAO_TRIBUTARIA", "ISENTO", "REDUCAO_BASE_CALCULO"]
    
    # FCP (Fundo de Combate à Pobreza) - alguns estados têm
    aliquota_fcp = random.choice([0, 1.0, 2.0]) if random.random() < 0.3 else 0
    
    # DIFAL (diferencial de alíquota)
    difal_aplicavel = uf_origem != uf_destino
    
    # Partilha DIFAL (valores atuais - desde 2023 é 100% destino, mas vou usar variável)
    partilha_origem = 0 if difal_aplicavel else 0
    partilha_destino = 100 if difal_aplicavel else 0
    
    data = {
        "ncm": ncm,
        "uf_origem": uf_origem.upper(),
        "uf_destino": uf_destino.upper(),
        "aliquota_interna_origem": aliquota_interna_origem,
        "aliquota_interna_destino": aliquota_interna_destino,
        "aliquota_interestadual": aliquota_interestadual,
        "icms_st_aplicavel": icms_st_aplicavel,
        "mva_original_icms_st": round(random.uniform(20.0, 50.0), 2) if icms_st_aplicavel else 0,
        "regime_icms_para_ncm": regimes[0] if not icms_st_aplicavel else regimes[1],
        "aliquota_fcp_destino": aliquota_fcp,
        "aliquota_difal_origem": aliquota_interna_origem if difal_aplicavel else 0,
        "aliquota_difal_destino": aliquota_interna_destino if difal_aplicavel else 0,
        "partilha_difal_origem": partilha_origem,
        "partilha_difal_destino": partilha_destino
    }
    
    # Cache for 30 days
    redis_client.setex(cache_key, 30 * 24 * 60 * 60, json.dumps(data))
    
    return data


def test_redis_connection() -> bool:
    """Test Redis connection"""
    try:
        redis_client.ping()
        return True
    except Exception as e:
        print(f"Redis connection error: {e}")
        return False

