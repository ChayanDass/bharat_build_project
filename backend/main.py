from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings, container
from backend.api.routes import router
from data.demo.seed_data import seed_demo_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database is seeded if empty on startup
    wards = container.ward_repo.list_wards()
    if not wards:
        seed_demo_data()
    yield


app = FastAPI(
    title="HeatOps API",
    description="Heat Response Command Centre API",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for React/Vite development & production frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
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
