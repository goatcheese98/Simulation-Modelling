from fastapi.testclient import TestClient

from newsvendor_api.main import app
from newsvendor_api.models import SimulationRequest
from newsvendor_api.simulation import analytic_optimal_quantity, distribution_bounds, run_simulation


client = TestClient(app)


def test_analytic_optimal_quantity_defaults_to_zero_when_margin_is_negative() -> None:
    lower, upper = distribution_bounds(mean=150, half_width=30)
    assert analytic_optimal_quantity(1.25, 1.0, lower, upper) == 0.0


def test_run_simulation_returns_expected_default_recommendation() -> None:
    response = run_simulation(
        SimulationRequest(
            purchase_cost=0.25,
            resale_value=1.0,
            average_demand=150,
            uniform_plus_minus=30,
            repetitions=2500,
            search_lower_quantity=100,
            search_upper_quantity=220,
            search_step=5,
            seed=11,
        )
    )

    recommendation = response["recommendation"]

    assert recommendation["analytic_order_quantity"] == 165.0
    assert recommendation["critical_fractile"] == 0.75
    assert recommendation["expected_profit_analytic"] > 100
    assert recommendation["optimal_order_quantity"] >= 100
    assert recommendation["optimal_order_quantity"] <= 220
    assert response["search_window"]["candidate_count"] == len(response["profit_curve"])
    assert len(response["policy_comparison"]) >= 4


def test_simulate_endpoint_responds_with_structured_payload() -> None:
    result = client.post(
        "/api/simulate",
        json={
            "purchase_cost": 0.25,
            "resale_value": 1.0,
            "average_demand": 150,
            "uniform_plus_minus": 30,
            "repetitions": 1200,
            "search_lower_quantity": 120,
            "search_upper_quantity": 210,
            "search_step": 10,
            "seed": 7,
        },
    )

    assert result.status_code == 200
    body = result.json()
    assert body["distribution"]["lower_bound"] == 120.0
    assert body["search_window"]["step"] == 10.0
    assert body["recommendation"]["analytic_order_quantity"] == 165.0
    assert body["sample_runs"][0]["rep"] == 1
