# routers/admin.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.backend.db import SessionLocal, User, UserRole
from pydantic import BaseModel

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def admin_required(user_role: UserRole):
    if user_role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")


class UserCreateRequest(BaseModel):
    username: str
    password: str
    role: UserRole


@router.post("/create_user")
def create_user(user_data: UserCreateRequest, db: Session = Depends(get_db),
):
    admin_required(UserRole.admin)

    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        username=user_data.username,
        password=user_data.password,
        role=user_data.role
    )
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": f"User {user_data.username} created", "user_id": new_user.id}


@router.get("/all_users")
def get_all_users(
    db: Session = Depends(get_db),
    current_role: UserRole = UserRole.admin
):
    admin_required(current_role)

    users = db.query(User).all()
    return [
        {
            "id": user.id,
            "username": user.username,
            "role": user.role.value
        } for user in users
    ]
