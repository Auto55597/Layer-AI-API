"""
Customer Management Router for SaaS Features
- Create/Delete Customers
- Generate/Revoke API Keys
- Manage subscription tiers
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime
import secrets
import hashlib
from typing import List, Optional

from models import Customer, APIKey, CreateCustomerRequest, CustomerResponse, GenerateAPIKeyResponse, APIKeyResponse
from database import get_session
from logger_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/customers", tags=["customers"])

# ============================================
# Helper Functions
# ============================================

def hash_api_key(api_key: str) -> str:
    """Hash API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key() -> str:
    """Generate a new API key"""
    return f"sk-{secrets.token_urlsafe(32)}"


# ============================================
# Customer Management Endpoints
# ============================================

@router.post("/register", response_model=GenerateAPIKeyResponse, summary="Register new customer")
async def register_customer(
    request: CreateCustomerRequest,
    session: Session = Depends(get_session)
):
    """
    Register (Sign up) new customer
    
    - name: Company name
    - email: Email address
    - subscription_tier: "starter" (default), "pro", "enterprise"
    """
    # Check if email already exists
    existing = session.exec(
        select(Customer).where(Customer.email == request.email.lower())
    ).first()
    if existing:
        logger.warning(f"Registration attempt with existing email: {request.email}")
        raise HTTPException(status_code=409, detail="Email already registered")
    
    # Generate API key
    api_key = generate_api_key()
    api_key_hash = hash_api_key(api_key)
    
    # Set tier limits
    tier_limits = {
        "free": {"max_agents": 5, "max_requests_per_minute": 10},
        "starter": {"max_agents": 50, "max_requests_per_minute": 100},
        "pro": {"max_agents": 500, "max_requests_per_minute": 1000},
        "enterprise": {"max_agents": 5000, "max_requests_per_minute": 10000},
    }
    
    limits = tier_limits.get(request.subscription_tier, tier_limits["starter"])
    
    # Create customer
    customer = Customer(
        name=request.name,
        email=request.email.lower(),
        subscription_tier=request.subscription_tier,
        api_key_hash=api_key_hash,
        max_agents=limits["max_agents"],
        max_requests_per_minute=limits["max_requests_per_minute"],
    )
    
    session.add(customer)
    session.commit()
    session.refresh(customer)
    
    logger.info(f"New customer registered: {customer.id} ({customer.email})")
    
    return GenerateAPIKeyResponse(
        api_key=api_key,
        key_id=customer.id,
        message=f"✅ Registration successful! Customer ID: {customer.id}\n⚠️  Save this API key somewhere safe. You won't be able to see it again."
    )


@router.get("/me", response_model=CustomerResponse, summary="Get current customer info")
async def get_current_customer(
    session: Session = Depends(get_session),
    customer_id: str = None  # In production, get from auth token
):
    """
    Retrieve current customer information
    (In production, should use auth token instead of query param)
    """
    if not customer_id:
        raise HTTPException(status_code=401, detail="Customer ID required")
    
    customer = session.get(Customer, customer_id)
    if not customer:
        logger.warning(f"Customer not found: {customer_id}")
        raise HTTPException(status_code=404, detail="Customer not found")
    
    if not customer.is_active:
        logger.warning(f"Inactive customer access attempt: {customer_id}")
        raise HTTPException(status_code=403, detail="Customer account is inactive")
    
    return CustomerResponse(
        id=customer.id,
        name=customer.name,
        email=customer.email,
        subscription_tier=customer.subscription_tier,
        max_agents=customer.max_agents,
        max_requests_per_minute=customer.max_requests_per_minute,
        total_api_calls=customer.total_api_calls,
        is_active=customer.is_active,
        created_at=customer.created_at,
    )


@router.get("/{customer_id}", response_model=CustomerResponse, summary="Get customer by ID")
async def get_customer(
    customer_id: str,
    session: Session = Depends(get_session)
):
    """
    Retrieve customer information by ID (Admin endpoint)
    """
    customer = session.get(Customer, customer_id)
    if not customer:
        logger.warning(f"Customer not found: {customer_id}")
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return CustomerResponse(
        id=customer.id,
        name=customer.name,
        email=customer.email,
        subscription_tier=customer.subscription_tier,
        max_agents=customer.max_agents,
        max_requests_per_minute=customer.max_requests_per_minute,
        total_api_calls=customer.total_api_calls,
        is_active=customer.is_active,
        created_at=customer.created_at,
    )


