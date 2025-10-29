# main.py
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, status
import shutil
import os
import logging
import asyncio
import asyncpg

from config import UPLOAD_DIR, DATABASE_URL
from file_utils import process_zip_file, parse_csv_to_data
from db_utils import get_database_statistics, get_all_notas_fiscais, get_nota_fiscal_by_chave, clear_all_tables, ensure_tables_exist
from xml_parser import parse_nfe_xml
from rabbitmq_client import publish_nota_fiscal

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    logger.info("Load service started successfully")

@app.get("/health")
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "load_service"}

@app.get("/status")
@app.get("/api/status")
async def status_check():
    """Status check endpoint with database statistics"""
    try:
        db_stats = await get_database_statistics()
        return {
            "status": "online",
            "service": "load_service",
            **db_stats
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return {
            "status": "online",
            "service": "load_service",
            "notas_fiscais": 0,
            "itens_nota_fiscal": 0,
            "total_records": 0,
            "total_value": 0.0,
            "last_upload": None
        }

@app.post("/upload-nfe-zip/")
@app.post("/api/upload-nfe-zip/")
async def upload_nfe_zip(file: UploadFile = File(...)):
    """
    Upload a ZIP file containing NFe CSV files (Cabecalho and Itens).
    The data will be parsed and sent to RabbitMQ queue for processing.
    """
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type. Only ZIP files are allowed.")

    temp_zip_path = os.path.join(UPLOAD_DIR, f"temp_{file.filename}")

    try:
        # Save the uploaded zip file temporarily
        with open(temp_zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Temporary ZIP file saved to {temp_zip_path}")

        # Process the zip file (extract and validate)
        cabecalho_csv_path, itens_csv_path = process_zip_file(temp_zip_path)
        logger.info(f"ZIP file processed. Cabecalho: {cabecalho_csv_path}, Itens: {itens_csv_path}")

        # Parse CSV files to data structures
        notas_fiscais_data = parse_csv_to_data(cabecalho_csv_path, itens_csv_path)
        logger.info(f"Parsed {len(notas_fiscais_data)} notas fiscais from CSV")

        # Send each nota fiscal to RabbitMQ
        published_count = 0
        failed_count = 0
        
        for nota_fiscal_data, items_data in notas_fiscais_data:
            if publish_nota_fiscal(nota_fiscal_data, items_data):
                published_count += 1
            else:
                failed_count += 1
                logger.error(f"Failed to publish nota fiscal: {nota_fiscal_data.get('chave_acesso')}")

        logger.info(f"Published {published_count} notas fiscais to RabbitMQ. Failed: {failed_count}")

        return {
            "message": f"File '{file.filename}' processed successfully",
            "notas_fiscais_processed": len(notas_fiscais_data),
            "published_to_queue": published_count,
            "failed": failed_count
        }

    except HTTPException as e:
        logger.error(f"HTTP Exception during upload: {e.detail}")
        raise e # Re-raise FastAPI HTTPExceptions
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")
    finally:
        # Clean up the temporary zip file
        if os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)
            logger.info(f"Temporary ZIP file {temp_zip_path} removed.")
        # Clean up extracted CSV files
        if 'cabecalho_csv_path' in locals() and os.path.exists(cabecalho_csv_path):
            os.remove(cabecalho_csv_path)
        if 'itens_csv_path' in locals() and os.path.exists(itens_csv_path):
            os.remove(itens_csv_path)

@app.post("/upload-nfe-xml/")
@app.post("/api/upload-nfe-xml/")
async def upload_nfe_xml(file: UploadFile = File(...)):
    """
    Upload a single NFe XML file and send it to RabbitMQ queue for processing.
    The XML file should be in the Brazilian NFe (Nota Fiscal Eletrônica) format.
    """
    if not file.filename.endswith('.xml'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid file type. Only XML files are allowed."
        )

    try:
        # Read the uploaded XML file content
        xml_content = await file.read()
        xml_string = xml_content.decode('utf-8')
        logger.info(f"XML file '{file.filename}' read successfully")

        # Parse the XML file
        try:
            nota_fiscal_data, items_data, impostos_nota, impostos_items = parse_nfe_xml(xml_string)
            logger.info(f"XML parsed successfully. Chave: {nota_fiscal_data.get('chave_acesso')}, Items: {len(items_data)}, Impostos Items: {len(impostos_items)}")
        except ValueError as e:
            logger.error(f"Error parsing XML: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error parsing XML file: {str(e)}"
            )

        # Send to RabbitMQ
        if publish_nota_fiscal(nota_fiscal_data, items_data, impostos_nota, impostos_items):
            logger.info(f"Successfully published nota fiscal to RabbitMQ: {nota_fiscal_data.get('chave_acesso')}")
            
            return {
                "message": f"File '{file.filename}' processed and sent to queue successfully",
                "chave_acesso": nota_fiscal_data.get('chave_acesso'),
                "numero_nf": nota_fiscal_data.get('numero_nf'),
                "items_count": len(items_data),
                "valor_total": nota_fiscal_data.get('valor_nota_fiscal'),
                "status": "queued"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to publish nota fiscal to RabbitMQ queue"
            )

    except HTTPException as e:
        logger.error(f"HTTP Exception during upload: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@app.get("/api/notas")
async def list_notas_fiscais():
    """
    List all notas fiscais with their basic information
    """
    try:
        notas = await get_all_notas_fiscais()
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

@app.get("/api/impostos/nota/{chave_acesso}")
async def get_impostos_nota(chave_acesso: str):
    """
    Get tax totals for a specific nota fiscal by chave_acesso
    """
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            result = await conn.fetchrow("""
                SELECT * FROM impostos_nota_fiscal
                WHERE chave_acesso_nf = $1
            """, chave_acesso)
            
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tax data not found for nota fiscal with chave_acesso '{chave_acesso}'"
                )
            
            return dict(result)
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tax data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving tax data: {str(e)}"
        )

