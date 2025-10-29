# main.py
import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import logging

from config import SERVICE_PORT
from db_utils import get_all_notas_fiscais, get_nota_fiscal_by_chave, get_database_statistics

app = FastAPI(title="Site Service", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup_event():
    logger.info("Site service started successfully")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "site_service"}


@app.get("/api/notas")
async def list_notas_fiscais():
    """
    List all notas fiscais with their basic information
    """
    try:
        logger.info("Fetching all notas fiscais")
        notas = await get_all_notas_fiscais()
        logger.info(f"Found {len(notas)} notas fiscais")
        return {"notas": notas}
    except Exception as e:
        logger.error(f"Error listing notas fiscais: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving notas fiscais: {str(e)}"
        )


@app.get("/api/notas/{chave_acesso}")
async def get_nota_fiscal_details(chave_acesso: str):
    """
    Get detailed information about a specific nota fiscal including its items
    """
    try:
        logger.info(f"Fetching nota fiscal with chave: {chave_acesso}")
        result = await get_nota_fiscal_by_chave(chave_acesso)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nota fiscal with chave_acesso '{chave_acesso}' not found"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting nota fiscal details: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving nota fiscal details: {str(e)}"
        )


@app.get("/api/statistics")
async def get_statistics():
    """
    Get database statistics
    """
    try:
        logger.info("Fetching database statistics")
        stats = await get_database_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving statistics: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)