@router.put("/{customer_id}/upgrade", response_model=CustomerResponse, summary="Upgrade subscription")
async def upgrade_subscription(
    customer_id: str,
    new_tier: str,
    session: Session = Depends(get_session)
):
    """
    Upgrade subscription tier
    - new_tier: "free", "starter", "pro", "enterprise"
    """
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    tier_limits = {
        "free": {"max_agents": 5, "max_requests_per_minute": 10},
        "starter": {"max_agents": 50, "max_requests_per_minute": 100},
        "pro": {"max_agents": 500, "max_requests_per_minute": 1000},
        "enterprise": {"max_agents": 5000, "max_requests_per_minute": 10000},
    }
    
    if new_tier not in tier_limits:
        raise HTTPException(status_code=400, detail=f"Invalid tier: {new_tier}")
    
    limits = tier_limits[new_tier]
    customer.subscription_tier = new_tier
    customer.max_agents = limits["max_agents"]
    customer.max_requests_per_minute = limits["max_requests_per_minute"]
    customer.updated_at = datetime.utcnow()
    
    session.add(customer)
    session.commit()
    session.refresh(customer)
    
    logger.info(f"Customer {customer_id} upgraded to {new_tier} tier")
    
    return CustomerResponse(
        id=customer.id,
        name=customer.name,
        email=customer.email,
        subscription_tier=customer.subscription_tier,
        max_agents=customer.max_agents,
        max_requests_per_minute=customer.max_requests_per_minute,
        total_api_calls=customer.total_api_calls,
        is_active=customer.is_active,
        created_at=customer.created_at,
    )


# ============================================
# API Key Management Endpoints
# ============================================

@router.post("/{customer_id}/api-keys/generate", response_model=GenerateAPIKeyResponse, summary="Generate new API key")
async def generate_api_key_endpoint(
    customer_id: str,
    key_name: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """
    Generate new API Key for Customer
    """
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    if not customer.is_active:
        raise HTTPException(status_code=403, detail="Customer account is inactive")
    
    # Generate new API key
    api_key = generate_api_key()
    api_key_hash = hash_api_key(api_key)
    
    # Create API key record
    api_key_obj = APIKey(
        customer_id=customer_id,
        key_hash=api_key_hash,
        name=key_name or "API Key"
    )
    
    session.add(api_key_obj)
    session.commit()
    session.refresh(api_key_obj)
    
    logger.info(f"API key generated for customer {customer_id}")
    
    return GenerateAPIKeyResponse(
        api_key=api_key,
        key_id=api_key_obj.id,
        message="⚠️  Save this API key somewhere safe. You won't be able to see it again."
    )


@router.get("/{customer_id}/api-keys", response_model=List[APIKeyResponse], summary="List API keys")
async def list_api_keys(
    customer_id: str,
    session: Session = Depends(get_session)
):
    """
    View all API Keys (not showing raw key, only hash)
    """
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    keys = session.exec(
        select(APIKey).where(APIKey.customer_id == customer_id)
    ).all()
    
    return [
        APIKeyResponse(
            id=key.id,
            name=key.name,
            created_at=key.created_at,
            last_used=key.last_used,
            is_active=key.is_active,
        )
        for key in keys
    ]


@router.delete("/{customer_id}/api-keys/{key_id}", summary="Revoke API key")
async def revoke_api_key(
    customer_id: str,
    key_id: str,
    session: Session = Depends(get_session)
):
    """
    Revoke API Key
    """
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    api_key = session.get(APIKey, key_id)
    if not api_key or api_key.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="API key not found")
    
    # Soft delete - mark as inactive
    api_key.is_active = False
    session.add(api_key)
    session.commit()
    
    logger.info(f"API key {key_id} revoked for customer {customer_id}")
    
    return {"message": "API key revoked successfully"}


@router.delete("/{customer_id}", summary="Delete customer (deactivate)")
async def deactivate_customer(
    customer_id: str,
    session: Session = Depends(get_session)
):
    """
    Close customer account (Soft delete - change to inactive)
    """
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer.is_active = False
    customer.updated_at = datetime.utcnow()
    session.add(customer)
    session.commit()
    
    logger.warning(f"Customer {customer_id} deactivated")
    
    return {"message": "Customer account deactivated"}
