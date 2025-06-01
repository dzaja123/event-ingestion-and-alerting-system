from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app import crud
from app.db.session import get_db
from app.schemas.authorized_user import AuthorizedUserCreate, AuthorizedUserRead
from app.services.cache_service import cache_service

router = APIRouter()


@router.post("/", response_model=AuthorizedUserRead, status_code=status.HTTP_201_CREATED)
async def create_authorized_user(
    user_in: AuthorizedUserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new authorized user.
    """
    # Check if user already exists
    existing_user = await crud.authorized_user.get_by_user_id(db, user_id=user_in.user_id)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID already exists in authorized list"
        )
    
    # Create user in database
    user = await crud.authorized_user.create(db, obj_in=user_in)
    
    # Add to cache
    await cache_service.add_authorized_user(user_in.user_id)
    
    return user


@router.get("/", response_model=List[AuthorizedUserRead])
async def get_authorized_users(
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve all authorized users.
    """
    users = await crud.authorized_user.get_all(db)
    return users


@router.get("/{user_id}", response_model=AuthorizedUserRead)
async def get_authorized_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific authorized user by user_id.
    """
    user = await crud.authorized_user.get_by_user_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authorized user not found"
        )
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_authorized_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a user from the authorized list.
    """
    success = await crud.authorized_user.delete(db, user_id=user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authorized user not found"
        )
    
    # Remove from cache - refresh entire cache to be safe
    users = await crud.authorized_user.get_all(db)
    user_ids = {user.user_id for user in users}
    await cache_service.set_authorized_users(user_ids)
