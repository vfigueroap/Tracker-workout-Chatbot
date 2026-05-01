from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.crud import user as user_crud
from backend.schemas.user import UserProfileOut, UserProfileUpdate

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=UserProfileOut)
def get_profile(db: Session = Depends(get_db)):
    user = user_crud.get_user(db)
    if not user:
        raise HTTPException(status_code=404, detail="Profile not found")
    return user


@router.put("", response_model=UserProfileOut)
def update_profile(data: UserProfileUpdate, db: Session = Depends(get_db)):
    return user_crud.update_user(db, data.model_dump(exclude_none=True))
