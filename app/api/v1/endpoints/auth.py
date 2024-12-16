from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core import deps
from app.schemas.user import UserCreate, User

router = APIRouter()

@router.post("/login")
async def login(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    TODO: Implement login endpoint
    """
    pass

@router.post("/register", response_model=User)
async def register(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate
):
    """
    TODO: Implement user registration
    """
    pass
