from fastapi import APIRouter, HTTPException, status
from app.models.schemas import LoginRequest, LoginResponse
from app.services.patient_service import verify_user
from app.auth import create_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    user = verify_user(req.username, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="bad username or password",
        )

    token = create_token({
        "sub": user["username"],
        "role": user["role"],
        "patient_id": user["patient_id"],
        "name": user["name"],
    })

    return LoginResponse(
        access_token=token,
        role=user["role"],
        patient_id=user["patient_id"],
        name=user["name"],
        username=user["username"],
    )
