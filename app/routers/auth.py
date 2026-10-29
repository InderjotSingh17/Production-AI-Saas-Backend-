# it handles reg API and database operations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.auth import hash_password,verify_password,create_access_token
from app.database import get_db
from app.models import User
from app.schemas import UserRegister, UserResponse, UserLogin, TokenResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    email = str(user_data.email).strip().lower()
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    user = User(
        email=email,
        hashed_password=hash_password(user_data.password),
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    return user

@router.post("/login",response_model=TokenResponse)
def login_user(
    credentials:UserLogin,
    db:Session=Depends(get_db),
):
    email = str(credentials.email).strip().lower()
    user=db.query(User).filter(User.email==email).first()
    if not user or not verify_password(
        credentials.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate":"Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )
    access_token=create_access_token(user.id)
    return {
        "access_token":access_token,
        "token_type":"bearer",
    }

@router.get("/me",response_model=UserResponse)
def get_my_response(current_user:User=Depends(get_current_user)):
    return current_user