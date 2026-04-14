from __future__ import annotations

from dataclasses import dataclass
from math import isclose, sqrt
import random
import statistics

from .models import SimulationRequest


@dataclass(frozen=True)
class Policy:
    key: str
    label: str
    order_quantity: float


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]

    raw_index = clamp(p, 0.0, 1.0) * (len(ordered) - 1)
    lower_index = int(raw_index)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    fraction = raw_index - lower_index
    return ordered[lower_index] + (ordered[upper_index] - ordered[lower_index]) * fraction


def confidence_interval_half_width(sample_values: list[float], confidence_level: float = 0.95) -> float:
    if len(sample_values) < 2:
        return 0.0

    sample_stdev = statistics.stdev(sample_values)
    # Normal approximation is sufficient for the simulation sample sizes used in the app.
    z_value = statistics.NormalDist().inv_cdf(0.5 + (confidence_level / 2))
    return z_value * sample_stdev / sqrt(len(sample_values))


def distribution_bounds(mean: float, half_width: float) -> tuple[float, float]:
    return max(0.0, mean - half_width), max(0.0, mean + half_width)


def expected_units_sold(order_quantity: float, lower: float, upper: float) -> float:
    if isclose(lower, upper):
        return min(order_quantity, upper)

    if order_quantity <= lower:
        return max(0.0, order_quantity)

    if order_quantity >= upper:
        return (lower + upper) / 2

    width = upper - lower
    return ((2 * order_quantity * upper) - (order_quantity**2) - (lower**2)) / (2 * width)


def expected_profit(
    order_quantity: float,
    purchase_cost: float,
    resale_value: float,
    lower: float,
    upper: float,
) -> float:
    return resale_value * expected_units_sold(order_quantity, lower, upper) - purchase_cost * order_quantity


def analytic_optimal_quantity(
    purchase_cost: float,
    resale_value: float,
    lower: float,
    upper: float,
) -> float:
    if resale_value <= purchase_cost:
        return 0.0

    if isclose(lower, upper):
        return upper

    critical_fractile = clamp(1 - (purchase_cost / resale_value), 0.0, 1.0)
    return lower + critical_fractile * (upper - lower)


def demand_draws(mean: float, half_width: float, repetitions: int, seed: int | None) -> list[float]:
    rng = random.Random(seed)
    lower, upper = distribution_bounds(mean, half_width)
    if isclose(lower, upper):
        return [upper for _ in range(repetitions)]
    return [rng.uniform(lower, upper) for _ in range(repetitions)]


def summarize_policy(
    policy: Policy,
    demands: list[float],
    purchase_cost: float,
    resale_value: float,
) -> dict[str, float | str]:
    profits: list[float] = []
    leftovers: list[float] = []
    lost_sales: list[float] = []
    sold_units: list[float] = []
    stockouts = 0

    for demand in demands:
        sold = min(policy.order_quantity, demand)
        leftover = max(policy.order_quantity - demand, 0.0)
        missed = max(demand - policy.order_quantity, 0.0)
        profit = sold * resale_value - policy.order_quantity * purchase_cost

        profits.append(profit)
        leftovers.append(leftover)
        lost_sales.append(missed)
        sold_units.append(sold)
        stockouts += int(missed > 0)

    mean_demand = statistics.fmean(demands) if demands else 0.0
    mean_sold = statistics.fmean(sold_units) if sold_units else 0.0
    avg_profit = statistics.fmean(profits) if profits else 0.0
    profit_ci_half_width = confidence_interval_half_width(profits)

    return {
        "key": policy.key,
        "label": policy.label,
        "order_quantity": round(policy.order_quantity, 2),
        "avg_profit": round(avg_profit, 4),
        "profit_ci_half_width": round(profit_ci_half_width, 4),
        "profit_ci_lower": round(avg_profit - profit_ci_half_width, 4),
        "profit_ci_upper": round(avg_profit + profit_ci_half_width, 4),
        "profit_p10": round(percentile(profits, 0.10), 4),
        "profit_p90": round(percentile(profits, 0.90), 4),
        "avg_leftover": round(statistics.fmean(leftovers) if leftovers else 0.0, 4),
        "avg_lost_sales": round(statistics.fmean(lost_sales) if lost_sales else 0.0, 4),
        "stockout_rate": round(stockouts / len(demands), 4) if demands else 0.0,
        "fill_rate": round((mean_sold / mean_demand) if mean_demand > 0 else 1.0, 4),
    }


