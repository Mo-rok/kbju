from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.backend.db import SessionLocal, Dish, MealPeriod, User, StudentData

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DishCreate(BaseModel):
    name: str
    period: MealPeriod
    kcal: float
    proteins: float
    fats: float
    carbs: float


class DishResponse(BaseModel):
    id: int
    name: str
    period: str
    kcal: float
    proteins: float
    fats: float
    carbs: float


@router.post("/dishes", response_model=DishResponse)
def create_dish(dish: DishCreate, db: Session = Depends(get_db)):
    try:
        db_dish = Dish(
            name=dish.name,
            period=dish.period.value,
            kcal=dish.kcal,
            proteins=dish.proteins,
            fats=dish.fats,
            carbs=dish.carbs
        )
        db.add(db_dish)
        db.commit()
        db.refresh(db_dish)
        return db_dish
    except Exception as e:
        db.rollback()
        raise HTTPException(400, detail=f"Ошибка создания: {str(e)}")


@router.get("/dishes", response_model=List[DishResponse])
def get_all_dishes(db: Session = Depends(get_db)):
    return db.query(Dish).all()


@router.get("/students", response_model=List[Dict])
def get_students_with_meals(db: Session = Depends(get_db)):
    students = db.query(User).filter(User.role == "student").all()
    dishes = db.query(Dish).all()

    result = []
    for student in students:
        if not student.student_data:
            continue

        # Рассчет потребностей
        daily_needs = calculate_daily_needs(student.student_data)
        meal_plan = create_meal_plan(dishes, daily_needs)

        student_data = {
            "student_id": student.id,
            "student_username": student.username,
            "bmi": calculate_bmi(student.student_data),
            "daily_needs": daily_needs,
            "meal_plan": meal_plan
        }
        result.append(student_data)
    return result


def calculate_bmi(student_data):
    if not student_data:
        return None
    return round(student_data.weight / ((student_data.height / 100) ** 2), 1)


def calculate_daily_needs(student_data):
    # Формула Миффлина-Сан Жеора
    if student_data.gender == 'male':
        bmr = 10 * student_data.weight + 6.25 * student_data.height - 5 * student_data.age + 5
    else:
        bmr = 10 * student_data.weight + 6.25 * student_data.height - 5 * student_data.age - 161

    activity_factor = {
        'sedentary': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'active': 1.725
    }.get(student_data.activity_level, 1.2)

    tdee = bmr * activity_factor
    return {
        'kcal': round(tdee),
        'proteins': round(student_data.weight * 1.5),  # 1.5г белка на кг веса
        'fats': round((tdee * 0.3) / 9),  # 30% от калорий
        'carbs': round((tdee * 0.5) / 4)  # 50% от калорий
    }


def create_meal_plan(dishes, daily_needs):
    # Распределение калорий по приемам пищи
    meal_distribution = {
        'breakfast': 0.25,
        'lunch': 0.35,
        'dinner': 0.25,
        'snack': 0.15
    }

    meal_plan = {}
    for period, ratio in meal_distribution.items():
        period_kcal = daily_needs['kcal'] * ratio
        meal_plan[period] = select_dishes_for_period(
            dishes,
            period,
            max_kcal=period_kcal
        )
    return meal_plan


def select_dishes_for_period(dishes, period, max_kcal):
    selected = []
    total_kcal = 0
    for dish in dishes:
        if dish.period.value == period and (total_kcal + dish.kcal) <= max_kcal:
            selected.append({
                "name": dish.name,
                "kcal": dish.kcal,
                "proteins": dish.proteins,
                "fats": dish.fats,
                "carbs": dish.carbs
            })
            total_kcal += dish.kcal
    return selected
