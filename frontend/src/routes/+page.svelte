<script lang="ts">
	import { onMount } from 'svelte';

	import { simulateNewsvendor } from '$lib/api';
	import PolicyComparison from '$lib/components/PolicyComparison.svelte';
	import ProfitCurve from '$lib/components/ProfitCurve.svelte';
	import Tooltip from '$lib/components/Tooltip.svelte';
	import { defaultScenario, type SimulationRequestPayload, type SimulationResponse } from '$lib/types';

	let scenario = $state<SimulationRequestPayload>({ ...defaultScenario });
	let result = $state<SimulationResponse | null>(null);
	let isLoading = $state(false);
	let errorMessage = $state('');
	let hasRequestedSimulation = $state(false);
	let darkMode = $state(false);
	let replayKey = $state(0);

	const demandLower = $derived.by(() => Math.max(scenario.average_demand - scenario.uniform_plus_minus, 0));
	const demandUpper = $derived.by(() => Math.max(scenario.average_demand + scenario.uniform_plus_minus, 0));
	const searchSpan = $derived.by(
		() => Math.max(scenario.search_upper_quantity - scenario.search_lower_quantity, 0)
	);
	const candidateCount = $derived.by(
		() => Math.floor(searchSpan / Math.max(scenario.search_step, 0.0001)) + 1
	);
	const margin = $derived.by(() => Math.max(scenario.resale_value - scenario.purchase_cost, 0));
	const quantityOverlapState = $derived.by(() => {
		if (!result) {
			return null;
		}

		const recommended = result.recommendation.optimal_order_quantity;
		const analytic = result.recommendation.analytic_order_quantity;
		const tolerance = Math.max(scenario.search_step / 2, 0.05);
		const difference = Math.abs(recommended - analytic);

		return {
			recommended,
			analytic,
			difference,
			overlaps: difference <= tolerance
		};
	});

	onMount(() => {
		const stored = typeof localStorage !== 'undefined' ? localStorage.getItem('theme') : null;
		if (stored) {
			darkMode = stored === 'dark';
		} else if (typeof window !== 'undefined') {
			darkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
		}
		applyTheme();
		void runSimulation();
	});

	function applyTheme() {
		if (typeof document !== 'undefined') {
			document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : 'light');
			localStorage.setItem('theme', darkMode ? 'dark' : 'light');
		}
	}

	function toggleTheme() {
		darkMode = !darkMode;
		applyTheme();
	}

	let debounceTimer: ReturnType<typeof setTimeout> | null = null;
	$effect(() => {
		void scenario.purchase_cost;
		void scenario.resale_value;
		void scenario.average_demand;
		void scenario.uniform_plus_minus;
		void scenario.repetitions;
		void scenario.search_lower_quantity;
		void scenario.search_upper_quantity;
		void scenario.search_step;
		void scenario.policy_spread_multiplier;
		if (debounceTimer) clearTimeout(debounceTimer);
		debounceTimer = setTimeout(() => {
			void runSimulation();
		}, 500);
		return () => {
			if (debounceTimer) clearTimeout(debounceTimer);
		};
	});

	async function runSimulation() {
		hasRequestedSimulation = true;
		isLoading = true;
		errorMessage = '';

		if (scenario.seed == null) {
			scenario.seed = Math.floor(Math.random() * 1_000_000_000);
		}

		try {
			result = await simulateNewsvendor(scenario);
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'Simulation failed';
		} finally {
			isLoading = false;
		}
	}

	function resetDefaults() {
		scenario = { ...defaultScenario };
		void runSimulation();
	}

	function currency(value: number | null | undefined): string {
		if (value == null) {
			return 'N/A';
		}
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			maximumFractionDigits: 2
		}).format(value);
	}

	function percent(value: number): string {
		return `${(value * 100).toFixed(1)}%`;
	}
</script>

<svelte:head>
	<title>Newsvendor Studio</title>
	<meta
		name="description"
		content="Professional newsvendor simulation with a SvelteKit interface and Python backend."
	/>
</svelte:head>

