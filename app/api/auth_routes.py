from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.core.database import get_db
from app.core.security import password_hasher, jwt_handler, api_key_manager
from app.core.auth import get_current_user
from app.models.user import User
from app.models.audit import AuditLog, ActionType
from app.schemas.user import UserCreate, UserResponse, LoginRequest, Token, APIKeyUpdate

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    result = await db.execute(
        select(User).where(
            (User.username == user_data.username) | (User.email == user_data.email)
        )
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )

    # Create new user
    hashed_password = password_hasher.hash_password(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Log action
    log = AuditLog(
        user_id=new_user.id,
        action_type=ActionType.INFO,
        action_description=f"User registered: {new_user.username}"
    )
    db.add(log)
    await db.commit()

    return new_user


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login and get access token"""
    # Find user
    result = await db.execute(
        select(User).where(User.username == login_data.username)
    )
    user = result.scalar_one_or_none()

    if not user or not password_hasher.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Update last login
    user.last_login = datetime.utcnow()

    # Create tokens
    access_token = jwt_handler.create_access_token({"sub": user.id})
    refresh_token = jwt_handler.create_refresh_token({"sub": user.id})

    # Log action
    log = AuditLog(
        user_id=user.id,
        action_type=ActionType.LOGIN,
        action_description=f"User logged in: {user.username}"
    )
    db.add(log)
    await db.commit()

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.post("/api-keys", status_code=status.HTTP_200_OK)
async def update_api_keys(
    api_keys: APIKeyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update Binance API keys"""
    # Encrypt API keys
    encrypted_key, encrypted_secret = api_key_manager.encrypt_api_credentials(
        api_keys.api_key,
        api_keys.api_secret
    )

    # Update user
    current_user.encrypted_binance_api_key = encrypted_key
    current_user.encrypted_binance_api_secret = encrypted_secret
    current_user.use_testnet = api_keys.use_testnet

    # Log action
    log = AuditLog(
        user_id=current_user.id,
        action_type=ActionType.API_KEY_UPDATED,
        action_description="Binance API keys updated"
    )
    db.add(log)

    await db.commit()

    return {"message": "API keys updated successfully", "use_testnet": api_keys.use_testnet}