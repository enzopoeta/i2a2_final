# main.py
import uvicorn
from fastapi import FastAPI, HTTPException, status, Query, Body
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
import requests
import random

from config import SERVICE_PORT, CNPJ_API_URLS
from redis_client import (
    test_redis_connection,
    get_or_generate_ncm_data,
    get_or_generate_icms_data
)

app = FastAPI(title="Gov Service", version="1.0.0")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Modelos Pydantic para batch requests
class NCMBatchRequest(BaseModel):
    ncms: List[str] = Field(..., description="Lista de códigos NCM com 8 dígitos")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ncms": ["84713012", "84733090", "85171231"]
            }
        }


class ICMSBatchItem(BaseModel):
    uf_origem: str = Field(..., pattern="^[A-Z]{2}$", description="UF de origem")
    uf_destino: str = Field(..., pattern="^[A-Z]{2}$", description="UF de destino")
    ncm: str = Field(..., pattern="^[0-9]{8}$", description="Código NCM")
    tipo_operacao: Optional[str] = Field("VENDA_PRODUTO", description="Tipo de operação")
    
    class Config:
        json_schema_extra = {
            "example": {
                "uf_origem": "SC",
                "uf_destino": "SP",
                "ncm": "84713012",
                "tipo_operacao": "VENDA_PRODUTO"
            }
        }


class ICMSBatchRequest(BaseModel):
    consultas: List[ICMSBatchItem] = Field(..., description="Lista de consultas ICMS")
    
    class Config:
        json_schema_extra = {
            "example": {
                "consultas": [
                    {
                        "uf_origem": "SC",
                        "uf_destino": "SP",
                        "ncm": "84713012"
                    },
                    {
                        "uf_origem": "SP",
                        "uf_destino": "RJ",
                        "ncm": "84733090"
                    }
                ]
            }
        }


@app.on_event("startup")
async def startup_event():
    logger.info("Gov service started successfully")
    
    # Test Redis connection
    if test_redis_connection():
        logger.info("✅ Redis connection successful")
    else:
        logger.warning("⚠️  Redis connection failed - service will continue but caching won't work")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_ok = test_redis_connection()
    return {
        "status": "healthy",
        "service": "gov_service",
        "redis": "connected" if redis_ok else "disconnected"
    }


@app.get("/cnpjinfo/{cnpj}")
async def get_cnpj_info(cnpj: str):
    """Get CNPJ information from external APIs"""
    cleaned_cnpj = ''.join(filter(str.isdigit, cnpj))
    if not cleaned_cnpj or len(cleaned_cnpj) not in [14]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CNPJ inválido. Deve conter 14 dígitos numéricos."
        )

    logger.info(f"Consultando CNPJ: {cleaned_cnpj}")

    api_urls = list(CNPJ_API_URLS)
    random.shuffle(api_urls)

    for url_template in api_urls:
        url = url_template.format(cnpj=cleaned_cnpj)
        logger.info(f"Tentando API: {url}")
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Dados obtidos com sucesso da API: {url}")
            return {"success": True, "cnpj": cleaned_cnpj, "source": url, "data": data}
        except requests.exceptions.RequestException as e:
            logger.warning(f"Falha ao consultar {url}: {e}")
            continue
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Não foi possível obter informações do CNPJ de nenhuma das APIs disponíveis."
    )


@app.get("/ncm/consultar")
async def consultar_ncm(
    ncm: str = Query(..., description="Código NCM com 8 dígitos", regex="^[0-9]{8}$")
):
    """
    Consulta informações tributárias de um NCM
    
    Retorna:
    - Descrição do NCM
    - Regime de PIS/COFINS (Monofásico, Alíquota Zero, etc)
    - Alíquotas padrão de PIS e COFINS
    - Alíquota de IPI
    
    Valores são gerados de forma consistente e persistidos no Redis
    """
    try:
        logger.info(f"Consultando NCM: {ncm}")
        data = get_or_generate_ncm_data(ncm)
        logger.info(f"NCM {ncm} consultado com sucesso")
        return data
    except Exception as e:
        logger.error(f"Erro ao consultar NCM {ncm}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar NCM: {str(e)}"
        )