<div class="page">
	<section class="masthead">
		<div class="masthead-left">
			<p class="eyebrow">Newsvendor Studio</p>
			<h1>Inventory policy analysis</h1>
		</div>
		<div class="masthead-right">
			<button
				class="theme-button"
				type="button"
				onclick={toggleTheme}
				aria-label={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
				title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
			>
				{#if darkMode}
					<svg viewBox="0 0 24 24" aria-hidden="true">
						<circle cx="12" cy="12" r="4.2" />
						<path d="M12 2.75v2.5M12 18.75v2.5M21.25 12h-2.5M5.25 12H2.75M18.55 5.45l-1.8 1.8M7.25 16.75l-1.8 1.8M18.55 18.55l-1.8-1.8M7.25 7.25l-1.8-1.8" />
					</svg>
				{:else}
					<svg viewBox="0 0 24 24" aria-hidden="true">
						<path
							d="M20.25 14.2A8.55 8.55 0 1 1 9.8 3.75a7.05 7.05 0 0 0 10.45 10.45Z"
						/>
					</svg>
				{/if}
			</button>
		</div>
	</section>

	<section class="layout">
		<form class="controls" onsubmit={(e) => e.preventDefault()}>
			<div class="panel-head">
				<div>
					<p class="eyebrow">Scenario</p>
					<h2>Decision inputs</h2>
				</div>
				<button class="ghost-button" type="button" onclick={resetDefaults}>Reset</button>
			</div>

			<div class="control-group">
				<div class="group-head">
					<h3>Economics</h3>
				</div>
				<div class="field-grid">
					<label class="field">
						<span>Purchase cost <Tooltip hint="Cost to acquire one unit." /></span>
						<input bind:value={scenario.purchase_cost} type="number" min="0.01" step="0.01" />
					</label>
					<label class="field">
						<span>Resale value <Tooltip hint="Revenue from selling one unit." /></span>
						<input bind:value={scenario.resale_value} type="number" min="0.01" step="0.01" />
					</label>
				</div>
				<div class="mini-stats">
					<div>
						<span>Unit margin <Tooltip hint="Profit per unit sold: resale value minus purchase cost." /></span>
						<strong>{currency(margin)}</strong>
					</div>
				</div>
			</div>

			<div class="control-group">
				<div class="group-head">
					<h3>Demand model</h3>
				</div>
				<div class="field-grid">
					<label class="field">
						<span>Average demand</span>
						<input bind:value={scenario.average_demand} type="number" min="0" step="1" />
					</label>
					<label class="field">
						<span>Uniform +/- <Tooltip hint="Demand is uniformly distributed between average minus this value and average plus this value." /></span>
						<input bind:value={scenario.uniform_plus_minus} type="number" min="0" step="1" />
					</label>
				</div>
				<div class="mini-stats">
					<div>
						<span>Demand band</span>
						<strong>{demandLower.toFixed(0)} to {demandUpper.toFixed(0)}</strong>
					</div>
				</div>
			</div>

			<div class="control-group">
				<div class="group-head">
					<h3>Order quantity search</h3>
				</div>
				<div class="field-grid field-grid-wide">
					<label class="field">
						<span>Lower limit <Tooltip hint="Smallest order quantity to evaluate." /></span>
						<input bind:value={scenario.search_lower_quantity} type="number" min="0" step="1" />
					</label>
					<label class="field">
						<span>Upper limit <Tooltip hint="Largest order quantity to evaluate." /></span>
						<input bind:value={scenario.search_upper_quantity} type="number" min="0" step="1" />
					</label>
					<label class="field">
						<span>Step size <Tooltip hint="Increment between consecutive order quantities in the search grid." /></span>
						<input bind:value={scenario.search_step} type="number" min="0.1" step="0.1" />
					</label>
					<label class="field">
						<span>Monte Carlo simulations <Tooltip hint="Number of random demand scenarios used to estimate average profit and service metrics." /></span>
						<input bind:value={scenario.repetitions} type="number" min="100" max="250000" step="100" />
					</label>
				</div>
				<div class="mini-stats">
					<div>
						<span>Grid points <Tooltip hint="How many different order quantities will be evaluated between the lower and upper limits." /></span>
						<strong>{candidateCount}</strong>
					</div>
				</div>
			</div>

			{#if errorMessage}
				<p class="error">{errorMessage}</p>
			{/if}
		</form>

		<div class="results">
			{#if result}
				<section class="summary">
					<div class="summary-main">
						<p class="eyebrow">Recommended policy</p>
						<h2>{result.recommendation.optimal_order_quantity.toFixed(1)} units</h2>
						<p>
							The simulation-optimal quantity from the tested search grid delivers
							<strong>{currency(result.recommendation.expected_profit_simulated)}</strong>
							expected profit at a
							<strong>{percent(result.recommendation.service_level)}</strong>
							<Tooltip hint="Probability that demand does not exceed the order quantity (i.e., no stockout)." />
							service level.
						</p>
					</div>

					<div class="summary-grid">
						<article>
							<span
								>Simulation-optimal profit <Tooltip
									hint="The highest average simulated profit achieved by any tested order quantity in the search window. This is how the simulation-optimal quantity is chosen."
								/></span
							>
							<strong>{currency(result.recommendation.optimal_avg_profit)}</strong>
						</article>
						<article>
							<span
								>Analytic qty <Tooltip
									hint="The formula-based order quantity from the classic newsvendor critical fractile. It is a theoretical optimum under the demand model, not necessarily the exact best point on the simulated search grid."
								/></span
							>
							<strong>{result.recommendation.analytic_order_quantity.toFixed(1)} units</strong>
						</article>
						<article>
							<span
								>Analytic profit <Tooltip
									hint="The theoretical expected profit for the analytic order quantity."
								/></span
							>
							<strong>{currency(result.recommendation.expected_profit_analytic)}</strong>
						</article>
						<article>
							<span
								>Simulated 90% band <Tooltip
									hint="The range from the 10th to the 90th percentile of simulated profit outcomes."
								/></span
							>
							<strong>{currency(result.recommendation.profit_p10)} to {currency(result.recommendation.profit_p90)}</strong>
						</article>

					</div>
				</section>

				<section class="metric-ribbon">
					<article>
						<span
							>Expected units sold <Tooltip
								hint="Average number of units sold per simulation run for the simulation-optimal quantity."
							/></span
						>
						<strong>{result.recommendation.expected_units_sold.toFixed(1)}</strong>
					</article>
					<article>
						<span
							>Expected leftover <Tooltip
								hint="Average unsold inventory remaining at the end of each period for the simulation-optimal quantity."
							/></span
						>
						<strong>{result.recommendation.expected_leftover.toFixed(1)}</strong>
					</article>
					<article>
						<span
							>Expected lost sales <Tooltip
								hint="Average demand that could not be satisfied because stock ran out for the simulation-optimal quantity."
							/></span
						>
						<strong>{result.recommendation.expected_lost_sales.toFixed(1)}</strong>
					</article>
					<article>
						<span
							>Fill rate <Tooltip
								hint="Percentage of total demand satisfied immediately from on-hand inventory in a given period for the simulation-optimal quantity."
							/></span
						>
						<strong>{percent(result.recommendation.fill_rate)}</strong>
					</article>
					<article>
						<span
							>Critical fractile <Tooltip
								hint="The target service level from the classic newsvendor formula: unit margin / (unit margin + unit cost). It corresponds to the formula-based analytic quantity, not the simulation-optimal quantity."
							/></span
						>
						<strong>{percent(result.recommendation.critical_fractile)}</strong>
					</article>
				</section>

				<div class="card-grid">
					<article class="card chart-card">
						<div class="card-head">
							<div>
								<p class="eyebrow">Profit curve</p>
								<h3>Average profit vs order quantity</h3>
							</div>
							<p class="chart-hint">
								<Tooltip
									hint="The solid line shows simulated profit over the search grid. The dashed line shows the analytic expected profit curve. Hover over the vertical reference lines for details."
								/>
							</p>
						</div>
						<ProfitCurve
							points={result.profit_curve}
							recommendedQuantity={result.recommendation.optimal_order_quantity}
							analyticQuantity={result.recommendation.analytic_order_quantity}
							meanDemand={result.distribution.mean}
							darkMode={darkMode}
							replayKey={replayKey}
						/>
						<div class="chart-footer">
							<p>Animation replays only when you trigger it.</p>
							<button
								class="play-button"
								type="button"
								onclick={() => replayKey++}
								aria-label="Replay animation"
							>
								Play animation
							</button>
						</div>
					</article>
				</div>

				<div class="card-grid card-grid-secondary">
					<article class="card policy-card">
						<div class="card-head">
							<div>
								<p class="eyebrow">Policy comparison</p>
							</div>
						</div>
						<PolicyComparison policies={result.policy_comparison} title="Compare policies" />
						<div class="policy-footer">
							<div class="slider-field">
								<div class="slider-head">
									<span>Deviation factor</span>
									<strong>{scenario.policy_spread_multiplier.toFixed(2)}</strong>
								</div>
								<input
									bind:value={scenario.policy_spread_multiplier}
									type="range"
									min="0"
									max="1"
									step="0.05"
								/>
								<p class="slider-hint">
									Lean and buffer quantities are computed as Optimal ± (demand half-width × deviation factor). Demand half-width is the <em>Uniform ±</em> value ({scenario.uniform_plus_minus.toFixed(0)} units).
								</p>
							</div>
						</div>
					</article>
				</div>
			{:else if isLoading}
				<section class="empty">
					<h2>Running the baseline simulation</h2>
					<p>Loading the default scenario so the optimization charts and policy comparisons can populate.</p>
				</section>
			{:else if errorMessage}
				<section class="empty">
					<h2>Simulation unavailable</h2>
					<p>The baseline run could not reach the simulation API. Update the connection and retry.</p>
					<button class="ghost-button" type="button" onclick={() => void runSimulation()}>
						Retry baseline scenario
					</button>
				</section>
			{:else}
				<section class="empty">
					<h2>{hasRequestedSimulation ? 'Preparing the next simulation' : 'Simulation runs automatically'}</h2>
					<p>
						{hasRequestedSimulation
							? 'Adjust any input to rerun the analysis with the updated scenario.'
							: 'The default scenario runs on page load, and any input change reruns the analysis automatically.'}
					</p>
					<button class="ghost-button" type="button" onclick={() => void runSimulation()}>
						Run baseline scenario
					</button>
				</section>
			{/if}
		</div>
	</section>
</div>

<style>
	.page {
		display: grid;
		gap: 0.6rem;
		padding: 0.6rem;
	}

	.masthead {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.75rem;
		padding: 0.5rem 0.75rem;
		border: 1px solid rgba(19, 34, 31, 0.08);
		border-radius: 0.85rem;
		background:
			linear-gradient(180deg, rgba(255, 252, 246, 0.98), rgba(249, 242, 231, 0.96)),
			linear-gradient(90deg, rgba(15, 118, 110, 0.06), rgba(215, 107, 48, 0.04));
		box-shadow: 0 12px 32px rgba(23, 36, 34, 0.06);
	}

	:global([data-theme='dark']) .masthead {
		background:
			linear-gradient(180deg, rgba(24, 34, 32, 0.98), rgba(15, 20, 19, 0.94)),
			linear-gradient(90deg, rgba(45, 212, 191, 0.08), rgba(232, 139, 82, 0.07));
		border-color: rgba(255, 255, 255, 0.08);
	}

	.masthead-left {
		display: flex;
		flex-direction: column;
		gap: 0.15rem;
	}

	.eyebrow {
		font-size: 0.65rem;
		font-weight: 700;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		color: var(--teal);
	}

	h1 {
		margin: 0;
		font-family: 'Newsreader', Georgia, serif;
		font-size: clamp(1.2rem, 2.2vw, 1.7rem);
		line-height: 1.1;
		letter-spacing: -0.02em;
	}

	.masthead-right {
		display: flex;
		align-items: center;
		gap: 0.55rem;
	}

	.theme-button {
		width: 2.5rem;
		height: 2.5rem;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0;
		border-radius: 999px;
		border: 1px solid rgba(19, 34, 31, 0.16);
		background: rgba(255, 255, 255, 0.92);
		color: var(--accent);
		box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35);
	}

	:global([data-theme='dark']) .theme-button {
		background: rgba(12, 18, 17, 0.92);
		color: #ffd166;
		border-color: rgba(255, 255, 255, 0.14);
		box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
	}

	.theme-button svg {
		width: 1.2rem;
		height: 1.2rem;
		stroke: currentColor;
		fill: none;
		stroke-width: 1.9;
		stroke-linecap: round;
		stroke-linejoin: round;
	}

	.theme-button:hover {
		transform: translateY(-1px);
		box-shadow:
			0 8px 18px rgba(15, 118, 110, 0.16),
			inset 0 1px 0 rgba(255, 255, 255, 0.4);
	}

	:global([data-theme='dark']) .theme-button:hover {
		box-shadow:
			0 8px 18px rgba(0, 0, 0, 0.28),
			inset 0 1px 0 rgba(255, 255, 255, 0.08);
	}

	.layout {
		display: grid;
		grid-template-columns: minmax(16rem, 19rem) minmax(0, 1fr);
		gap: 0.75rem;
		align-items: start;
	}

	.controls,
	.summary,
	.card,
	.empty {
		border: 1px solid rgba(19, 34, 31, 0.08);
		border-radius: 1rem;
		background: rgba(255, 252, 246, 0.82);
		box-shadow: 0 10px 28px rgba(23, 36, 34, 0.05);
		backdrop-filter: blur(10px);
	}

	:global([data-theme='dark']) .controls,
	:global([data-theme='dark']) .summary,
	:global([data-theme='dark']) .card,
	:global([data-theme='dark']) .empty {
		background: rgba(20, 28, 26, 0.82);
		border-color: rgba(255, 255, 255, 0.08);
	}

	.controls {
		display: grid;
		gap: 0.7rem;
		padding: 0.75rem;
		position: sticky;
		top: 0.6rem;
		height: fit-content;
		align-self: start;
	}

	.panel-head,
	.card-head {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 0.75rem;
	}

	h2,
	h3 {
		margin: 0.15rem 0 0;
		font-size: 1.05rem;
		line-height: 1.12;
	}

	.group-head h3 {
		font-size: 0.92rem;
		margin-top: 0;
	}

	.card-head p,
	.summary-main p,
	.empty p {
		margin: 0.15rem 0 0;
		font-size: 0.8rem;
		color: var(--ink-soft);
		line-height: 1.45;
	}

	.control-group {
		display: grid;
		gap: 0.55rem;
		padding: 0.6rem;
		border-radius: 0.85rem;
		background: rgba(255, 255, 255, 0.68);
		border: 1px solid rgba(19, 34, 31, 0.06);
	}

	:global([data-theme='dark']) .control-group,
	:global([data-theme='dark']) .mini-stats div,
	:global([data-theme='dark']) .summary-grid article,
	:global([data-theme='dark']) .metric-ribbon article {
		background: rgba(0, 0, 0, 0.25);
		border-color: rgba(255, 255, 255, 0.06);
	}

	.field-grid {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 0.55rem;
	}

	.field-grid-wide {
		grid-template-columns: repeat(2, minmax(0, 1fr));
	}

	.field {
		display: grid;
		gap: 0.28rem;
	}

	.field span,
	.mini-stats span,
	.summary-grid span,
	.metric-ribbon span {
		font-size: 0.68rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--ink-soft);
	}

	input {
		width: 100%;
		padding: 0.5rem 0.65rem;
		border: 1px solid rgba(19, 34, 31, 0.12);
		border-radius: 0.7rem;
		background: rgba(255, 255, 255, 0.9);
		color: var(--ink);
		font-size: 0.88rem;
	}

	:global([data-theme='dark']) input {
		background: rgba(0, 0, 0, 0.3);
		border-color: rgba(255, 255, 255, 0.1);
		color: var(--ink);
	}

	input:focus,
	button:focus {
		outline: 2px solid rgba(15, 118, 110, 0.2);
		outline-offset: 2px;
	}

	.ghost-button {
		border: 0;
		font-weight: 700;
		font-size: 0.85rem;
		padding: 0.45rem 0.65rem;
		border-radius: 999px;
		background: rgba(19, 34, 31, 0.06);
		color: var(--ink);
	}

	:global([data-theme='dark']) .ghost-button {
		background: rgba(255, 255, 255, 0.08);
		color: var(--ink);
	}

	.mini-stats,
	.metric-ribbon,
	.summary-grid {
		display: grid;
		gap: 0.45rem;
	}

	.mini-stats {
		grid-template-columns: 1fr;
	}

	.mini-stats div,
	.summary-grid article,
	.metric-ribbon article {
		min-width: 0;
		padding: 0.55rem 0.9rem 0.55rem 0.65rem;
		border-radius: 0.75rem;
		background: rgba(255, 255, 255, 0.72);
		border: 1px solid rgba(19, 34, 31, 0.06);
	}

	.mini-stats strong,
	.summary-grid strong,
	.metric-ribbon strong {
		display: block;
		margin-top: 0.15rem;
		font-size: 0.92rem;
		line-height: 1.35;
		overflow-wrap: anywhere;
	}

	.error {
		margin: 0;
		font-size: 0.8rem;
		color: var(--danger);
		font-weight: 700;
	}

	.results {
		display: grid;
		gap: 0.55rem;
	}

	.summary {
		display: grid;
		grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr);
		gap: 0.55rem;
		padding: 0.7rem;
	}

	.summary-main h2 {
		font-size: clamp(1.35rem, 2vw, 1.7rem);
	}

	.summary-main p strong {
		color: var(--ink);
	}

	.summary-grid {
		grid-template-columns: repeat(2, minmax(0, 1fr));
	}

	.metric-ribbon {
		grid-template-columns: repeat(5, minmax(0, 1fr));
	}

	.card-grid {
		display: grid;
		grid-template-columns: minmax(0, 1fr);
		gap: 0.55rem;
	}

	.card {
		padding: 0.7rem;
	}

	.chart-card {
		min-height: 18rem;
	}

	.chart-footer {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 0.75rem;
		margin-top: 0.75rem;
		padding-top: 0.75rem;
		border-top: 1px solid rgba(19, 34, 31, 0.08);
	}

	:global([data-theme='dark']) .chart-footer {
		border-top-color: rgba(255, 255, 255, 0.08);
	}

	.chart-footer p {
		margin: 0;
		font-size: 0.8rem;
		color: var(--ink-soft);
	}

	.play-button {
		padding: 0.45rem 0.85rem;
		font-size: 0.8rem;
		font-weight: 700;
		border-radius: 999px;
		background: var(--accent);
		color: #fff;
		border: none;
	}

	:global([data-theme='dark']) .play-button {
		background: var(--accent);
		color: #0f1413;
	}

	.chart-hint {
		margin: 0;
		font-size: 1rem;
	}

	.policy-footer {
		margin-top: 0.75rem;
		padding-top: 0.75rem;
		border-top: 1px solid rgba(19, 34, 31, 0.08);
	}

	:global([data-theme='dark']) .policy-footer {
		border-top-color: rgba(255, 255, 255, 0.08);
	}

	.slider-field {
		display: grid;
		gap: 0.35rem;
	}

	.slider-head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.5rem;
	}

	.slider-head span {
		font-size: 0.7rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--ink-soft);
	}

	.slider-head strong {
		font-size: 0.9rem;
		font-variant-numeric: tabular-nums;
	}

	.slider-field input[type='range'] {
		-webkit-appearance: none;
		appearance: none;
		width: 100%;
		height: 0.35rem;
		border-radius: 999px;
		background: rgba(19, 34, 31, 0.12);
		cursor: pointer;
		outline: none;
	}

	:global([data-theme='dark']) .slider-field input[type='range'] {
		background: rgba(255, 255, 255, 0.15);
	}

	.slider-field input[type='range']::-webkit-slider-thumb {
		-webkit-appearance: none;
		appearance: none;
		width: 1rem;
		height: 1rem;
		border-radius: 50%;
		background: var(--accent);
		border: 2px solid rgba(255, 255, 255, 0.9);
		box-shadow: 0 2px 6px rgba(23, 36, 34, 0.25);
		transition: transform 0.1s ease;
	}

	.slider-field input[type='range']::-webkit-slider-thumb:hover {
		transform: scale(1.08);
	}

	.slider-field input[type='range']::-moz-range-thumb {
		width: 1rem;
		height: 1rem;
		border-radius: 50%;
		background: var(--accent);
		border: 2px solid rgba(255, 255, 255, 0.9);
		box-shadow: 0 2px 6px rgba(23, 36, 34, 0.25);
		transition: transform 0.1s ease;
	}

	.slider-field input[type='range']::-moz-range-thumb:hover {
		transform: scale(1.08);
	}

	.slider-hint {
		margin: 0;
		font-size: 0.78rem;
		line-height: 1.4;
		color: var(--ink-soft);
	}

	.empty {
		padding: 1rem;
	}

	@media (max-width: 1180px) {
		.layout,
		.card-grid,
		.summary,
		.masthead {
			grid-template-columns: 1fr;
		}

		.controls {
			position: static;
		}

		.mini-stats,
		.metric-ribbon {
			grid-template-columns: repeat(3, minmax(0, 1fr));
		}
	}

	@media (max-width: 760px) {
		.page {
			padding: 0.6rem;
		}

		.field-grid,
		.field-grid-wide,
		.mini-stats,
		.summary-grid,
		.metric-ribbon {
			grid-template-columns: 1fr;
		}

		.panel-head,
		.card-head {
			flex-direction: column;
		}

		.chart-footer {
			flex-direction: column;
			align-items: stretch;
		}

		h1 {
			font-size: clamp(1.1rem, 7vw, 1.5rem);
		}
	}
</style>
