"""
Quote management endpoints

Handles quote requests, file uploads, and workflow management
"""
from datetime import datetime, timedelta
from typing import List, Optional, Annotated
from decimal import Decimal

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Form,
)
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.session import get_db
from app.models.user import User
from app.models.quote import Quote, QuoteFile, QuoteMaterial
from app.schemas.quote import (
    QuoteCreate,
    QuoteResponse,
    QuoteListResponse,
    QuoteFileResponse,
    QuoteUpdateStatus,
    QuoteAccept,
    PortalQuoteCreate,
    PortalQuoteResponse,
    PortalAcceptQuote,
    PortalSubmitForReview,
)
from app.api.v1.endpoints.auth import get_current_user
from app.services.file_storage import file_storage
from app.services.bambu_client import BambuSuiteClient
from app.services.bom_service import auto_create_product_and_bom
from app.core.config import settings

router = APIRouter(prefix="/quotes", tags=["Quotes"])

# Initialize Bambu Suite client
bambu_client = BambuSuiteClient(
    api_url=settings.BAMBU_SUITE_API_URL,
    api_key=settings.BAMBU_SUITE_API_KEY
)

# Quote expiration period
QUOTE_EXPIRATION_DAYS = 7


# ============================================================================
# ENDPOINT: Upload File and Create Quote
# ============================================================================

