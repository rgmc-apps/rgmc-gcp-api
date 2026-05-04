"""Trade Portal Auth Routes."""
import logging
from datetime import date
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from src.services.generic_functions import decrypt
from ._db import get_tp_engine

logger = logging.getLogger('tradeportal.auth')

auth_router = APIRouter(tags=["Trade Portal"])


class LoginRequest(BaseModel):
    secCode: str
    password: str


class LoginResponse(BaseModel):
    secCode: str
    typeCode: Optional[str] = ""
    name: Optional[str] = ""
    isActive: Optional[bool] = True
    expirationDate: Optional[date] = None


@auth_router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest):
    try:
        with get_tp_engine().connect() as conn:
            row = conn.execute(
                text("SELECT * FROM dbo.SystemUser WHERE secCode = :sec_code"),
                {"sec_code": credentials.secCode}
            ).fetchone()

        if not row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        user = dict(row._mapping)

        if not user.get("isActive"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is inactive")

        decrypted_password = decrypt(user["password"])
        if decrypted_password != credentials.password:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        return LoginResponse(
            secCode=user["secCode"],
            typeCode=user.get("typeCode", ""),
            name=user.get("name", ""),
            isActive=user.get("isActive", True),
            expirationDate=user.get("expirationDate"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
