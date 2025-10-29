# main.py
import uvicorn
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import logging
import threading
import requests
import json
import re

from config import SERVICE_PORT, TAXES_WEBHOOK_URL
from db_utils import get_nota_fiscal_by_chave, get_database_statistics, save_analise_fiscal, update_analise_fiscal_processamento, get_analise_fiscal_by_chave
from rabbitmq_client import publish_to_taxes_queue
from rabbitmq_worker import start_consumer

app = FastAPI(title="Taxes Service", version="1.0.0")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaxesCalculationRequest(BaseModel):
    chave_acesso: str


class AnaliseFiscalRequest(BaseModel):
    texto: str


class UpdateProcessamentoRequest(BaseModel):
    chave_acesso: str
    em_processamento: bool


@app.on_event("startup")
async def startup_event():
    logger.info("Taxes service started successfully")
    
    # Start RabbitMQ consumer in a separate thread
    consumer_thread = threading.Thread(target=start_consumer, daemon=True)
    consumer_thread.start()
    logger.info("RabbitMQ consumer worker started in background")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "taxes_service"}


@app.get("/status")
async def status_check():
    """Status check endpoint with database statistics"""
    try:
        db_stats = await get_database_statistics()
        return {
            "status": "online",
            "service": "taxes_service",
            "version": "1.0.0",
            **db_stats
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return {
            "status": "online",
            "service": "taxes_service",
            "version": "1.0.0",
            "notas_fiscais": 0,
            "itens_nota_fiscal": 0
        }


@app.post("/calculate-taxes/")
async def calculate_taxes(request: TaxesCalculationRequest):
    """
    Retrieve a nota fiscal from database by chave_acesso and send it to 
    the taxes calculation queue.
    
    Args:
        request: TaxesCalculationRequest with chave_acesso
        
    Returns:
        Success message with nota fiscal summary
    """
    chave_acesso = request.chave_acesso.strip()
    
    if not chave_acesso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="chave_acesso is required and cannot be empty"
        )
    
    logger.info(f"📋 Received taxes calculation request for: {chave_acesso}")
    
    try:
        # Step 1: Retrieve nota fiscal from database
        logger.info("🔍 Step 1: Retrieving nota fiscal from database...")
        nota_fiscal_data = await get_nota_fiscal_by_chave(chave_acesso)
        
        if not nota_fiscal_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nota fiscal not found with chave_acesso: {chave_acesso}"
            )
        
        nota_fiscal = nota_fiscal_data['nota_fiscal']
        items = nota_fiscal_data['items']
        
        logger.info(f"✅ Found nota fiscal: {nota_fiscal.get('numero_nf')}")
        logger.info(f"   Emitente: {nota_fiscal.get('razao_social_emitente')}")
        logger.info(f"   Destinatário: {nota_fiscal.get('nome_destinatario')}")
        logger.info(f"   Items: {len(items)}")
        logger.info(f"   Valor Total: R$ {nota_fiscal.get('valor_nota_fiscal', 0):.2f}")
        
        # Step 2: Send to N8N webhook for taxes processing (async - don't wait for response)
        logger.info(f"🔄 Step 2: Sending to N8N taxes webhook: {TAXES_WEBHOOK_URL}")
        webhook_url = TAXES_WEBHOOK_URL
        
        # Enviar webhook de forma assíncrona (não aguardar resposta)
        # O processamento pode levar vários minutos, então não esperamos
        def send_webhook_async():
            try:
                logger.info("📡 Enviando webhook para N8N (assíncrono)...")
                webhook_response = requests.post(
                    webhook_url,
                    json=nota_fiscal_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=300  # 5 minutos de timeout
                )
                webhook_response.raise_for_status()
                webhook_result = webhook_response.json()
                
                # Print webhook response
                print("=" * 80)
                print("🎯 RESPOSTA DO WEBHOOK N8N - TAXES:")
                print("=" * 80)
                print(json.dumps(webhook_result, indent=2, ensure_ascii=False))
                print("=" * 80)
                
                logger.info(f"✅ Webhook response received: {webhook_response.status_code}")
                
            except requests.exceptions.Timeout:
                logger.warning("⏱️  Timeout calling N8N webhook (5min)")
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"🔌 Connection error calling N8N webhook: {e}")
            except Exception as e:
                logger.warning(f"⚠️  Error calling N8N webhook: {e}")
        
        # Iniciar thread para enviar webhook sem bloquear
        webhook_thread = threading.Thread(target=send_webhook_async, daemon=True)
        webhook_thread.start()
        
        webhook_result = {"status": "processing", "message": "Webhook enviado para processamento assíncrono"}
        
        # Step 3: Publish to taxes calculation queue
        logger.info("📤 Step 3: Publishing to taxes calculation queue...")
        success = publish_to_taxes_queue(nota_fiscal_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to publish nota fiscal to taxes calculation queue"
            )
        
        logger.info("✅ Successfully sent to taxes calculation queue")
        
        return {
            "message": "Nota fiscal processed successfully",
            "chave_acesso": chave_acesso,
            "numero_nf": nota_fiscal.get('numero_nf'),
            "razao_social_emitente": nota_fiscal.get('razao_social_emitente'),
            "nome_destinatario": nota_fiscal.get('nome_destinatario'),
            "items_count": len(items),
            "valor_total": nota_fiscal.get('valor_nota_fiscal'),
            "classificacao": nota_fiscal.get('classificacao'),
            "webhook_response": webhook_result,
            "queue_published": success
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


def clean_json_text(text: str) -> str:
    """Clean markdown code blocks and other formatting from JSON text"""
    # Remove markdown code blocks (```json ... ``` or ``` ... ```)
    text = re.sub(r'^```json\s*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'^```\s*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n?```$', '', text, flags=re.MULTILINE)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


@app.post("/analise_fiscal")
async def save_analise_fiscal_endpoint(request: AnaliseFiscalRequest):
    """
    Save fiscal analysis data
    Receives a raw text (possibly with markdown) containing JSON data
    """
    try:
        logger.info("Received analise_fiscal data")
        
        # Clean the text
        cleaned_text = clean_json_text(request.texto)
        logger.info(f"Cleaned text: {cleaned_text[:200]}...")
        
        # Parse JSON
        try:
            dados_json = json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON format: {str(e)}"
            )
        
        # Extract chave_acesso from JSON
        analise = dados_json.get("analise_fiscal", {})
        info_nfe = analise.get("info_nfe", {})
        chave_acesso = info_nfe.get("chave_acesso")
        
        if not chave_acesso:
            logger.error("chave_acesso not found in JSON")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="chave_acesso not found in JSON data"
            )
        
        logger.info(f"Saving analise fiscal for chave_acesso: {chave_acesso}")
        
        # Save to database with em_processamento=False (dados incluídos com sucesso)
        result_id = await save_analise_fiscal(chave_acesso, dados_json, em_processamento=False)
        
        logger.info(f"Successfully saved analise fiscal with id: {result_id}, em_processamento set to False")
        
        return {
            "success": True,
            "id": result_id,
            "chave_acesso": chave_acesso,
            "message": "Análise fiscal salva com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving analise fiscal: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving analise fiscal: {str(e)}"
        )


