"""
Print Jobs API Endpoints

These endpoints are called BY Bambu Print Suite to update
the ERP system with print job status changes.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from app.db.session import get_db
from app.models.print_job import PrintJob
from app.models.production_order import ProductionOrder

router = APIRouter()
logger = logging.getLogger(__name__)

class PrintJobStatusUpdate(BaseModel):
    """Print job status update from Bambu Suite"""
    status: str
    progress: Optional[float] = None
    current_layer: Optional[int] = None
    total_layers: Optional[int] = None
    remaining_time: Optional[int] = None

class PrintJobCompletion(BaseModel):
    """Print job completion data"""
    actual_time_minutes: int
    actual_material_grams: float
    variance_percent: float
    completed_at: str

class PrintJobResponse(BaseModel):
    """Print job response"""
    id: int
    production_order_id: Optional[int]
    printer_id: Optional[int]
    status: str
    priority: str
    gcode_file: Optional[str] = None
    estimated_time_minutes: Optional[int] = None
    actual_time_minutes: Optional[int] = None
    estimated_material_grams: Optional[float] = None
    actual_material_grams: Optional[float] = None
    variance_percent: Optional[float] = None
    queued_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PrintJobListResponse(BaseModel):
    """Print job list response"""
    total: int
    items: List[PrintJobResponse]

@router.patch("/{job_id}")
async def update_print_job_status(
    job_id: int,
    update: PrintJobStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Update print job status

    Called by Bambu Print Suite when job status changes
    (queued -> running -> paused -> completed/failed)
    """
    try:
        logger.info(f"Updating print job {job_id}: {update.status}")

        # Find print job by ID
        print_job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
        if not print_job:
            raise HTTPException(status_code=404, detail=f"Print job {job_id} not found")

        # Update status
        print_job.status = update.status

        # Update timestamps based on status
        if update.status == 'printing' and not print_job.started_at:
            print_job.started_at = datetime.utcnow()

        if update.status in ['completed', 'failed'] and not print_job.finished_at:
            print_job.finished_at = datetime.utcnow()

        # Update production order status if print job started
        if update.status == 'printing':
            production_order = db.query(ProductionOrder).filter(
                ProductionOrder.id == print_job.production_order_id
            ).first()
            if production_order and production_order.status != 'in_progress':
                production_order.status = 'in_progress'
                production_order.start_date = datetime.utcnow()

        db.commit()

        return {
            "job_id": job_id,
            "status": update.status,
            "updated_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update print job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{job_id}/complete")
async def complete_print_job(
    job_id: str,
    completion: PrintJobCompletion,
    db: Session = Depends(get_db)
):
    """
    Mark print job as complete with actual metrics

    Called by Bambu Print Suite when a print finishes.
    Updates the ERP with actual time, material, and cost data.
    """
    try:
        logger.info(f"Completing print job {job_id}")

        # Find print job by ID
        if not job_id.isdigit():
            raise HTTPException(status_code=400, detail="Invalid job ID format")

        print_job = db.query(PrintJob).filter(PrintJob.id == int(job_id)).first()
        if not print_job:
            raise HTTPException(status_code=404, detail=f"Print job {job_id} not found")

        # Update print job with actual metrics
        print_job.status = 'completed'
        print_job.actual_time_minutes = completion.actual_time_minutes
        print_job.actual_material_grams = completion.actual_material_grams
        print_job.finished_at = datetime.fromisoformat(completion.completed_at)

        # Calculate variance
        if print_job.estimated_time_minutes and print_job.actual_time_minutes:
            variance = ((completion.actual_time_minutes - print_job.estimated_time_minutes) /
                       print_job.estimated_time_minutes) * 100
            print_job.variance_percent = variance
        elif print_job.estimated_material_grams:
            variance = ((completion.actual_material_grams - float(print_job.estimated_material_grams)) /
                       float(print_job.estimated_material_grams)) * 100
            print_job.variance_percent = variance

        # Calculate actual cost (rough estimate: $0.02 per gram + $0.10 per minute machine time)
        material_cost = completion.actual_material_grams * 0.02
        machine_cost = completion.actual_time_minutes * 0.10
        actual_cost = material_cost + machine_cost

        # Update production order
        production_order = db.query(ProductionOrder).filter(
            ProductionOrder.id == print_job.production_order_id
        ).first()

        if production_order:
            production_order.status = 'completed'
            production_order.finish_date = datetime.utcnow()
            production_order.actual_time_minutes = completion.actual_time_minutes
            production_order.actual_cost = actual_cost

        # TODO: Create inventory transaction for material consumption
        # This will be implemented when we update inventory endpoints

        db.commit()

        logger.info(f"Print job {job_id} completed successfully")

        return {
            "job_id": job_id,
            "status": "completed",
            "completed_at": completion.completed_at,
            "actual_cost": float(actual_cost)
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to complete print job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{job_id}", response_model=PrintJobResponse)
async def get_print_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Get print job details"""
    try:
        print_job = db.query(PrintJob).filter(PrintJob.id == job_id).first()

        if not print_job:
            raise HTTPException(status_code=404, detail=f"Print job {job_id} not found")

        return PrintJobResponse.from_orm(print_job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get print job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=PrintJobListResponse)
async def list_print_jobs(
    status: Optional[str] = None,
    production_order_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List print jobs with optional filtering

    - **status**: Filter by status (queued, printing, paused, completed, failed, cancelled)
    - **production_order_id**: Filter by production order ID
    - **limit**: Max results (default: 50)
    - **offset**: Pagination offset (default: 0)
    """
    try:
        # Build query
        query = db.query(PrintJob)

        # Apply filters
        if status:
            query = query.filter(PrintJob.status == status)

        if production_order_id:
            query = query.filter(PrintJob.production_order_id == production_order_id)

        # Get total count
        total = query.count()

        # Get paginated results
        print_jobs = query.order_by(PrintJob.created_at.desc()).offset(offset).limit(limit).all()

        return PrintJobListResponse(
            total=total,
            items=[PrintJobResponse.from_orm(pj) for pj in print_jobs]
        )

    except Exception as e:
        logger.error(f"Failed to list print jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
