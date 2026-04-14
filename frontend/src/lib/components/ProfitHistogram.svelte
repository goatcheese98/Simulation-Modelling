<script lang="ts">
	import { onMount } from 'svelte';

	import type { ECharts, EChartsOption } from 'echarts';

	import type { ProfitHistogramBin } from '$lib/types';

	interface Props {
		bins: ProfitHistogramBin[];
		darkMode?: boolean;
	}

	let { bins, darkMode = false }: Props = $props();

	let chartHost = $state<HTMLDivElement | null>(null);
	let chart = $state<ECharts | null>(null);

	function currency(value: number): string {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			maximumFractionDigits: 2
		}).format(value);
	}

	function buildOption(): EChartsOption {
		const axisColor = darkMode ? 'rgba(255,255,255,0.25)' : 'rgba(21, 37, 35, 0.22)';
		const gridColor = darkMode ? 'rgba(255,255,255,0.10)' : 'rgba(21, 37, 35, 0.08)';
		const labelColor = darkMode ? '#bfc9c6' : '#546863';
		const tooltipBg = darkMode ? '#1f2e2b' : '#13221f';
		const tooltipText = darkMode ? '#f2f2f2' : '#f7f1e8';
		const barColor = darkMode ? '#2dd4bf' : '#0f766e';
		const barShadow = darkMode ? 'rgba(45, 212, 191, 0.22)' : 'rgba(15, 118, 110, 0.16)';

		return {
			animationDuration: 700,
			animationEasing: 'cubicOut',
			grid: {
				top: 16,
				right: 18,
				bottom: 42,
				left: 56,
				containLabel: true
			},
			tooltip: {
				trigger: 'item',
				backgroundColor: tooltipBg,
				borderWidth: 0,
				padding: 14,
				textStyle: {
					color: tooltipText,
					fontFamily: 'Space Grotesk Variable, sans-serif',
					fontSize: 13
				},
				formatter: (params) => {
					const point = Array.isArray(params) ? params[0] : params;
					const bucket = bins[Number(point?.dataIndex)] ?? null;
					if (!bucket) {
						return '';
					}

					return `<div style="display:grid;gap:6px;min-width:210px;">
						<div style="font-size:13px;letter-spacing:0.08em;text-transform:uppercase;color:rgba(247,241,232,0.68);">Profit range</div>
						<div style="font-size:17px;font-weight:700;line-height:1.35;">${currency(bucket.bin_start)} to ${currency(bucket.bin_end)}</div>
						<div style="display:flex;justify-content:space-between;gap:16px;"><span>Replications</span><strong>${bucket.count.toLocaleString()}</strong></div>
						<div style="display:flex;justify-content:space-between;gap:16px;"><span>Share</span><strong>${(bucket.share * 100).toFixed(1)}%</strong></div>
					</div>`;
				}
			},
			xAxis: {
				type: 'category',
				data: bins.map((bucket) => `${bucket.bin_start}-${bucket.bin_end}`),
				name: 'Profit range',
				nameLocation: 'middle',
				nameGap: 30,
				nameTextStyle: {
					color: labelColor,
					fontSize: 12
				},
				axisLine: { lineStyle: { color: axisColor } },
				axisTick: { show: false },
				axisLabel: {
					color: labelColor,
					hideOverlap: true,
					formatter: (_value: string, index: number) => {
						const bucket = bins[index];
						if (!bucket) {
							return '';
						}
						const midpoint = (bucket.bin_start + bucket.bin_end) / 2;
						return currency(midpoint);
					}
				}
			},
			yAxis: {
				type: 'value',
				name: 'Replications',
				nameTextStyle: {
					color: labelColor,
					fontSize: 12
				},
				axisLine: { show: false },
				splitLine: { lineStyle: { color: gridColor } },
				axisLabel: {
					color: labelColor
				}
			},
			series: [
				{
					name: 'Replications',
					type: 'bar',
					barMaxWidth: 28,
					data: bins.map((bucket) => bucket.count),
					itemStyle: {
						color: barColor,
						borderRadius: [8, 8, 0, 0],
						shadowBlur: 10,
						shadowColor: barShadow
					}
				}
			]
		};
	}

	$effect(() => {
		if (!chart || bins.length === 0) {
			return;
		}

		chart.setOption(buildOption(), {
			notMerge: false,
			lazyUpdate: true,
			replaceMerge: ['series']
		});
	});

	onMount(() => {
		let resizeObserver: ResizeObserver | null = null;

		async function setup() {
			if (!chartHost) {
				return;
			}

			const echarts = await import('echarts');
			chart = echarts.init(chartHost, undefined, { renderer: 'canvas' });
			chart.setOption(buildOption(), {
				notMerge: false,
				lazyUpdate: true,
				replaceMerge: ['series']
			});

			resizeObserver = new ResizeObserver(() => chart?.resize());
			resizeObserver.observe(chartHost);
		}

		void setup();

		return () => {
			resizeObserver?.disconnect();
			chart?.dispose();
			chart = null;
		};
	});
</script>

<div class="chart-shell">
	<div bind:this={chartHost} class="chart-host" aria-label="Histogram of profit outcomes"></div>
</div>

<style>
	.chart-shell {
		min-height: 16rem;
	}

	.chart-host {
		width: 100%;
		min-height: 16rem;
	}

	@media (max-width: 760px) {
		.chart-host {
			min-height: 18rem;
		}
	}
</style>
