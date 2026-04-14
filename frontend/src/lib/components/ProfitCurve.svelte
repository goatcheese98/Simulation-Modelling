<script lang="ts">
	import { onMount } from 'svelte';

	import type { ECharts, EChartsOption } from 'echarts';

	import type { ProfitCurvePoint } from '$lib/types';

	interface Props {
		points: ProfitCurvePoint[];
		recommendedQuantity: number;
		analyticQuantity: number;
		meanDemand: number;
		darkMode?: boolean;
		replayKey?: number;
	}

	let { points, recommendedQuantity, analyticQuantity, meanDemand, darkMode = false, replayKey = 0 }: Props = $props();

	let chartHost = $state<HTMLDivElement | null>(null);
	let chart = $state<ECharts | null>(null);
	let animationStep = $state(2);

	function currency(value: number): string {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			maximumFractionDigits: 2
		}).format(value);
	}

	$effect(() => {
		// Whenever data updates, show everything immediately
		void points.length;
		animationStep = 2;
	});

	$effect(() => {
		// Play animation when replay button is clicked
		void replayKey;
		if (replayKey === 0 || points.length === 0) {
			return;
		}
		animationStep = 0;
		const t1 = setTimeout(() => (animationStep = 1), 700);
		const t2 = setTimeout(() => (animationStep = 2), 1400);
		return () => {
			clearTimeout(t1);
			clearTimeout(t2);
		};
	});

	function buildOption(): EChartsOption {
		const recommendedPoint =
			points.find((point) => point.order_quantity === recommendedQuantity) ?? points[0] ?? null;
		const analyticPoint =
			points.find((point) => point.order_quantity === analyticQuantity) ?? recommendedPoint;
		const minQuantity = points.length > 0 ? Math.min(...points.map((point) => point.order_quantity)) : 0;
		const maxQuantity = points.length > 0 ? Math.max(...points.map((point) => point.order_quantity)) : 0;

		const axisColor = darkMode ? 'rgba(255,255,255,0.25)' : 'rgba(21, 37, 35, 0.22)';
		const gridColor = darkMode ? 'rgba(255,255,255,0.10)' : 'rgba(21, 37, 35, 0.08)';
		const labelColor = darkMode ? '#bfc9c6' : '#546863';
		const tooltipBg = darkMode ? '#1f2e2b' : '#13221f';
		const tooltipText = darkMode ? '#f2f2f2' : '#f7f1e8';
		const simColor = darkMode ? '#2dd4bf' : '#0f766e';
		const simArea = darkMode ? 'rgba(45, 212, 191, 0.15)' : 'rgba(15, 118, 110, 0.12)';
		const anaColor = darkMode ? '#fbbf24' : '#c08a15';
		const bestColor = darkMode ? '#e88b52' : '#d76b30';

		const meanProfit =
			points.find((p) => p.order_quantity === meanDemand)?.avg_profit ??
			points[Math.floor(points.length / 2)]?.avg_profit ??
			0;

		const referencePoints = [
			{
				name: 'Mean demand',
				x: meanDemand,
				y: meanProfit,
				desc: `Mean demand: ${meanDemand.toFixed(1)} units`
			},
			{
				name: 'Analytic quantity',
				x: analyticQuantity,
				y: analyticPoint?.analytic_profit ?? 0,
				desc: `Analytic quantity: ${analyticQuantity.toFixed(1)} units\nAnalytic profit: ${currency(analyticPoint?.analytic_profit ?? 0)}`
			},
			{
				name: 'Best quantity',
				x: recommendedQuantity,
				y: recommendedPoint?.avg_profit ?? 0,
				desc: `Best quantity: ${recommendedQuantity.toFixed(1)} units\nSimulated profit: ${currency(recommendedPoint?.avg_profit ?? 0)}`
			}
		];

		const series: any[] = [];

		// Step 1: Analytic profit
		series.push({
			name: 'Analytic profit',
			type: 'line',
			smooth: true,
			symbol: 'none',
			lineStyle: { width: 2, type: 'dashed', color: anaColor },
			data: points.map((point) => [point.order_quantity, point.analytic_profit]),
			endLabel: {
				show: true,
				formatter: 'Analytic profit',
				color: anaColor,
				fontSize: 12,
				fontWeight: 600,
				offset: [8, -18]
			},
			markLine: analyticPoint
				? {
						symbol: 'none',
						label: { show: false },
						lineStyle: { type: 'dotted', color: anaColor },
						data: [{ xAxis: analyticQuantity }]
					}
				: undefined
		});

		if (animationStep >= 1) {
			series.push({
				name: 'Simulated profit',
				type: 'line',
				smooth: true,
				symbol: 'none',
				lineStyle: { width: 3, color: simColor },
				areaStyle: {
					color: simArea
				},
				data: points.map((point) => [point.order_quantity, point.avg_profit]),
				endLabel: {
					show: true,
					formatter: 'Simulated profit',
					color: simColor,
					fontSize: 12,
					fontWeight: 600,
					offset: [8, 18]
				},
				markLine: {
					symbol: 'none',
					label: { show: false },
					lineStyle: { type: 'dashed', color: darkMode ? 'rgba(255,255,255,0.25)' : 'rgba(21, 37, 35, 0.3)' },
					data: [{ xAxis: meanDemand, name: 'Mean demand' }]
				}
			});
		}

		if (animationStep >= 2 && recommendedPoint) {
			series.push(
				{
					name: 'Best quantity',
					type: 'line' as const,
					data: [],
					markLine: {
						symbol: 'none',
						label: { show: false },
						lineStyle: { type: 'dashed' as const, color: bestColor },
						data: [{ xAxis: recommendedQuantity }]
					}
				},
				{
					name: 'References',
					type: 'scatter',
					symbolSize: 28,
					itemStyle: { color: 'transparent', borderWidth: 0 },
					emphasis: { scale: false },
					data: referencePoints.map((r) => [r.x, r.y]),
					tooltip: {
						trigger: 'item',
						backgroundColor: tooltipBg,
						borderWidth: 0,
						padding: 16,
						textStyle: {
							color: tooltipText,
							fontFamily: 'Space Grotesk Variable, sans-serif',
							fontSize: 14
						},
						formatter: (params: any) => {
							const idx = typeof params.dataIndex === 'number' ? params.dataIndex : 0;
							const r = referencePoints[idx];
							return `<div style="display:grid;gap:8px;"><div style="font-size:13px;letter-spacing:0.08em;text-transform:uppercase;color:rgba(247,241,232,0.68);">${r.name}</div><div style="font-size:18px;font-weight:700;line-height:1.35;white-space:pre-line;">${r.desc}</div></div>`;
						}
					},
					z: 10
				}
			);
		}

		return {
			animationDuration: 500,
			grid: { top: 24, right: 100, bottom: 52, left: 72, containLabel: true },
			tooltip: {
				trigger: 'axis',
				backgroundColor: tooltipBg,
				borderWidth: 0,
				padding: 16,
				textStyle: {
					color: tooltipText,
					fontFamily: 'Space Grotesk Variable, sans-serif',
					fontSize: 14
				},
				valueFormatter: (value) =>
					typeof value === 'number' ? currency(value) : String(value ?? ''),
				formatter: (params) => {
					const rows = Array.isArray(params) ? params : [params];
					const quantity = String(
						(rows[0] as { axisValue?: string | number } | undefined)?.axisValue ?? ''
					);
					const lines = rows
						.map((row) => {
							const pointValue = Array.isArray(row.value) ? row.value[1] : row.value;
							return `<div style="display:flex;justify-content:space-between;gap:16px;"><span>${row.marker}${row.seriesName}</span><strong>${currency(Number(pointValue))}</strong></div>`;
						})
						.join('');

					return `<div style="display:grid;gap:8px;"><div style="font-size:13px;letter-spacing:0.08em;text-transform:uppercase;color:rgba(247,241,232,0.68);">Order quantity</div><div style="font-size:20px;font-weight:700;">${quantity} units</div>${lines}</div>`;
				}
			},
			legend: {
				bottom: 0,
				itemWidth: 12,
				itemHeight: 12,
				textStyle: {
					color: labelColor,
					fontFamily: 'Space Grotesk Variable, sans-serif'
				}
			},
			xAxis: {
				type: 'value',
				min: minQuantity,
				max: maxQuantity,
				name: 'Order quantity',
				nameLocation: 'middle',
				nameGap: 34,
				nameTextStyle: { color: labelColor },
				axisLine: { lineStyle: { color: axisColor } },
				splitLine: { lineStyle: { color: gridColor } },
				axisLabel: {
					color: labelColor,
					formatter: (value: number) => value.toFixed(0)
				}
			},
			yAxis: {
				type: 'value',
				axisLabel: {
					color: labelColor,
					formatter: (value: number) => `$${value.toFixed(0)}`
				},
				axisLine: { show: false },
				splitLine: { lineStyle: { color: gridColor } },
				nameTextStyle: { color: labelColor }
			},
			series
		};
	}

	$effect(() => {
		if (!chart || points.length === 0) {
			return;
		}

		chart.setOption(buildOption(), true);
	});

	onMount(() => {
		let resizeObserver: ResizeObserver | null = null;

		async function setup() {
			if (!chartHost) {
				return;
			}

			const echarts = await import('echarts');
			chart = echarts.init(chartHost, undefined, { renderer: 'canvas' });
			chart.setOption(buildOption(), true);

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
	<div bind:this={chartHost} class="chart-host" aria-label="Expected profit by order quantity"></div>
</div>

<style>
	.chart-shell {
		min-height: 20rem;
	}

	.chart-host {
		width: 100%;
		min-height: 20rem;
	}
</style>
