"""Auth router: register, login (OAuth2 form), me."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import repositories
from app.database import get_db
from app.models import User
from app.schemas import Token, UserCreate, UserOut
from app.security import (
    check_login_rate_limit,
    clear_failed_logins,
    create_access_token,
    get_current_user,
    record_failed_login,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if repositories.get_user_by_email(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    user = repositories.create_user(
        db, payload.email, payload.password, full_name=payload.full_name
    )
    repositories.log_audit(db, user.id, "REGISTER", "user", str(user.id),
                           f"Registered {user.email}")
    return user


@router.post("/login", response_model=Token)
def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    check_login_rate_limit(request)
    user = repositories.get_user_by_email(db, form.username)
    if user is None or not verify_password(form.password, user.hashed_password):
        record_failed_login(request)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is inactive"
        )
    clear_failed_logins(request)
    repositories.log_audit(db, user.id, "LOGIN", "user", str(user.id),
                           f"Login {user.email}")
    return Token(access_token=create_access_token({"sub": user.email}))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