@app.get("/icms/consultar_aliquotas")
async def consultar_aliquotas_icms(
    uf_origem: str = Query(..., description="UF de origem (sigla)", regex="^[A-Z]{2}$"),
    uf_destino: str = Query(..., description="UF de destino (sigla)", regex="^[A-Z]{2}$"),
    ncm: str = Query(..., description="Código NCM com 8 dígitos", regex="^[0-9]{8}$"),
    tipo_operacao: str = Query(
        "VENDA_PRODUTO",
        description="Tipo de operação",
        regex="^(VENDA_PRODUTO|PRESTACAO_SERVICO|DEVOLUCAO)$"
    ),
    data_referencia: str = Query(
        None,
        description="Data de referência no formato YYYY-MM-DD",
        regex="^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    )
):
    """
    Consulta alíquotas e regras de ICMS
    
    Retorna:
    - Alíquotas internas de origem e destino
    - Alíquota interestadual
    - Informações sobre ST (Substituição Tributária)
    - MVA (Margem de Valor Agregado) se ST aplicável
    - Regras de DIFAL (Diferencial de Alíquota)
    - FCP (Fundo de Combate à Pobreza)
    
    Valores são gerados de forma consistente e persistidos no Redis
    """
    try:
        logger.info(f"Consultando ICMS: {uf_origem} -> {uf_destino}, NCM: {ncm}")
        data = get_or_generate_icms_data(uf_origem, uf_destino, ncm)
        logger.info(f"ICMS consultado com sucesso para {uf_origem}->{uf_destino}")
        return data
    except Exception as e:
        logger.error(f"Erro ao consultar ICMS: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar ICMS: {str(e)}"
        )


@app.post("/ncm/consultar_lote")
async def consultar_ncm_lote(request: NCMBatchRequest):
    """
    Consulta informações tributárias de múltiplos NCMs em uma única requisição
    
    Retorna uma lista com os dados de cada NCM no mesmo formato da consulta individual
    
    Exemplo de uso:
    ```json
    {
        "ncms": ["84713012", "84733090", "85171231"]
    }
    ```
    
    Retorno:
    ```json
    {
        "total": 3,
        "sucesso": 3,
        "falhas": 0,
        "resultados": [
            { "ncm": "84713012", "descricao": "...", ... },
            { "ncm": "84733090", "descricao": "...", ... },
            { "ncm": "85171231", "descricao": "...", ... }
        ],
        "erros": []
    }
    ```
    """
    logger.info(f"Consultando lote de {len(request.ncms)} NCMs")
    
    resultados = []
    erros = []
    
    for ncm in request.ncms:
        try:
            # Validar formato
            if not (ncm and len(ncm) == 8 and ncm.isdigit()):
                erros.append({
                    "ncm": ncm,
                    "erro": "NCM deve ter exatamente 8 dígitos numéricos"
                })
                continue
            
            data = get_or_generate_ncm_data(ncm)
            resultados.append(data)
            
        except Exception as e:
            logger.error(f"Erro ao consultar NCM {ncm}: {e}")
            erros.append({
                "ncm": ncm,
                "erro": str(e)
            })
    
    response = {
        "total": len(request.ncms),
        "sucesso": len(resultados),
        "falhas": len(erros),
        "resultados": resultados,
        "erros": erros
    }
    
    logger.info(f"Lote NCM concluído: {len(resultados)} sucessos, {len(erros)} falhas")
    return response


@app.post("/icms/consultar_lote")
async def consultar_icms_lote(request: ICMSBatchRequest):
    """
    Consulta alíquotas de ICMS para múltiplas operações em uma única requisição
    
    Retorna uma lista com os dados de cada consulta no mesmo formato da consulta individual
    
    Exemplo de uso:
    ```json
    {
        "consultas": [
            {
                "uf_origem": "SC",
                "uf_destino": "SP",
                "ncm": "84713012",
                "tipo_operacao": "VENDA_PRODUTO"
            },
            {
                "uf_origem": "SP",
                "uf_destino": "RJ",
                "ncm": "84733090"
            }
        ]
    }
    ```
    
    Retorno:
    ```json
    {
        "total": 2,
        "sucesso": 2,
        "falhas": 0,
        "resultados": [
            { "ncm": "84713012", "uf_origem": "SC", ... },
            { "ncm": "84733090", "uf_origem": "SP", ... }
        ],
        "erros": []
    }
    ```
    """
    logger.info(f"Consultando lote de {len(request.consultas)} operações ICMS")
    
    resultados = []
    erros = []
    
    for item in request.consultas:
        try:
            uf_origem = item.uf_origem.upper()
            uf_destino = item.uf_destino.upper()
            ncm = item.ncm
            
            # Validações
            if not (uf_origem and len(uf_origem) == 2 and uf_origem.isalpha()):
                erros.append({
                    "consulta": item.dict(),
                    "erro": "UF de origem inválida"
                })
                continue
                
            if not (uf_destino and len(uf_destino) == 2 and uf_destino.isalpha()):
                erros.append({
                    "consulta": item.dict(),
                    "erro": "UF de destino inválida"
                })
                continue
                
            if not (ncm and len(ncm) == 8 and ncm.isdigit()):
                erros.append({
                    "consulta": item.dict(),
                    "erro": "NCM deve ter exatamente 8 dígitos numéricos"
                })
                continue
            
            data = get_or_generate_icms_data(uf_origem, uf_destino, ncm)
            resultados.append(data)
            
        except Exception as e:
            logger.error(f"Erro ao consultar ICMS: {e}")
            erros.append({
                "consulta": item.dict(),
                "erro": str(e)
            })
    
    response = {
        "total": len(request.consultas),
        "sucesso": len(resultados),
        "falhas": len(erros),
        "resultados": resultados,
        "erros": erros
    }
    
    logger.info(f"Lote ICMS concluído: {len(resultados)} sucessos, {len(erros)} falhas")
    return response


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
