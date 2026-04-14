from fastapi.testclient import TestClient

from newsvendor_api.main import app
from newsvendor_api.models import SimulationRequest
from newsvendor_api.simulation import (
    analytic_optimal_quantity,
    confidence_interval_half_width,
    distribution_bounds,
    expected_profit,
    run_simulation,
)


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


def test_analytic_quantity_maximizes_uniform_expected_profit() -> None:
    lower, upper = distribution_bounds(mean=150, half_width=30)
    analytic_quantity = analytic_optimal_quantity(0.25, 1.0, lower, upper)

    analytic_profit = expected_profit(analytic_quantity, 0.25, 1.0, lower, upper)
    nearby_profits = [
        expected_profit(quantity, 0.25, 1.0, lower, upper)
        for quantity in (150.0, 160.0, 170.0, 180.0)
    ]

    assert analytic_quantity == 165.0
    assert all(analytic_profit >= profit for profit in nearby_profits)


def test_confidence_interval_half_width_is_zero_for_single_value() -> None:
    assert confidence_interval_half_width([12.5]) == 0.0


def test_run_simulation_returns_confidence_interval_fields() -> None:
    response = run_simulation(
        SimulationRequest(
            purchase_cost=0.25,
            resale_value=1.0,
            average_demand=150,
            uniform_plus_minus=30,
            repetitions=4000,
            search_lower_quantity=100,
            search_upper_quantity=220,
            search_step=5,
            seed=17,
        )
    )

    recommendation = response["recommendation"]
    optimal_point = next(
        point
        for point in response["profit_curve"]
        if point["order_quantity"] == recommendation["optimal_order_quantity"]
    )

    assert recommendation["profit_ci_half_width"] > 0
    assert recommendation["profit_ci_lower"] <= recommendation["expected_profit_simulated"]
    assert recommendation["profit_ci_upper"] >= recommendation["expected_profit_simulated"]
    assert optimal_point["avg_profit_ci_half_width"] > 0
    assert optimal_point["avg_profit_ci_lower"] <= optimal_point["avg_profit"]
    assert optimal_point["avg_profit_ci_upper"] >= optimal_point["avg_profit"]
