export interface SimulationRequestPayload {
	purchase_cost: number;
	resale_value: number;
	average_demand: number;
	uniform_plus_minus: number;
	repetitions: number;
	search_lower_quantity: number;
	search_upper_quantity: number;
	search_step: number;
	policy_spread_multiplier: number;
	seed?: number | null;
}

export interface DistributionSummary {
	name: string;
	lower_bound: number;
	upper_bound: number;
	mean: number;
	spread: number;
}

export interface RecommendationSummary {
	optimal_order_quantity: number;
	optimal_avg_profit: number;
	critical_fractile: number;
	analytic_order_quantity: number;
	expected_profit_analytic: number;
	expected_profit_simulated: number;
	profit_ci_half_width: number;
	profit_ci_lower: number;
	profit_ci_upper: number;
	analytic_profit_simulated?: number | null;
	profit_p10: number;
	profit_p90: number;
	expected_units_sold: number;
	expected_leftover: number;
	expected_lost_sales: number;
	service_level: number;
	fill_rate: number;
}

export interface PolicyResult {
	key: string;
	label: string;
	order_quantity: number;
	avg_profit: number;
	profit_ci_half_width: number;
	profit_ci_lower: number;
	profit_ci_upper: number;
	profit_p10: number;
	profit_p90: number;
	avg_leftover: number;
	avg_lost_sales: number;
	stockout_rate: number;
	fill_rate: number;
}

export interface ProfitCurvePoint {
	order_quantity: number;
	avg_profit: number;
	avg_profit_ci_half_width: number;
	avg_profit_ci_lower: number;
	avg_profit_ci_upper: number;
	analytic_profit: number;
}

export interface SearchWindowSummary {
	lower_quantity: number;
	upper_quantity: number;
	step: number;
	candidate_count: number;
}

export interface SampleRun {
	rep: number;
	demand: number;
	sold: number;
	leftover: number;
	lost_sales: number;
	profit: number;
}

export interface ProfitHistogramBin {
	bin_start: number;
	bin_end: number;
	count: number;
	share: number;
}

export interface SimulationResponse {
	inputs: SimulationRequestPayload & { seed?: number | null };
	distribution: DistributionSummary;
	search_window: SearchWindowSummary;
	recommendation: RecommendationSummary;
	policy_comparison: PolicyResult[];
	profit_curve: ProfitCurvePoint[];
	profit_histogram: ProfitHistogramBin[];
	sample_runs: SampleRun[];
}

export const defaultScenario: SimulationRequestPayload = {
	purchase_cost: 0.25,
	resale_value: 1,
	average_demand: 150,
	uniform_plus_minus: 30,
	repetitions: 5000,
	search_lower_quantity: 100,
	search_upper_quantity: 220,
	search_step: 5,
	policy_spread_multiplier: 0.45,
	seed: null
};
