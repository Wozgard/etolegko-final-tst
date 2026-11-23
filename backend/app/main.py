import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.campaigns import router as campaigns_router
from app.api.mock import router as mock_router
from app.config import mock_database_path, settings
from app.db import engine


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    yield
    if settings.keitaro_mock and "pytest" not in sys.modules:
        engine.dispose()
        mock_db = mock_database_path()
        if mock_db.is_file():
            mock_db.unlink()


app = FastAPI(lifespan=_lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(campaigns_router)
app.include_router(mock_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}