def build_policy_set(optimal_quantity: float, average_demand: float, spread: float, multiplier: float = 0.45) -> list[Policy]:
    policy_candidates = [
        Policy("optimal", "Optimal order", optimal_quantity),
        Policy("mean", "Order the mean", average_demand),
        Policy("lean", "Lean inventory", max(0.0, optimal_quantity - (spread * multiplier))),
        Policy("buffered", "Buffer inventory", optimal_quantity + (spread * multiplier)),
    ]

    deduped: list[Policy] = []
    seen: set[float] = set()
    for policy in policy_candidates:
        rounded_quantity = round(policy.order_quantity, 4)
        if rounded_quantity in seen:
            continue
        seen.add(rounded_quantity)
        deduped.append(policy)

    return deduped


def quantity_grid(lower: float, upper: float, step: float) -> list[float]:
    if upper < lower:
        return []

    quantities: list[float] = []
    current = lower
    epsilon = step / 1000

    while current <= upper + epsilon:
        quantities.append(round(current, 4))
        current += step

    if quantities and quantities[-1] > upper + epsilon:
        quantities.pop()

    if not quantities or not isclose(quantities[-1], upper):
        quantities.append(round(upper, 4))

    deduped: list[float] = []
    seen: set[float] = set()
    for quantity in quantities:
        marker = round(quantity, 4)
        if marker in seen:
            continue
        seen.add(marker)
        deduped.append(marker)

    return deduped


def profit_curve(
    demands: list[float],
    search_lower: float,
    search_upper: float,
    search_step: float,
    purchase_cost: float,
    resale_value: float,
    lower_demand: float,
    upper_demand: float,
) -> list[dict[str, float]]:
    curve: list[dict[str, float]] = []

    for quantity in quantity_grid(search_lower, search_upper, search_step):
        policy = summarize_policy(
            Policy(key=f"search-{quantity}", label=f"Search {quantity}", order_quantity=quantity),
            demands,
            purchase_cost,
            resale_value,
        )
        curve.append(
            {
                "order_quantity": round(quantity, 2),
                "avg_profit": float(policy["avg_profit"]),
                "avg_profit_ci_half_width": float(policy["profit_ci_half_width"]),
                "avg_profit_ci_lower": float(policy["profit_ci_lower"]),
                "avg_profit_ci_upper": float(policy["profit_ci_upper"]),
                "analytic_profit": round(
                    expected_profit(quantity, purchase_cost, resale_value, lower_demand, upper_demand),
                    4,
                ),
            }
        )

    return curve


def sample_runs(
    demands: list[float],
    order_quantity: float,
    purchase_cost: float,
    resale_value: float,
    count: int = 8,
) -> list[dict[str, float | int]]:
    runs: list[dict[str, float | int]] = []
    for index, demand in enumerate(demands[:count], start=1):
        sold = min(order_quantity, demand)
        leftover = max(order_quantity - demand, 0.0)
        missed = max(demand - order_quantity, 0.0)
        profit = sold * resale_value - order_quantity * purchase_cost

        runs.append(
            {
                "rep": index,
                "demand": round(demand, 2),
                "sold": round(sold, 2),
                "leftover": round(leftover, 2),
                "lost_sales": round(missed, 2),
                "profit": round(profit, 2),
            }
        )

    return runs


