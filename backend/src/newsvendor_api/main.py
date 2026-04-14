import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .models import SimulationRequest
from .simulation import run_simulation

_DEFAULT_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://localhost:3000",
]

_allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
if _allowed_origins_env:
    _DEFAULT_ORIGINS = [origin.strip() for origin in _allowed_origins_env.split(",")]

app = FastAPI(
    title="Newsvendor Studio API",
    version="0.1.0",
    summary="Monte Carlo simulator and analytics for the classic newsvendor problem",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_DEFAULT_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/simulate")
def simulate(payload: SimulationRequest) -> dict[str, object]:
    return run_simulation(payload)
