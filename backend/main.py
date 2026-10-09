from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings, container
from backend.api.routes import router
from data.demo.seed_data import seed_demo_data
from backend.security.cognito_identity import CognitoIdentityMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.SEED_DEMO_DATA and not container.ward_repo.list_wards():
        seed_demo_data()
    yield


app = FastAPI(
    title="HeatOps API",
    description="Heat Response Command Centre API",
    version="1.0.0",
    lifespan=lifespan
)

if settings.AUTHENTICATION_PROVIDER == "cognito":
    app.add_middleware(CognitoIdentityMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in settings.CORS_ALLOWED_ORIGINS.split(",")
        if origin.strip()
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "system": "HeatOps Command Centre",
        "environment": settings.ENVIRONMENT,
        "llm_provider": settings.LLM_PROVIDER,
        "database_provider": settings.DATABASE_PROVIDER
    }


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
