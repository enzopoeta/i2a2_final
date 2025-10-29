# main.py
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, status
import logging
import json
import threading

from config import SERVICE_PORT
from db_utils import insert_nota_fiscal_from_json, get_database_statistics
from rabbitmq_worker import start_consumer

app = FastAPI(title="Onboarding Service", version="1.0.0")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup_event():
    logger.info("Onboarding service started successfully")
    
    # Start RabbitMQ consumer in a separate thread
    consumer_thread = threading.Thread(target=start_consumer, daemon=True)
    consumer_thread.start()
    logger.info("RabbitMQ consumer worker started in background")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "onboarding_service"}


@app.get("/status")
async def status_check():
    """Status check endpoint with database statistics"""
    try:
        db_stats = await get_database_statistics()
        return {
            "status": "online",
            "service": "onboarding_service",
            "version": "1.0.0",
            **db_stats
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return {
            "status": "online",
            "service": "onboarding_service",
            "version": "1.0.0",
            "notas_fiscais": 0,
            "itens_nota_fiscal": 0,
            "total_records": 0,
            "total_value": 0.0,
            "last_upload": None,
            "notas_classificadas": 0
        }


@app.post("/insert-nota-fiscal/")
async def insert_nota_fiscal(file: UploadFile = File(...)):
    """
    Insert a nota fiscal into the database from a JSON file.
    
    The JSON file should contain:
    {
        "nota_fiscal": { ... nota fiscal data ... },
        "items": [ ... list of items ... ]
    }
    """
    if not file.filename.endswith('.json'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JSON files are allowed."
        )
    
    try:
        # Read and parse JSON content
        content = await file.read()
        data = json.loads(content.decode('utf-8'))
        
        logger.info(f"Received JSON file: {file.filename}")
        
        # Validate JSON structure
        if 'nota_fiscal' not in data or 'items' not in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON structure. Expected 'nota_fiscal' and 'items' keys."
            )
        
        nota_fiscal_data = data['nota_fiscal']
        items_data = data['items']
        
        # Validate chave_acesso
        if not nota_fiscal_data.get('chave_acesso'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required field 'chave_acesso' in nota_fiscal."
            )
        
        logger.info(f"Processing nota fiscal: {nota_fiscal_data.get('chave_acesso')}")
        
        # Insert into database
        success = await insert_nota_fiscal_from_json(nota_fiscal_data, items_data)
        
        if success:
            return {
                "message": "Nota fiscal inserted successfully",
                "chave_acesso": nota_fiscal_data.get('chave_acesso'),
                "numero_nf": nota_fiscal_data.get('numero_nf'),
                "items_count": len(items_data),
                "valor_total": nota_fiscal_data.get('valor_nota_fiscal'),
                "classificacao": nota_fiscal_data.get('classificacao')
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to insert nota fiscal into database"
            )
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON format: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)