@router.post("/upload", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
async def upload_quote_file(
    file: UploadFile = File(..., description="3D model file (.3mf or .stl)"),
    product_name: Optional[str] = Form(None, max_length=255),
    quantity: int = Form(1, ge=1, le=1000),
    material_type: str = Form(..., max_length=50),
    color: Optional[str] = Form(None, max_length=30),
    finish: str = Form("standard", max_length=50),
    rush_level: str = Form("standard", max_length=20),
    customer_notes: Optional[str] = Form(None, max_length=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload 3D model file and create quote request

    This endpoint:
    1. Validates file format (.3mf or .stl) and size (<100MB)
    2. Saves file to local storage with GCS backup
    3. Creates Quote and QuoteFile records
    4. Calls Bambu Suite for pricing (future)
    5. Applies auto-approval logic

    Returns:
        Quote with pricing and approval status
    """
    # Validate file before upload
    is_valid, error_message = file_storage.validate_file(file)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

    # Save file to storage
    try:
        file_metadata = await file_storage.save_file(
            file=file,
            user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    # Get pricing from Bambu Suite (with fallback to calculated pricing)
    try:
        quote_data = await bambu_client.generate_quote(
            file_path=file_metadata['file_path'],
            material_type=material_type,
            quantity=quantity,
            finish=finish,
            rush_level=rush_level
        )

        material_grams = quote_data['material_grams']
        print_time_hours = quote_data['print_time_hours']
        unit_price = quote_data['unit_price']
        total_price = quote_data['total_price']
        dimensions_x = quote_data['dimensions_x']
        dimensions_y = quote_data['dimensions_y']
        dimensions_z = quote_data['dimensions_z']

    except Exception as e:
        # If pricing fails completely, return error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate quote: {str(e)}"
        )

    # Generate quote number
    year = datetime.utcnow().year
    last_quote = (
        db.query(Quote)
        .filter(Quote.quote_number.like(f"Q-{year}-%"))
        .order_by(desc(Quote.quote_number))
        .first()
    )

    if last_quote:
        last_num = int(last_quote.quote_number.split("-")[2])
        next_num = last_num + 1
    else:
        next_num = 1

    quote_number = f"Q-{year}-{next_num:03d}"

    # Calculate expiration date
    expires_at = datetime.utcnow() + timedelta(days=QUOTE_EXPIRATION_DAYS)

    # Create Quote record
    quote = Quote(
        user_id=current_user.id,
        quote_number=quote_number,
        product_name=product_name,
        quantity=quantity,
        material_type=material_type.upper(),
        color=color.upper() if color else None,
        finish=finish.lower(),
        material_grams=material_grams,
        print_time_hours=print_time_hours,
        unit_price=unit_price,
        total_price=total_price,
        file_format=file_metadata['file_format'],
        file_size_bytes=file_metadata['file_size_bytes'],
        dimensions_x=dimensions_x,
        dimensions_y=dimensions_y,
        dimensions_z=dimensions_z,
        status="pending",
        rush_level=rush_level.lower(),
        customer_notes=customer_notes,
        expires_at=expires_at,
    )

    # Apply auto-approval logic
    if quote.is_auto_approvable:
        quote.auto_approve_eligible = True
        quote.auto_approved = True
        quote.status = "approved"
        quote.approval_method = "auto"
        quote.approved_at = datetime.utcnow()
    else:
        quote.auto_approve_eligible = False
        # Determine why it needs review
        reasons = []
        if quote.total_price >= 50:
            reasons.append(f"Price ${quote.total_price} exceeds $50 threshold")
        if file_metadata['file_size_bytes'] > 100 * 1024 * 1024:
            reasons.append("File size exceeds 100MB")
        if material_type.upper() in ['ABS', 'ASA']:
            if dimensions_x > 200 or dimensions_y > 200 or dimensions_z > 100:
                reasons.append("ABS/ASA dimensions exceed limits (200x200x100mm)")
        quote.requires_review_reason = "; ".join(reasons)

    db.add(quote)
    db.flush()  # Get quote.id without committing

    # Create QuoteFile record
    quote_file = QuoteFile(
        quote_id=quote.id,
        original_filename=file_metadata['original_filename'],
        stored_filename=file_metadata['stored_filename'],
        file_path=file_metadata['file_path'],
        file_size_bytes=file_metadata['file_size_bytes'],
        file_format=file_metadata['file_format'],
        mime_type=file_metadata['mime_type'],
        file_hash=file_metadata['file_hash'],
        is_valid=True,
        processed=False,  # Will be true after Bambu Suite processes
    )

    db.add(quote_file)
    db.commit()
    db.refresh(quote)

    return quote


# ============================================================================
# ENDPOINT: Get User's Quotes
# ============================================================================

@router.get("/", response_model=List[QuoteListResponse])
async def get_user_quotes(
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get list of quotes for current user

    Query parameters:
    - skip: Pagination offset (default: 0)
    - limit: Max results (default: 50, max: 100)
    - status_filter: Filter by status (pending, approved, rejected, etc.)

    Returns:
        List of quotes ordered by creation date (newest first)
    """
    if limit > 100:
        limit = 100

    query = db.query(Quote).filter(Quote.user_id == current_user.id)

    if status_filter:
        query = query.filter(Quote.status == status_filter)

    quotes = (
        query
        .order_by(desc(Quote.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

    return quotes


# ============================================================================
# ENDPOINT: Get Quote Details
# ============================================================================

@router.get("/{quote_id}", response_model=QuoteResponse)
async def get_quote_details(
    quote_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific quote

    Returns:
        Complete quote data including files and pricing
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )

    # Verify user owns this quote
    if quote.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this quote"
        )

    return quote


# ============================================================================
# ENDPOINT: Accept Quote
# ============================================================================

@router.post("/{quote_id}/accept", response_model=QuoteResponse)
async def accept_quote(
    quote_id: int,
    acceptance: QuoteAccept,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Customer accepts an approved quote

    This endpoint:
    1. Moves the quote to 'accepted' status
    2. Auto-creates a custom product (CUSTOM-Q-YYYY-XXX)
    3. Auto-creates a BOM with:
       - Material line (filament based on quote specs)
       - Packaging line (shipping box based on dimensions)

    The BOM is editable by admins before finalizing the order.

    Requirements:
    - Quote must be in 'approved' status
    - Quote must not be expired
    - User must own the quote
    - Quote must have material_type, dimensions, and quantity

    Returns:
        Updated quote with 'accepted' status and product_id
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )

    # Verify ownership
    if quote.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to accept this quote"
        )

    # Check status
    if quote.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot accept quote with status '{quote.status}'. Must be 'approved'."
        )

    # Check expiration
    if quote.is_expired:
        quote.status = "expired"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quote has expired. Please request a new quote."
        )

    # Accept quote
    quote.status = "accepted"
    quote.approval_method = "customer"
    if acceptance.customer_notes:
        quote.customer_notes = acceptance.customer_notes

    # Auto-create Product + BOM from the accepted quote
    try:
        product, bom = auto_create_product_and_bom(quote, db)
        # product_id is already linked to quote in the service function
        db.commit()
        db.refresh(quote)

        # Log success
        print(f"[BOM] Created product {product.sku} and BOM (ID: {bom.id}) for quote {quote.quote_number}")
        print(f"[BOM] BOM has {len(bom.lines)} lines")

    except ValueError as e:
        # Quote data is missing or invalid
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot create product/BOM: {str(e)}"
        )
    except RuntimeError as e:
        # Could not find material or box
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"BOM creation failed: {str(e)}"
        )
    except Exception as e:
        # Unexpected error
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create product/BOM: {str(e)}"
        )

    return quote


