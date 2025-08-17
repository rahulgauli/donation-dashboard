from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
# from app.routers import _for_admin_, _for_public

app = FastAPI(
    title="secret-vault-service",
    description="Hashicorp vault namespace creation and management",
    version="0.0.1"
)

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

# app.include_router(_for_public.)
# app.include_router(_for_admin_)