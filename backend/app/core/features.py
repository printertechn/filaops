"""
Feature Flag System for FilaOps

Controls access to features based on subscription tier.
Set LICENSING_ENABLED = False to give everyone all features (current mode).
Set LICENSING_ENABLED = True to enforce license checking.
"""
from enum import Enum
from typing import Dict, List, Callable
from functools import wraps
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session

# ============================================================================
# MASTER SWITCH - Set to True when ready to enforce licensing
# ============================================================================
LICENSING_ENABLED = False  # Everyone gets all features for now!

class FeatureTier(str, Enum):
    """Subscription tiers"""
    COMMUNITY = "community"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    
    # Aliases for backward compatibility
    PRO = "professional"  # Same as PROFESSIONAL

# ============================================================================
# Feature Definitions
# ============================================================================
# NOTE: For now, ALL features are marked as "community" so everyone gets them.
# When ready to monetize, just change the tier values below.
# ============================================================================

FEATURE_FLAGS: Dict[str, Dict] = {
    # ========================================================================
    # Quality - Traceability (FREE FOREVER)
    # ========================================================================
    "traceability_forward": {
        "name": "Forward Traceability",
        "tier": FeatureTier.COMMUNITY,
        "description": "Trace materials forward from spool to finished products",
        "category": "quality",
    },
    "traceability_backward": {
        "name": "Backward Traceability",
        "tier": FeatureTier.COMMUNITY,
        "description": "Trace finished products back to source materials",
        "category": "quality",
    },
    "traceability_export": {
        "name": "DHR Report Export",
        "tier": FeatureTier.COMMUNITY,
        "description": "Export Device History Records as PDF/CSV",
        "category": "quality",
    },
    "quality_audit_log": {
        "name": "Quality Audit Log",
        "tier": FeatureTier.COMMUNITY,
        "description": "Track all quality-related changes",
        "category": "quality",
    },
    
    # ========================================================================
    # Quality - Advanced (Future: Professional Tier)
    # ========================================================================
    # When ready to monetize, change these to FeatureTier.PROFESSIONAL
    "recall_impact_calculator": {
        "name": "Recall Impact Calculator",
        "tier": FeatureTier.COMMUNITY,  # TODO: Change to PROFESSIONAL when ready
        "description": "Calculate scope of material recalls",
        "category": "quality",
    },
    "quality_holds": {
        "name": "Quality Holds & Quarantine",
        "tier": FeatureTier.COMMUNITY,  # TODO: Change to PROFESSIONAL when ready
        "description": "Put materials/products on quality hold",
        "category": "quality",
    },
    "traceability_alerts": {
        "name": "Material Usage Alerts",
        "tier": FeatureTier.COMMUNITY,  # TODO: Change to PROFESSIONAL when ready
        "description": "Email notifications when specific materials are used",
        "category": "quality",
    },
    "advanced_reports": {
        "name": "Advanced Quality Reports",
        "tier": FeatureTier.COMMUNITY,  # TODO: Change to PROFESSIONAL when ready
        "description": "Custom quality reports and analytics",
        "category": "quality",
    },
    
    # ========================================================================
    # Quality - Enterprise (Future: Enterprise Tier)
    # ========================================================================
    # When ready to monetize, change these to FeatureTier.ENTERPRISE
    "traceability_webhooks": {
        "name": "Traceability API Webhooks",
        "tier": FeatureTier.COMMUNITY,  # TODO: Change to ENTERPRISE when ready
        "description": "Real-time webhooks for material usage events",
        "category": "quality",
    },
    "multi_site_traceability": {
        "name": "Multi-Site Traceability",
        "tier": FeatureTier.COMMUNITY,  # TODO: Change to ENTERPRISE when ready
        "description": "Trace materials across multiple facilities",
        "category": "quality",
    },
    "spc_charts": {
        "name": "Statistical Process Control",
        "tier": FeatureTier.COMMUNITY,  # TODO: Change to ENTERPRISE when ready
        "description": "Real-time SPC charts and control limits",
        "category": "quality",
    },
}

# ============================================================================
# Convenience Lists
# ============================================================================

COMMUNITY_FEATURES = [
    code for code, feature in FEATURE_FLAGS.items() 
    if feature["tier"] == FeatureTier.COMMUNITY
]

