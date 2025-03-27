from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.backend.db import init_db, SessionLocal, User, UserRole
from app.backend.routers import admin, staff, student

app = FastAPI()


@app.on_event("startup")
def on_startup():
    init_db()
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            new_admin = User(
                username="admin",
                password="admin",
                role=UserRole.admin
            )
            db.add(new_admin)
            db.commit()
    finally:
        db.close()


# Настройки CORS для разрешения всех источников
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все источники
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все методы
    allow_headers=["*"],  # Разрешаем все заголовки
)

app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(staff.router, prefix="/staff", tags=["staff"])
app.include_router(student.router, prefix="/student", tags=["student"])


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/login")
def login(login_data: LoginRequest):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == login_data.username).first()
        if not user or user.password != login_data.password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        return {"user_id": user.id, "role": user.role.value}
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "Hello from School Nutrition API"}
