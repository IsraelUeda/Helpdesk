from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from security import verify_password, hash_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticação"])

@router.post("/login", response_model=schemas.TokenResponse)
def login(credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    email = credentials.email.strip().lower()
    password = credentials.password

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        # Se for um usuário novo, cadastra automaticamente para facilitar testes e desenvolvimento
        user_name = email.split("@")[0].replace(".", " ").title()
        user = models.User(
            email=email,
            name=user_name,
            hashed_password=hash_password(password),
            role="atendente",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Verifica a senha
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha inválidos.",
            )

    token = create_access_token({"sub": user.id, "email": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }

@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user
