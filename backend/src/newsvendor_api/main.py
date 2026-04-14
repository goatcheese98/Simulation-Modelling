from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .models import SimulationRequest
from .simulation import run_simulation

app = FastAPI(
    title="Newsvendor Studio API",
    version="0.1.0",
    summary="Monte Carlo simulator and analytics for the classic newsvendor problem",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
