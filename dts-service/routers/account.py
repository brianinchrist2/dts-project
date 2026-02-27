from fastapi import APIRouter, Depends, HTTPException, Query

from dependencies import get_account_service
from services.account_service import AccountService
from models.schemas import AccountInfo, HistoryResponse

router = APIRouter(prefix="/api/account", tags=["account"])


@router.get("/info", response_model=AccountInfo)
async def get_account_info(svc: AccountService = Depends(get_account_service)):
    info = await svc.get_info()
    if info is None:
        raise HTTPException(status_code=503, detail="Cannot retrieve account info from MT5")
    return info


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    days: int = Query(default=30, ge=1, le=365),
    svc: AccountService = Depends(get_account_service),
):
    deals = await svc.get_history(days)
    return HistoryResponse(deals=deals)
