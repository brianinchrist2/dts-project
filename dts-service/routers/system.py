from fastapi import APIRouter, Depends

from config import settings
from dependencies import get_mt5, get_db
from mt5.connection import MT5Manager
from db.database import DatabaseManager
from models.schemas import HealthResponse, VersionResponse

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health(
    mt5: MT5Manager = Depends(get_mt5),
    db: DatabaseManager = Depends(get_db),
):
    db_ok = True
    try:
        db.fetchone("SELECT 1")
    except Exception:
        db_ok = False

    return HealthResponse(
        status="ok" if mt5.connected and db_ok else "degraded",
        mt5_connected=mt5.connected,
        db_ok=db_ok,
    )


@router.get("/version", response_model=VersionResponse)
async def version(mt5: MT5Manager = Depends(get_mt5)):
    mt5_ver = None
    try:
        ver = await mt5.version()
        if ver:
            mt5_ver = str(ver)
    except Exception:
        pass

    return VersionResponse(
        service_version=settings.version,
        mt5_version=mt5_ver,
    )