@app.put("/analise_fiscal/processamento")
async def update_processamento(request: UpdateProcessamentoRequest):
    """
    Update em_processamento field for a fiscal analysis.
    If the analise_fiscal record doesn't exist but the nota fiscal does, creates a new analise_fiscal record.
    
    Args:
        request: UpdateProcessamentoRequest with chave_acesso and em_processamento
        
    Returns:
        Updated or created record information
    """
    try:
        logger.info(f"Updating em_processamento for chave_acesso: {request.chave_acesso} to {request.em_processamento}")
        
        result = await update_analise_fiscal_processamento(
            request.chave_acesso, 
            request.em_processamento
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update/create em_processamento for chave_acesso: {request.chave_acesso}"
            )
        
        # Check if there was an error (nota fiscal not found)
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("message", "Nota fiscal não encontrada")
            )
        
        # Check if record was created or updated
        was_created = result.get("created", False)
        action = "criado" if was_created else "atualizado"
        
        logger.info(f"Successfully {'created' if was_created else 'updated'} em_processamento")
        
        return {
            "success": True,
            "message": f"Registro de análise fiscal {action} com sucesso",
            "action": "created" if was_created else "updated",
            **{k: v for k, v in result.items() if k != "created"}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating/creating em_processamento: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating/creating em_processamento: {str(e)}"
        )


@app.get("/analise_fiscal/{chave_acesso}")
async def get_analise_fiscal(chave_acesso: str):
    """
    Get fiscal analysis by chave_acesso
    
    Args:
        chave_acesso: Access key of the nota fiscal
        
    Returns:
        Fiscal analysis data or None if not found
    """
    try:
        logger.info(f"Fetching analise fiscal for chave_acesso: {chave_acesso}")
        
        analise = await get_analise_fiscal_by_chave(chave_acesso)
        
        if not analise:
            return {
                "found": False,
                "message": "Análise fiscal não encontrada"
            }
        
        logger.info(f"Successfully retrieved analise fiscal")
        
        return {
            "found": True,
            "analise": analise
        }
        
    except Exception as e:
        logger.error(f"Error getting analise fiscal: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting analise fiscal: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)

