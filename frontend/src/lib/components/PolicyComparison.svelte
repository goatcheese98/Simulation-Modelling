<script lang="ts">
	import type { PolicyResult } from '$lib/types';
	import Tooltip from './Tooltip.svelte';

	interface Props {
		policies: PolicyResult[];
		title?: string;
	}

	type MetricKey = 'avg_profit' | 'fill_rate' | 'stockout_rate' | 'avg_leftover' | 'avg_lost_sales';

	const metrics: {
		key: MetricKey;
		label: string;
		suffix?: string;
		percent?: boolean;
		hint: string;
	}[] = [
		{
			key: 'avg_profit',
			label: 'Expected profit',
			suffix: '$',
			hint: 'Average profit per period for this policy across all simulated demand draws.'
		},
		{
			key: 'fill_rate',
			label: 'Fill rate',
			percent: true,
			hint: 'Percentage of total demand satisfied immediately from on-hand inventory in a given period.'
		},
		{
			key: 'stockout_rate',
			label: 'Stockout rate',
			percent: true,
			hint: 'Percentage of periods where demand exceeded the order quantity and inventory ran out.'
		},
		{
			key: 'avg_leftover',
			label: 'Expected leftover',
			hint: 'Average number of unsold units remaining after demand is realized each period.'
		},
		{
			key: 'avg_lost_sales',
			label: 'Expected lost sales',
			hint: 'Average units of unmet demand per period because stock was insufficient.'
		}
	];

	const policyHints: Record<string, string> = {
		optimal:
			'The order quantity that achieved the highest average simulated profit in the search window.',
		analytic:
			'The classical newsvendor solution derived from the critical fractile and assumed demand distribution.',
		lean:
			'A deliberately lower order quantity that reduces holding cost and leftover inventory risk. It accepts a higher chance of stockouts in exchange for lower average inventory.',
		buffered:
			'A deliberately higher order quantity that builds extra safety stock above the analytic solution. It reduces stockout risk and lost sales, but increases expected leftover inventory and holding cost.',
		'order-mean': 'Ordering exactly the average demand, ignoring demand uncertainty.'
	};

	let { policies, title = '' }: Props = $props();
	let selectedMetric = $state<MetricKey>('avg_profit');

	const sortedPolicies = $derived.by(() =>
		[...policies].sort((a, b) => b[selectedMetric] - a[selectedMetric])
	);

	function formatMetric(value: number, metric: (typeof metrics)[number]): string {
		if (metric.percent) {
			return `${(value * 100).toFixed(1)}%`;
		}
		if (metric.suffix === '$') {
			return new Intl.NumberFormat('en-US', {
				style: 'currency',
				currency: 'USD',
				maximumFractionDigits: 2
			}).format(value);
		}
		return value.toFixed(1);
	}
</script>

<div class="comparison-shell">
	<div class="toolbar">
		{#if title}
			<h3 class="toolbar-title">{title}</h3>
		{/if}
		<label class="select-wrap">
			<span>Sort by</span>
			<select bind:value={selectedMetric}>
				{#each metrics as option}
					<option value={option.key}>{option.label}</option>
				{/each}
			</select>
		</label>
	</div>

	<div class="table-wrap">
		<table class="policy-table">
			<thead>
				<tr>
					<th class="corner">Policy</th>
					{#each sortedPolicies as policy}
						<th class:highlight={policy.key === 'optimal'}>
							<div class="policy-label">
								{policy.label}
								{#if policyHints[policy.key]}
									<Tooltip hint={policyHints[policy.key]} />
								{/if}
							</div>
							<div class="policy-qty">Q = {policy.order_quantity.toFixed(1)}</div>
						</th>
					{/each}
				</tr>
			</thead>
			<tbody>
				{#each metrics as metric}
					<tr class:dim={metric.key !== selectedMetric}>
						<td class="metric-name">
							{metric.label}
							<Tooltip hint={metric.hint} />
						</td>
						{#each sortedPolicies as policy}
							<td class="metric-cell" class:best={policy.key === 'optimal'}>
								{formatMetric(policy[metric.key], metric)}
							</td>
						{/each}
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</div>

<style>
	.comparison-shell {
		display: grid;
		gap: 0.6rem;
	}

	.toolbar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 0.75rem;
	}

	.toolbar-title {
		margin: 0;
		font-size: 1.05rem;
		line-height: 1.12;
	}

	.select-wrap {
		margin-left: auto;
		display: inline-flex;
		align-items: center;
		flex-wrap: nowrap;
		gap: 0.4rem;
		font-size: 0.75rem;
		font-weight: 700;
		color: var(--ink-soft);
		text-transform: uppercase;
		letter-spacing: 0.08em;
		white-space: nowrap;
	}

	.select-wrap span {
		line-height: 1;
	}

	.select-wrap select {
		min-width: 10rem;
		padding: 0.35rem 0.6rem;
		border: 1px solid var(--line-strong);
		border-radius: 0.6rem;
		background: rgba(255, 255, 255, 0.9);
		color: var(--ink);
		font-size: 0.8rem;
		font-weight: 600;
		text-transform: none;
		letter-spacing: normal;
		line-height: 1.2;
	}

	:global([data-theme='dark']) .select-wrap select {
		background: rgba(0, 0, 0, 0.25);
		color: var(--ink);
		border-color: var(--line);
	}

	.table-wrap {
		overflow-x: auto;
	}

	.policy-table {
		width: 100%;
		border-collapse: separate;
		border-spacing: 0;
		font-size: 0.85rem;
	}

	.policy-table th,
	.policy-table td {
		padding: 0.45rem 0.6rem;
		text-align: left;
		border-bottom: 1px solid var(--line);
		white-space: nowrap;
	}

	.policy-table th {
		font-weight: 600;
		color: var(--ink-soft);
		background: rgba(255, 255, 255, 0.5);
	}

	:global([data-theme='dark']) .policy-table th {
		background: rgba(0, 0, 0, 0.2);
	}

	.policy-table thead th:first-child {
		border-top-left-radius: 0.7rem;
		border-bottom-left-radius: 0.7rem;
	}

	.policy-table thead th:last-child {
		border-top-right-radius: 0.7rem;
		border-bottom-right-radius: 0.7rem;
	}

	.policy-table tbody tr:last-child td {
		border-bottom: none;
	}

	.corner {
		width: 1%;
	}

	.policy-label {
		font-size: 0.8rem;
		color: var(--ink);
		display: inline-flex;
		align-items: center;
	}

	.policy-qty {
		font-size: 0.72rem;
		font-weight: 500;
		color: var(--ink-soft);
	}

	.metric-name {
		font-weight: 600;
		color: var(--ink);
	}

	.metric-cell {
		font-variant-numeric: tabular-nums;
		color: var(--ink-soft);
	}

	.metric-cell.best {
		color: var(--accent);
		font-weight: 700;
	}

	th.highlight {
		background: var(--accent-soft);
	}

	tr.dim td.metric-cell {
		opacity: 0.7;
	}

	tr.dim td.metric-name {
		opacity: 0.85;
	}

	@media (max-width: 720px) {
		.toolbar {
			flex-wrap: wrap;
			justify-content: stretch;
		}

		.toolbar-title,
		.select-wrap,
		.select-wrap select {
			width: 100%;
		}

		.policy-table th,
		.policy-table td {
			padding: 0.4rem 0.45rem;
			font-size: 0.8rem;
		}
	}
</style>
