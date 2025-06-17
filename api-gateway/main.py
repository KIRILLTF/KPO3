from fastapi import FastAPI, Request, HTTPException, Response
import httpx
from config import settings

app = FastAPI(
    title="API Gateway",
    description="Проксирует `/orders*` → Orders Service и `/payments*` → Payments Service",
)

@app.get("/")
async def root():
    return {"message": "API Gateway is up and running"}

@app.middleware("http")
async def require_user_id(request: Request, call_next):
    public = ("/", "/health", "/docs", "/openapi.json", "/redoc")
    if request.url.path in public:
        return await call_next(request)
    if "X-User-Id" not in request.headers:
        raise HTTPException(400, "X-User-Id header missing")
    return await call_next(request)

client = httpx.AsyncClient()

async def proxy(request: Request, target_base: str) -> Response:
    # убираем trailing slash, чтобы /orders/ → /orders, но /orders/1 → /orders/1
    path = request.url.path.rstrip('/')
    url = f"{target_base}{path}"
    resp = await client.request(
        method=request.method,
        url=url,
        headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
        params=request.query_params,
        content=await request.body(),
    )
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=dict(resp.headers),
        media_type=resp.headers.get("content-type"),
    )

# Проксируем всё, что начинается с /orders
@app.api_route("/orders", methods=["GET","POST","PUT","PATCH","DELETE"])
@app.api_route("/orders/{rest:path}", methods=["GET","POST","PUT","PATCH","DELETE"])
async def orders_proxy(request: Request, rest: str = ""):
    return await proxy(request, settings.ORDERS_SERVICE_URL)

# Проксируем всё, что начинается с /payments
@app.api_route("/payments", methods=["GET","POST","PUT","PATCH","DELETE"])
@app.api_route("/payments/{rest:path}", methods=["GET","POST","PUT","PATCH","DELETE"])
async def payments_proxy(request: Request, rest: str = ""):
    return await proxy(request, settings.PAYMENTS_SERVICE_URL)

@app.get("/health")
async def health():
    return {"status": "ok"}