# ============================================================================
# ENDPOINT: Update Quote Status (Admin)
# ============================================================================

@router.patch("/{quote_id}/status", response_model=QuoteResponse)
async def update_quote_status(
    quote_id: int,
    update: QuoteUpdateStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update quote status (admin only)

    Allows manual approval, rejection, or cancellation of quotes

    Admin statuses:
    - approved: Manually approve the quote
    - rejected: Reject the quote with reason
    - cancelled: Cancel the quote

    Returns:
        Updated quote
    """
    # TODO: Add admin role check
    # For now, any authenticated user can update (remove this in production)

    quote = db.query(Quote).filter(Quote.id == quote_id).first()

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )

    # Update status
    quote.status = update.status

    if update.status == "approved":
        quote.approval_method = "manual"
        quote.approved_by = current_user.id
        quote.approved_at = datetime.utcnow()
    elif update.status == "rejected":
        quote.rejection_reason = update.rejection_reason

    if update.admin_notes:
        quote.admin_notes = update.admin_notes

    db.commit()
    db.refresh(quote)

    return quote


# ============================================================================
# PORTAL ENDPOINTS (Public/No Auth Required)
# ============================================================================

# Portal guest user ID - create this user in DB or use existing admin
# TODO: Create a proper portal user in production
PORTAL_USER_ID = 1


@router.post("/portal", response_model=PortalQuoteResponse, status_code=status.HTTP_201_CREATED)
async def create_portal_quote(
    quote_data: PortalQuoteCreate,
    db: Session = Depends(get_db),
):
    """
    Create a quote from the public portal (no authentication required)
    
    This endpoint is used by the customer-facing quote portal to save
    quotes generated by the Print Suite API to the ERP database.
    
    The quote is saved with a "portal" status and can be viewed in
    the admin dashboard.
    
    Returns:
        Created quote with ID and quote number
    """
    # Generate quote number
    year = datetime.utcnow().year
    last_quote = (
        db.query(Quote)
        .filter(Quote.quote_number.like(f"Q-{year}-%"))
        .order_by(desc(Quote.quote_number))
        .first()
    )
    
    if last_quote:
        last_num = int(last_quote.quote_number.split("-")[2])
        next_num = last_num + 1
    else:
        next_num = 1
    
    quote_number = f"Q-{year}-{next_num:03d}"
    
    # Calculate expiration (7 days)
    expires_at = datetime.utcnow() + timedelta(days=QUOTE_EXPIRATION_DAYS)
    
    # Convert print time from minutes to hours
    print_time_hours = float(quote_data.print_time_minutes) / 60.0
    
    # Determine file format from filename
    file_format = quote_data.file_format.lower()
    if not file_format.startswith('.'):
        file_format = '.' + file_format
    
    # Determine if quote can be auto-approved
    # Auto-approve only if: price < $50 AND no special requirements (notes)
    has_special_requirements = bool(quote_data.customer_notes and quote_data.customer_notes.strip())
    can_auto_approve = quote_data.total_price < 50 and not has_special_requirements

    # Use customer_id if provided (logged in), else use portal guest user
    actual_user_id = quote_data.customer_id if quote_data.customer_id else PORTAL_USER_ID

    # Create quote record
    quote = Quote(
        user_id=actual_user_id,
        quote_number=quote_number,
        product_name=quote_data.filename,
        quantity=quote_data.quantity,
        material_type=quote_data.material.upper(),
        color=quote_data.color.upper() if quote_data.color else None,  # Store color for BOM creation
        finish=quote_data.quality.lower(),  # Using finish field for quality
        material_grams=quote_data.material_grams,
        print_time_hours=print_time_hours,
        unit_price=quote_data.unit_price,
        total_price=quote_data.total_price,
        file_format=file_format,
        file_size_bytes=0,  # Not tracking file size for portal quotes
        dimensions_x=quote_data.dimensions_x,
        dimensions_y=quote_data.dimensions_y,
        dimensions_z=quote_data.dimensions_z,
        status="pending",
        rush_level="standard",
        customer_notes=quote_data.customer_notes,
        expires_at=expires_at,
        auto_approve_eligible=can_auto_approve,
        auto_approved=can_auto_approve,
    )

    # Auto-approve if eligible (price < $50 and no special requirements)
    if can_auto_approve:
        quote.status = "approved"
        quote.approval_method = "auto"
        quote.approved_at = datetime.utcnow()
    
    db.add(quote)
    db.flush()  # Get quote.id before creating materials

    # Create QuoteMaterial records for multi-material quotes
    print(f"[PORTAL] multi_material data received: {quote_data.multi_material}")
    if quote_data.multi_material and quote_data.multi_material.is_multi_material:
        print(f"[PORTAL] Creating QuoteMaterial records for {quote_data.multi_material.material_count} materials")
        mm = quote_data.multi_material
        weights = mm.filament_weights_grams or []
        types = mm.filament_types or []
        colors = mm.filament_colors or []
        color_names = mm.filament_color_names or []
        color_hexes = mm.filament_color_hexes or []

        for slot_idx, weight in enumerate(weights):
            if weight > 0:  # Only create records for slots with material usage
                qm = QuoteMaterial(
                    quote_id=quote.id,
                    slot_number=slot_idx + 1,  # 1-indexed
                    material_type=types[slot_idx] if slot_idx < len(types) else quote_data.material.upper(),
                    color_code=colors[slot_idx] if slot_idx < len(colors) else None,
                    color_name=color_names[slot_idx] if slot_idx < len(color_names) else None,
                    color_hex=color_hexes[slot_idx] if slot_idx < len(color_hexes) else None,
                    material_grams=weight,
                    is_primary=(slot_idx == 0),  # First slot is primary
                )
                db.add(qm)

    db.commit()
    db.refresh(quote)

    # Return portal-specific response
    return PortalQuoteResponse(
        id=quote.id,
        quote_number=quote.quote_number,
        filename=quote_data.filename,
        material=quote.material_type,
        quality=quote_data.quality,
        infill=quote_data.infill,
        color=quote_data.color,
        color_name=quote_data.color_name,
        quantity=quote.quantity,
        unit_price=quote.unit_price,
        total_price=quote.total_price,
        material_grams=quote.material_grams,
        print_time_minutes=quote_data.print_time_minutes,
        material_in_stock=quote_data.material_in_stock if quote_data.material_in_stock is not None else True,
        status=quote.status,
        created_at=quote.created_at,
        expires_at=quote.expires_at,
    )


@router.get("/portal/list")
async def list_portal_quotes(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    List all quotes (public endpoint for admin dashboard MVP)
    
    Returns quotes ordered by creation date (newest first)
    """
    if limit > 100:
        limit = 100
    
    from sqlalchemy.orm import joinedload

    quotes = (
        db.query(Quote)
        .options(joinedload(Quote.user))  # Eager load customer info
        .order_by(desc(Quote.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    # Calculate stats
    total = db.query(Quote).count()
    pending = db.query(Quote).filter(Quote.status == "pending").count()
    accepted = db.query(Quote).filter(Quote.status == "accepted").count()
    
    # Sum total revenue from accepted quotes
    from sqlalchemy import func
    revenue_result = (
        db.query(func.sum(Quote.total_price))
        .filter(Quote.status == "accepted")
        .scalar()
    )
    revenue = float(revenue_result) if revenue_result else 0.0
    
    # Count pending_review as well
    pending_review = db.query(Quote).filter(Quote.status == "pending_review").count()

    # Build quote list with customer info
    quote_list = []
    for q in quotes:
        customer_info = None
        if q.user and q.user.id != PORTAL_USER_ID:  # Skip generic portal user
            customer_info = {
                "id": q.user.id,
                "customer_number": q.user.customer_number,
                "email": q.user.email,
                "name": q.user.full_name,
                "company": q.user.company_name,
                "phone": q.user.phone,
            }

        quote_list.append({
            "id": q.id,
            "quote_number": q.quote_number,
            "filename": q.product_name,
            "material": q.material_type,
            "color": q.color,
            "quantity": q.quantity,
            "unit_price": float(q.unit_price) if q.unit_price else None,
            "total_price": float(q.total_price),
            "status": q.status,
            "customer_notes": q.customer_notes,
            "dimensions_x": float(q.dimensions_x) if q.dimensions_x else None,
            "dimensions_y": float(q.dimensions_y) if q.dimensions_y else None,
            "dimensions_z": float(q.dimensions_z) if q.dimensions_z else None,
            "material_grams": float(q.material_grams) if q.material_grams else None,
            "created_at": q.created_at.isoformat(),
            "customer": customer_info,
        })

    return {
        "quotes": quote_list,
        "stats": {
            "total": total,
            "pending": pending,
            "pending_review": pending_review,
            "accepted": accepted,
            "revenue": revenue,
        }
    }


# ============================================================================
# ENDPOINT: Portal Accept Quote (No Auth Required)
# ============================================================================

@router.post("/portal/{quote_id}/accept")
async def portal_accept_quote(
    quote_id: int,
    shipping_data: PortalAcceptQuote,
    db: Session = Depends(get_db),
):
    """
    Portal guest user accepts/submits a quote with shipping address.

    Behavior depends on whether the quote has special requirements (notes):
    - WITHOUT notes: Auto-accept and create product/BOM
    - WITH notes: Keep as "pending_review" for admin to review and price

    Also handles multi-color print options:
    - print_mode: "single" or "multi" - customer's color choice
    - adjusted_unit_price: Updated price if customer chose single-color
    - multi_color_info: Color selections for each slot if multi-color

    Note: This endpoint is public. Real order conversion happens when
    admin reviews the BOM and converts to sales order.
    """
    import json

    quote = db.query(Quote).filter(Quote.id == quote_id).first()

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )

    # Check status - allow approved or pending
    if quote.status not in ["approved", "pending"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot accept quote with status '{quote.status}'"
        )

    # Check expiration
    if quote.is_expired:
        quote.status = "expired"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quote has expired. Please request a new quote."
        )

    # Save shipping address to quote
    quote.shipping_name = shipping_data.shipping_name
    quote.shipping_address_line1 = shipping_data.shipping_address_line1
    quote.shipping_address_line2 = shipping_data.shipping_address_line2
    quote.shipping_city = shipping_data.shipping_city
    quote.shipping_state = shipping_data.shipping_state
    quote.shipping_zip = shipping_data.shipping_zip
    quote.shipping_country = shipping_data.shipping_country
    quote.shipping_phone = shipping_data.shipping_phone
    # Save shipping selection (from EasyPost)
    if shipping_data.shipping_rate_id:
        quote.shipping_rate_id = shipping_data.shipping_rate_id
        quote.shipping_carrier = shipping_data.shipping_carrier
        quote.shipping_service = shipping_data.shipping_service
        quote.shipping_cost = shipping_data.shipping_cost

    # Handle multi-color print mode selection
    if shipping_data.print_mode:
        print_mode = shipping_data.print_mode.lower()
        print(f"[PORTAL] Quote {quote.quote_number} - print_mode: {print_mode}")

        if print_mode == "single":
            # Customer chose single-color for a multi-material file
            # Update the price to the single-color alternative
            if shipping_data.adjusted_unit_price is not None:
                old_price = float(quote.unit_price or 0)
                quote.unit_price = Decimal(str(shipping_data.adjusted_unit_price))
                quote.total_price = quote.unit_price * quote.quantity
                print(f"[PORTAL] Price adjusted: ${old_price:.2f} -> ${float(quote.unit_price):.2f} (single-color)")

            # Store mode in internal notes
            notes = {"print_mode": "single", "original_was_multi_material": True}
            quote.internal_notes = json.dumps(notes)

        elif print_mode == "multi" and shipping_data.multi_color_info:
            # Customer chose multi-color with specific color selections
            primary_slot = shipping_data.multi_color_info.primary_slot
            color_info = {
                "print_mode": "multi",
                "primary_slot": primary_slot,
                "slot_colors": [
                    {
                        "slot": slot.slot,
                        "color_code": slot.color_code,
                        "color_name": slot.color_name,
                        "color_hex": slot.color_hex,
                        "is_primary": slot.is_primary or (slot.slot == primary_slot)
                    }
                    for slot in shipping_data.multi_color_info.slot_colors
                ]
            }
            quote.internal_notes = json.dumps(color_info)
            # Find and log the primary color
            primary_color = next((s for s in color_info['slot_colors'] if s['is_primary']), None)
            print(f"[PORTAL] Multi-color selections: {len(color_info['slot_colors'])} colors")
            for sc in color_info['slot_colors']:
                print(f"[PORTAL] Slot {sc['slot']}: {sc['color_name']} ({sc['color_code']})")

            # Update QuoteMaterial records with the selected colors
            print(f"[PORTAL] Quote has {len(quote.materials) if quote.materials else 0} QuoteMaterial records")
            if quote.materials:
                for qm in quote.materials:
                    print(f"[PORTAL] Existing QM: slot={qm.slot_number}, type={qm.material_type}, grams={qm.material_grams}")

                for slot_color in color_info['slot_colors']:
                    slot_num = slot_color['slot']
                    found = False
                    # Find matching QuoteMaterial record
                    for qm in quote.materials:
                        if qm.slot_number == slot_num:
                            qm.color_code = slot_color['color_code']
                            qm.color_name = slot_color['color_name']
                            qm.color_hex = slot_color.get('color_hex')
                            qm.is_primary = slot_color.get('is_primary', False)
                            print(f"[PORTAL] Updated QuoteMaterial slot {slot_num}: {slot_color['color_code']}")
                            found = True
                            break
                    if not found:
                        print(f"[PORTAL] WARNING: No QuoteMaterial for slot {slot_num} - color {slot_color['color_code']} not saved to QM")
            else:
                print(f"[PORTAL] WARNING: No QuoteMaterial records exist for this quote")

            # Also update quote.color with primary color for fallback
            if primary_color:
                quote.color = primary_color['color_code']
                print(f"[PORTAL] Updated quote.color to primary: {primary_color['color_code']}")

    # Check if quote has special requirements (notes) - needs manual review
    has_special_requirements = bool(quote.customer_notes and quote.customer_notes.strip())

    if has_special_requirements:
        # Keep in pending_review status - admin must approve
        quote.status = "pending_review"
        quote.approval_method = "portal_submitted"
        db.commit()
        db.refresh(quote)

        print(f"[PORTAL] Quote {quote.quote_number} submitted for review (has special requirements)")

        return {
            "success": True,
            "quote_number": quote.quote_number,
            "quote_id": quote.id,
            "status": quote.status,
            "product_id": None,
            "message": "Quote submitted for review! We'll send you a final quote with pricing.",
            "requires_review": True,
        }

    # Standard quote - accept and create product/BOM
    quote.status = "accepted"
    quote.approval_method = "portal"

    # Auto-create Product + BOM
    try:
        product, bom = auto_create_product_and_bom(quote, db)
        db.commit()
        db.refresh(quote)

        print(f"[PORTAL] Quote {quote.quote_number} accepted")
        print(f"[PORTAL] Created product {product.sku} and BOM (ID: {bom.id})")

    except Exception as e:
        db.rollback()
        print(f"[PORTAL] BOM creation failed: {str(e)}")
        # Still accept the quote, BOM can be created manually
        quote.status = "accepted"
        quote.approval_method = "portal"
        quote.internal_notes = f"Auto-BOM failed: {str(e)}"
        db.commit()

    return {
        "success": True,
        "quote_number": quote.quote_number,
        "quote_id": quote.id,
        "status": quote.status,
        "product_id": quote.product_id,
        "message": "Quote accepted! We will review and send you an invoice.",
        "requires_review": False,
    }


# ============================================================================
# ENDPOINT: Portal Admin Status Update (No Auth - MVP)
# ============================================================================

from pydantic import BaseModel as PydanticBaseModel

class PortalStatusUpdate(PydanticBaseModel):
    """Request body for admin status update"""
    status: str  # approved, rejected, accepted
    admin_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    updated_price: Optional[float] = None


@router.patch("/portal/{quote_id}/status")
async def portal_update_quote_status(
    quote_id: int,
    update: PortalStatusUpdate,
    db: Session = Depends(get_db),
):
    """
    Admin updates quote status (MVP - no auth required).

    Actions:
    - approve: Mark as approved (can update price for custom quotes)
    - reject: Mark as rejected with reason
    - accepted: Mark as accepted and create product/BOM

    Future: Add proper admin authentication
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )

    new_status = update.status.lower()
    valid_statuses = ["approved", "rejected", "accepted", "cancelled"]

    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    # Handle status-specific logic
    if new_status == "approved":
        quote.status = "approved"
        quote.approval_method = "manual"
        quote.approved_at = datetime.utcnow()

        # Update price if provided (for custom quotes)
        if update.updated_price is not None:
            quote.total_price = Decimal(str(update.updated_price))
            quote.unit_price = Decimal(str(update.updated_price)) / quote.quantity

    elif new_status == "rejected":
        quote.status = "rejected"
        quote.rejection_reason = update.rejection_reason or "Rejected by admin"

    elif new_status == "accepted":
        quote.status = "accepted"
        quote.approval_method = "manual"

        # Create product/BOM
        try:
            product, bom = auto_create_product_and_bom(quote, db)
            print(f"[ADMIN] Created product {product.sku} and BOM for quote {quote.quote_number}")
        except Exception as e:
            print(f"[ADMIN] BOM creation failed: {str(e)}")
            quote.internal_notes = f"Auto-BOM failed: {str(e)}"

    elif new_status == "cancelled":
        quote.status = "cancelled"

    # Add admin notes if provided
    if update.admin_notes:
        quote.admin_notes = update.admin_notes

    db.commit()
    db.refresh(quote)

    return {
        "success": True,
        "quote_id": quote.id,
        "quote_number": quote.quote_number,
        "status": quote.status,
        "total_price": float(quote.total_price),
        "message": f"Quote status updated to '{quote.status}'",
    }


# ============================================================================
# ENDPOINT: Portal Submit Quote for Review
# ============================================================================

@router.post("/portal/{quote_id}/submit-for-review")
async def portal_submit_for_review(
    quote_id: int,
    review_data: PortalSubmitForReview,
    db: Session = Depends(get_db),
):
    """
    Submit a quote for engineer review (quotes with special requirements).
    
    This endpoint:
    1. Saves customer email for follow-up
    2. Saves shipping address
    3. Sets status to "pending_review"
    4. (Future) Sends confirmation email to customer
    
    After review, engineer will:
    1. Review requirements and adjust pricing if needed
    2. Send payment link to customer email
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    # Check status - allow pending or approved quotes
    if quote.status not in ["pending", "approved"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit quote with status '{quote.status}' for review"
        )
    
    # Check expiration
    if quote.is_expired:
        quote.status = "expired"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quote has expired. Please request a new quote."
        )
    
    # Save customer contact info
    quote.customer_email = review_data.customer_email
    if review_data.customer_name:
        quote.customer_name = review_data.customer_name
    elif review_data.shipping_name:
        quote.customer_name = review_data.shipping_name
    
    # Save shipping address
    quote.shipping_name = review_data.shipping_name
    quote.shipping_address_line1 = review_data.shipping_address_line1
    quote.shipping_address_line2 = review_data.shipping_address_line2
    quote.shipping_city = review_data.shipping_city
    quote.shipping_state = review_data.shipping_state
    quote.shipping_zip = review_data.shipping_zip
    quote.shipping_country = review_data.shipping_country
    quote.shipping_phone = review_data.shipping_phone
    
    # Save shipping selection if provided
    if review_data.shipping_rate_id:
        quote.shipping_rate_id = review_data.shipping_rate_id
        quote.shipping_carrier = review_data.shipping_carrier
        quote.shipping_service = review_data.shipping_service
        quote.shipping_cost = review_data.shipping_cost
    
    # Update status to pending_review
    quote.status = "pending_review"
    quote.approval_method = "portal_submitted"
    
    db.commit()
    db.refresh(quote)
    
    print(f"[PORTAL] Quote {quote.quote_number} submitted for review")
    print(f"[PORTAL] Customer email: {quote.customer_email}")
    print(f"[PORTAL] Special requirements: {quote.customer_notes}")
    
    # TODO: Send confirmation email to customer
    # await send_review_confirmation_email(quote)
    
    return {
        "success": True,
        "quote_id": quote.id,
        "quote_number": quote.quote_number,
        "status": quote.status,
        "customer_email": quote.customer_email,
        "message": "Quote submitted for review. You will receive a confirmation email shortly, followed by a payment link once reviewed.",
    }


# ============================================================================
# ENDPOINT: Get Material Inventory for Quote
# ============================================================================

@router.get("/portal/{quote_id}/inventory")
async def get_quote_material_inventory(
    quote_id: int,
    db: Session = Depends(get_db),
):
    """
    Get material inventory status for a specific quote.

    Returns:
    - Material SKU
    - Quantity on hand (kg)
    - Quantity needed for this quote (kg)
    - Quantity reserved by other pending quotes (kg)
    - Needs reorder flag
    """
    from app.models.material import MaterialInventory, MaterialType, Color
    from sqlalchemy import func

    quote = db.query(Quote).filter(Quote.id == quote_id).first()

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )

    # Find the material inventory for this quote's material + color
    inventory = None
    material_type = None
    color = None

    if quote.material_type:
        # Look up material type
        material_type = db.query(MaterialType).filter(
            MaterialType.code == quote.material_type.upper()
        ).first()

        # If not found by exact code, try base material
        if not material_type:
            material_type = db.query(MaterialType).filter(
                MaterialType.base_material == quote.material_type.upper(),
                MaterialType.active == True
            ).first()

    if quote.color:
        color = db.query(Color).filter(
            Color.code == quote.color.upper()
        ).first()

    if material_type and color:
        inventory = db.query(MaterialInventory).filter(
            MaterialInventory.material_type_id == material_type.id,
            MaterialInventory.color_id == color.id,
            MaterialInventory.active == True
        ).first()

    # Calculate quantity needed for this quote (convert grams to kg)
    qty_needed_kg = float(quote.material_grams or 0) / 1000.0

    # Calculate quantity reserved by OTHER pending quotes with same material
    reserved_kg = 0.0
    if material_type and color:
        # Sum material_grams from pending/approved quotes (excluding current quote)
        pending_statuses = ['pending', 'pending_review', 'approved']
        reserved_result = db.query(func.sum(Quote.material_grams)).filter(
            Quote.material_type == quote.material_type,
            Quote.color == quote.color,
            Quote.status.in_(pending_statuses),
            Quote.id != quote_id  # Exclude current quote
        ).scalar()

        reserved_kg = float(reserved_result or 0) / 1000.0

    # Build response
    if inventory:
        qty_on_hand = float(inventory.quantity_kg or 0)
        qty_available = qty_on_hand - reserved_kg
        needs_order = qty_available < qty_needed_kg or inventory.needs_reorder

        return {
            "found": True,
            "sku": inventory.sku,
            "material_name": material_type.name if material_type else quote.material_type,
            "color_name": color.name if color else quote.color,
            "qty_on_hand_kg": round(qty_on_hand, 3),
            "qty_reserved_kg": round(reserved_kg, 3),
            "qty_available_kg": round(qty_available, 3),
            "qty_needed_kg": round(qty_needed_kg, 3),
            "reorder_point_kg": float(inventory.reorder_point_kg or 0),
            "needs_order": needs_order,
            "in_stock": inventory.in_stock,
            "vendor": inventory.preferred_vendor,
        }
    else:
        return {
            "found": False,
            "sku": None,
            "material_name": material_type.name if material_type else quote.material_type,
            "color_name": color.name if color else quote.color,
            "qty_on_hand_kg": 0,
            "qty_reserved_kg": round(reserved_kg, 3),
            "qty_available_kg": 0,
            "qty_needed_kg": round(qty_needed_kg, 3),
            "reorder_point_kg": 0,
            "needs_order": True,
            "in_stock": False,
            "vendor": None,
            "message": "No inventory record found for this material/color combination"
        }