PROFESSIONAL_FEATURES = [
    code for code, feature in FEATURE_FLAGS.items() 
    if feature["tier"] in [FeatureTier.COMMUNITY, FeatureTier.PROFESSIONAL]
]

ENTERPRISE_FEATURES = list(FEATURE_FLAGS.keys())  # All features

# ============================================================================
# Feature Access Functions
# ============================================================================

def has_feature(feature_code: str, user_tier: str = "community") -> bool:
    """
    Check if a user's tier has access to a feature.
    
    If LICENSING_ENABLED = False, always returns True (everyone gets everything).
    If LICENSING_ENABLED = True, checks tier hierarchy.
    
    Args:
        feature_code: Feature identifier (e.g., "traceability_forward")
        user_tier: User's subscription tier
    
    Returns:
        True if user has access, False otherwise
    """
    # If licensing is disabled, everyone gets everything!
    if not LICENSING_ENABLED:
        return True
    
    # Check if feature exists
    if feature_code not in FEATURE_FLAGS:
        return False
    
    feature = FEATURE_FLAGS[feature_code]
    tier_order = ["community", "professional", "enterprise"]
    
    required_tier_index = tier_order.index(feature["tier"])
    user_tier_index = tier_order.index(user_tier.lower())
    
    return user_tier_index >= required_tier_index

def get_features_for_tier(tier: str) -> List[str]:
    """
    Get all feature codes available for a tier.
    
    Args:
        tier: Subscription tier
    
    Returns:
        List of feature codes
    """
    if tier == FeatureTier.COMMUNITY:
        return COMMUNITY_FEATURES
    elif tier == FeatureTier.PROFESSIONAL:
        return PROFESSIONAL_FEATURES
    elif tier == FeatureTier.ENTERPRISE:
        return ENTERPRISE_FEATURES
    return COMMUNITY_FEATURES

def get_features_by_category(category: str) -> Dict[str, Dict]:
    """
    Get all features in a category.
    
    Args:
        category: Category name (e.g., "quality")
    
    Returns:
        Dict of feature_code -> feature_info
    """
    return {
        code: feature 
        for code, feature in FEATURE_FLAGS.items() 
        if feature.get("category") == category
    }

# ============================================================================
# Backward Compatibility (Legacy API)
# ============================================================================

# Alias for backward compatibility
Tier = FeatureTier

def get_current_tier(db: Session, user) -> FeatureTier:
    """
    Get the current user's subscription tier.
    
    Args:
        db: Database session
        user: Current user object
    
    Returns:
        User's tier (defaults to COMMUNITY if licensing disabled)
    """
    # If licensing is disabled, everyone is enterprise (all features)
    if not LICENSING_ENABLED:
        return FeatureTier.ENTERPRISE
    
    # TODO: When licensing is enabled, check organization's license key
    # For now, default to community
    return FeatureTier.COMMUNITY

def get_available_features(tier: FeatureTier) -> List[str]:
    """
    Get list of feature codes available for a tier.
    
    Args:
        tier: Subscription tier
    
    Returns:
        List of feature codes
    """
    return get_features_for_tier(tier.value)

def require_tier(minimum_tier: FeatureTier) -> Callable:
    """
    Decorator to require a minimum subscription tier.
    
    Usage:
        @router.get("/advanced-analytics")
        @require_tier(Tier.PROFESSIONAL)
        async def advanced_analytics(...):
            ...
    
    Args:
        minimum_tier: Minimum tier required
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # If licensing is disabled, allow everything
            if not LICENSING_ENABLED:
                return await func(*args, **kwargs)
            
            # Extract user and db from kwargs (injected by FastAPI)
            user = kwargs.get("current_user")
            db = kwargs.get("db")
            
            if not user or not db:
                raise HTTPException(
                    status_code=500,
                    detail="Missing authentication dependencies"
                )
            
            # Check user's tier
            user_tier = get_current_tier(db, user)
            tier_order = ["community", "professional", "enterprise"]
            
            required_index = tier_order.index(minimum_tier.value)
            user_index = tier_order.index(user_tier.value)
            
            if user_index < required_index:
                raise HTTPException(
                    status_code=403,
                    detail=f"This feature requires {minimum_tier.value.title()} tier or higher"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
