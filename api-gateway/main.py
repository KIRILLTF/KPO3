# api_gateway/main.py

import os
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx

app = FastAPI(title="API Gateway", version="0.1.0")

# Если ваш каталог называется api-gateway, то придётся запускать
#   uvicorn main:app --app-dir api-gateway ...
# Или лучше переименовать папку в api_gateway
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:8002")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8001")


async def get_user_id_header(request: Request) -> str:
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        raise HTTPException(status_code=400, detail="X-User-Id header missing")
    return user_id


class OrderCreate(BaseModel):
    amount: float
    description: str


class PaymentTopUp(BaseModel):
    user_id: int
    amount: float


@app.post(
    "/orders",
    dependencies=[Depends(get_user_id_header)],
    response_model=dict,
    summary="Create a new order",
)
async def create_order(
    order: OrderCreate,
    user_id: str = Depends(get_user_id_header),
):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{ORDER_SERVICE_URL}/orders",
            headers={"X-User-Id": user_id},
            json=order.dict(),
            timeout=10.0,
        )
    return JSONResponse(status_code=resp.status_code, content=resp.json())


@app.api_route(
    "/orders/{path:path}",
    methods=["GET", "PUT", "PATCH", "DELETE"],
    dependencies=[Depends(get_user_id_header)],
    summary="Proxy all other /orders/* calls",
)
async def orders_proxy(
    path: str,
    request: Request,
    user_id: str = Depends(get_user_id_header),
):
    url = f"{ORDER_SERVICE_URL}/orders/{path}"
    async with httpx.AsyncClient() as client:
        # для GET/DELETE — body не нужен, для остальных передаём JSON
        kwargs = {
            "method": request.method,
            "url": url,
            "headers": {"X-User-Id": user_id},
            "params": request.query_params,
            "timeout": 10.0,
        }
        if request.method in ("POST", "PUT", "PATCH"):
            kwargs["json"] = await request.json()
        resp = await client.request(**kwargs)

    # пытаемся читать JSON, иначе оставляем текст
    try:
        content = resp.json()
    except ValueError:
        content = resp.text
    return JSONResponse(status_code=resp.status_code, content=content)


@app.post(
    "/payments",
    dependencies=[Depends(get_user_id_header)],
    response_model=dict,
    summary="Top-up a user’s account",
)
async def create_topup(
    topup: PaymentTopUp,
    user_id: str = Depends(get_user_id_header),
):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{PAYMENT_SERVICE_URL}/payments/top-up",
            headers={"X-User-Id": user_id},
            json=topup.dict(),
            timeout=10.0,
        )
    return JSONResponse(status_code=resp.status_code, content=resp.json())


@app.api_route(
    "/payments/{path:path}",
    methods=["GET", "PUT", "PATCH", "DELETE"],
    dependencies=[Depends(get_user_id_header)],
    summary="Proxy all other /payments/* calls",
)
async def payments_proxy(
    path: str,
    request: Request,
    user_id: str = Depends(get_user_id_header),
):
    url = f"{PAYMENT_SERVICE_URL}/payments/{path}"
    async with httpx.AsyncClient() as client:
        kwargs = {
            "method": request.method,
            "url": url,
            "headers": {"X-User-Id": user_id},
            "params": request.query_params,
            "timeout": 10.0,
        }
        if request.method in ("POST", "PUT", "PATCH"):
            kwargs["json"] = await request.json()
        resp = await client.request(**kwargs)

    try:
        content = resp.json()
    except ValueError:
        content = resp.text
    return JSONResponse(status_code=resp.status_code, content=content)


@app.get("/health", tags=["Health"], summary="Gateway health check")
async def health():
    return {"status": "ok"}
