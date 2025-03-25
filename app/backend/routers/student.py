# routers/student.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.backend.db import SessionLocal, User, StudentData, UserRole
from pydantic import BaseModel

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class StudentParams(BaseModel):
    user_id: int
    height: float
    weight: float
    age: int


@router.post("/set_params")
def set_student_params(
        params: StudentParams,  # Принимаем данные из тела
        db: Session = Depends(get_db)  # Реальная проверка прав
):

    user = db.query(User).filter(User.id == params.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role != UserRole.student:
        raise HTTPException(status_code=403, detail="Not a student")

    # Обновляем или создаем запись
    if user.student_data:
        student_data = user.student_data
    else:
        student_data = StudentData(user_id=params.user_id)
        db.add(student_data)

    student_data.height = params.height
    student_data.weight = params.weight
    student_data.age = params.age

    try:
        db.commit()
        db.refresh(student_data)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Параметры успешно сохранены"}


@router.get("/calculate_kbju")
def calculate_kbju(
    user_id: int,
    db: Session = Depends(get_db),
    current_role: UserRole = UserRole.student
):

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.student_data:
        raise HTTPException(status_code=404, detail="Student data not found")

    height = user.student_data.height
    weight = user.student_data.weight
    age = user.student_data.age

    bmi = round(weight / ((height/100)**2), 2)

    # Условная формула
    daily_kcal = 30 * weight
    daily_proteins = 1.2 * weight
    daily_fats = 0.9 * weight
    daily_carbs = 3.0 * weight

    return {
        "bmi": bmi,
        "daily_kcal": round(daily_kcal, 2),
        "daily_proteins": round(daily_proteins, 2),
        "daily_fats": round(daily_fats, 2),
        "daily_carbs": round(daily_carbs, 2)
    }