@app.get("/api/impostos/itens/{chave_acesso}")
async def get_impostos_itens(chave_acesso: str):
    """
    Get tax data for all items of a specific nota fiscal by chave_acesso
    """
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            results = await conn.fetch("""
                SELECT ii.*, inf.numero_produto, inf.descricao_produto
                FROM impostos_item ii
                JOIN itensnotafiscal inf ON ii.id_item_nf = inf.id_item_nf
                WHERE ii.chave_acesso_nf = $1
                ORDER BY ii.numero_item
            """, chave_acesso)
            
            return [dict(row) for row in results]
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error getting item tax data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving item tax data: {str(e)}"
        )

@app.get("/api/impostos/completo/{chave_acesso}")
async def get_impostos_completo(chave_acesso: str):
    """
    Get complete tax information (totals + items) for a specific nota fiscal
    """
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            # Get tax totals
            impostos_nota = await conn.fetchrow("""
                SELECT * FROM impostos_nota_fiscal
                WHERE chave_acesso_nf = $1
            """, chave_acesso)
            
            # Get tax data for items
            impostos_itens = await conn.fetch("""
                SELECT ii.*, inf.numero_produto, inf.descricao_produto
                FROM impostos_item ii
                JOIN itensnotafiscal inf ON ii.id_item_nf = inf.id_item_nf
                WHERE ii.chave_acesso_nf = $1
                ORDER BY ii.numero_item
            """, chave_acesso)
            
            return {
                "chave_acesso": chave_acesso,
                "impostos_nota": dict(impostos_nota) if impostos_nota else None,
                "impostos_itens": [dict(row) for row in impostos_itens]
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error getting complete tax data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving complete tax data: {str(e)}"
        )

@app.delete("/api/clear-all-data")
async def clear_all_data():
    """
    Clear all data from all tables in the database.
    WARNING: This operation cannot be undone!
    """
    try:
        logger.warning("⚠️ CLEARING ALL DATA FROM DATABASE - This action was requested by user")
        result = await clear_all_tables()
        logger.info("✅ All data cleared successfully")
        return result
    except Exception as e:
        logger.error(f"Error clearing database: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing database: {str(e)}"
        )

@app.post("/api/ensure-tables")
async def ensure_tables():
    """
    Ensure all tables exist in the database, creating them if needed.
    This does NOT drop existing data.
    """
    try:
        logger.info("🔧 Ensuring all tables exist...")
        result = await ensure_tables_exist()
        logger.info("✅ All tables verified/created successfully")
        return result
    except Exception as e:
        logger.error(f"Error ensuring tables exist: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ensuring tables exist: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 