def run_simulation(payload: SimulationRequest) -> dict[str, object]:
    lower_demand, upper_demand = distribution_bounds(payload.average_demand, payload.uniform_plus_minus)
    analytic_quantity = analytic_optimal_quantity(
        purchase_cost=payload.purchase_cost,
        resale_value=payload.resale_value,
        lower=lower_demand,
        upper=upper_demand,
    )
    demands = demand_draws(
        mean=payload.average_demand,
        half_width=payload.uniform_plus_minus,
        repetitions=payload.repetitions,
        seed=payload.seed,
    )
    curve = profit_curve(
        demands=demands,
        search_lower=payload.search_lower_quantity,
        search_upper=payload.search_upper_quantity,
        search_step=payload.search_step,
        purchase_cost=payload.purchase_cost,
        resale_value=payload.resale_value,
        lower_demand=lower_demand,
        upper_demand=upper_demand,
    )
    best_curve_point = max(curve, key=lambda point: (point["avg_profit"], -point["order_quantity"]))
    best_quantity = float(best_curve_point["order_quantity"])
    policies = build_policy_set(
        optimal_quantity=best_quantity,
        average_demand=payload.average_demand,
        spread=payload.uniform_plus_minus,
        multiplier=payload.policy_spread_multiplier,
    )
    policies.insert(1, Policy("analytic", "Analytic critical-fractile", analytic_quantity))
    policy_comparison = [
        summarize_policy(policy, demands, payload.purchase_cost, payload.resale_value) for policy in policies
    ]
    optimal_policy = next(item for item in policy_comparison if item["key"] == "optimal")
    analytic_policy = next((item for item in policy_comparison if item["key"] == "analytic"), None)
    optimal_analytic_profit = expected_profit(
        analytic_quantity,
        payload.purchase_cost,
        payload.resale_value,
        lower_demand,
        upper_demand,
    )
    expected_units = expected_units_sold(best_quantity, lower_demand, upper_demand)

    return {
        "inputs": payload.model_dump(),
        "distribution": {
            "name": "uniform",
            "lower_bound": round(lower_demand, 2),
            "upper_bound": round(upper_demand, 2),
            "mean": round((lower_demand + upper_demand) / 2, 2),
            "spread": round(payload.uniform_plus_minus, 2),
        },
        "search_window": {
            "lower_quantity": round(payload.search_lower_quantity, 2),
            "upper_quantity": round(payload.search_upper_quantity, 2),
            "step": round(payload.search_step, 2),
            "candidate_count": len(curve),
        },
        "recommendation": {
            "optimal_order_quantity": round(best_quantity, 2),
            "optimal_avg_profit": round(float(best_curve_point["avg_profit"]), 4),
            "critical_fractile": round(
                clamp(1 - (payload.purchase_cost / payload.resale_value), 0.0, 1.0),
                4,
            ),
            "analytic_order_quantity": round(analytic_quantity, 2),
            "expected_profit_analytic": round(optimal_analytic_profit, 4),
            "expected_profit_simulated": optimal_policy["avg_profit"],
            "profit_ci_half_width": optimal_policy["profit_ci_half_width"],
            "profit_ci_lower": optimal_policy["profit_ci_lower"],
            "profit_ci_upper": optimal_policy["profit_ci_upper"],
            "profit_p10": optimal_policy["profit_p10"],
            "profit_p90": optimal_policy["profit_p90"],
            "analytic_profit_simulated": analytic_policy["avg_profit"] if analytic_policy else None,
            "expected_units_sold": round(expected_units, 4),
            "expected_leftover": round(max(best_quantity - expected_units, 0.0), 4),
            "expected_lost_sales": round(max(payload.average_demand - expected_units, 0.0), 4),
            "service_level": round(1 - float(optimal_policy["stockout_rate"]), 4),
            "fill_rate": optimal_policy["fill_rate"],
        },
        "policy_comparison": policy_comparison,
        "profit_curve": curve,
        "sample_runs": sample_runs(
            demands=demands,
            order_quantity=best_quantity,
            purchase_cost=payload.purchase_cost,
            resale_value=payload.resale_value,
        ),
    }
