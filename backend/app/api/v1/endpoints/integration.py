"""
Bambu Print Suite Integration API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from app.services.bambu_client import BambuSuiteClient
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Pydantic models for requests/responses
class PrintJobRequest(BaseModel):
    """Request to create a print job"""
    production_order_id: int
    production_order_code: str
    product_sku: str
    product_name: str
    quantity: int
    gcode_file: Optional[str] = None
    material_type: str
    priority: str = "normal"
    estimated_time: Optional[int] = None

class PrintJobResponse(BaseModel):
    """Response from print job creation"""
    id: str
    printer_id: str
    status: str
    created_at: datetime

class PrinterStatus(BaseModel):
    """Printer status information"""
    id: str
    name: str
    model: str
    status: str
    current_job_id: Optional[str] = None
    progress_percent: Optional[float] = None
    remaining_time: Optional[int] = None

class MaterialCheckRequest(BaseModel):
    """Request to check material availability"""
    material_type: str
    required_quantity: float  # in kg

class MaterialCheckResponse(BaseModel):
    """Material availability response"""
    available: bool
    on_hand: float
    allocated: float
    locations: List[dict]

class QuoteConversionRequest(BaseModel):
    """Request to convert quote to sales order"""
    quote_id: str
    customer_id: int

class QuoteConversionResponse(BaseModel):
    """Quote conversion response"""
    sales_order_id: int
    production_order_id: int
    print_job_id: str

# Dependency to get Bambu Suite client
def get_bambu_client() -> BambuSuiteClient:
    """Get Bambu Suite API client"""
    return BambuSuiteClient(
        api_url=settings.BAMBU_SUITE_API_URL,
        api_key=settings.BAMBU_SUITE_API_KEY
    )

@router.post("/print-jobs", response_model=PrintJobResponse)
async def create_print_job(
    request: PrintJobRequest,
    bambu_client: BambuSuiteClient = Depends(get_bambu_client)
):
    """
    Create a print job in Bambu Print Suite from an ERP production order

    This endpoint is called when a production order is created in the ERP
    and needs to be sent to the print farm for execution.
    """
    try:
        logger.info(f"Creating print job for production order {request.production_order_code}")

        # Create print job in Bambu Suite
        job = await bambu_client.create_print_job(
            production_order_id=request.production_order_id,
            product_sku=request.product_sku,
            product_name=request.product_name,
            quantity=request.quantity,
            gcode_file=request.gcode_file,
            material_type=request.material_type,
            priority=request.priority
        )

        logger.info(f"Print job created: {job['id']} assigned to printer {job['printer_id']}")

        return PrintJobResponse(
            id=job['id'],
            printer_id=job['printer_id'],
            status=job['status'],
            created_at=job['created_at']
        )

    except Exception as e:
        logger.error(f"Failed to create print job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/printer-status", response_model=List[PrinterStatus])
async def get_printer_status(
    bambu_client: BambuSuiteClient = Depends(get_bambu_client)
):
    """
    Get real-time status of all printers from Bambu Print Suite

    This endpoint provides live printer status for the ERP dashboard,
    showing which printers are available, busy, or experiencing issues.
    """
    try:
        printers = await bambu_client.get_all_printer_status()

        return [
            PrinterStatus(
                id=p['id'],
                name=p['name'],
                model=p['model'],
                status=p['status'],
                current_job_id=p.get('current_job_id'),
                progress_percent=p.get('progress_percent'),
                remaining_time=p.get('remaining_time')
            )
            for p in printers
        ]

    except Exception as e:
        logger.error(f"Failed to get printer status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/material-check", response_model=MaterialCheckResponse)
async def check_material_availability(request: MaterialCheckRequest):
    """
    Check if material is available in ERP inventory

    This endpoint is called by Bambu Print Suite before starting a print
    to ensure sufficient material is available.
    """
    try:
        # TODO: Query ERP inventory database
        # For now, return mock data
        return MaterialCheckResponse(
            available=True,
            on_hand=5.0,
            allocated=1.0,
            locations=[
                {"location": "PRODUCTION_AREA", "quantity": 3.0},
                {"location": "WAREHOUSE_A", "quantity": 2.0}
            ]
        )

    except Exception as e:
        logger.error(f"Failed to check material availability: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quotes/convert", response_model=QuoteConversionResponse)
async def convert_quote_to_order(
    request: QuoteConversionRequest,
    bambu_client: BambuSuiteClient = Depends(get_bambu_client)
):
    """
    Convert an approved Bambu Suite quote to an ERP sales order

    This endpoint handles the complete flow:
    1. Get quote from Bambu Suite
    2. Create customer (if new)
    3. Create sales order in ERP
    4. Create production order
    5. Create print job
    """
    try:
        logger.info(f"Converting quote {request.quote_id} to sales order")

        # Get quote from Bambu Suite
        quote = await bambu_client.get_quote(request.quote_id)

        # TODO: Create sales order in ERP database
        # TODO: Create production order
        # TODO: Create print job

        # For now, return mock data
        return QuoteConversionResponse(
            sales_order_id=1001,
            production_order_id=2001,
            print_job_id="PJ-001"
        )

    except Exception as e:
        logger.error(f"Failed to convert quote to order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sync-status")
async def get_sync_status(
    bambu_client: BambuSuiteClient = Depends(get_bambu_client)
):
    """
    Get integration sync status

    Shows connectivity and health of the integration between
    ERP and Bambu Print Suite.
    """
    try:
        # Test connection to Bambu Suite
        is_connected = await bambu_client.test_connection()

        return {
            "status": "connected" if is_connected else "disconnected",
            "bambu_suite_url": settings.BAMBU_SUITE_API_URL,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
