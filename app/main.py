from fastapi import FastAPI, HTTPException
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
from app.routers._for_admin_ import admin_router

from app.middleware_token import BearerAuthASGIMiddleware
from app.security import creds, create_access_token


app = FastAPI(
    title="Dashboard Service",
    description="A dashboard service for managing donations and users.",
    version="0.0.1"
)

app.add_middleware(BearerAuthASGIMiddleware)

origins = [
    "http://localhost:3000"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def custom_openapi():
    """
    Generate the custom OpenAPI schema for the secret-vault-service API.

    :return: The OpenAPI schema.
    """

    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="dashboard-service",
        description="API for the dashboard service",
        version="0.0.1",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
app.include_router(admin_router)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 60 * 30  


@app.post("/auth/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    if not creds.verify_password(body.username, body.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(sub=body.username)
    return TokenResponse(access_token=token)

@app.get("/healthz")
async def health_check():
    """
    Health check endpoint to verify the service is running.
    """
    return {"status": "ok"}
