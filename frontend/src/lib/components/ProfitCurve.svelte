<script lang="ts">
	import { onMount } from 'svelte';

	import type { ECharts, EChartsOption } from 'echarts';

	import type { ProfitCurvePoint } from '$lib/types';

	interface Props {
		points: ProfitCurvePoint[];
		recommendedQuantity: number;
		analyticQuantity: number;
		meanDemand: number;
		yAxisScale?: 'focused' | 'full';
		darkMode?: boolean;
		replayKey?: number;
	}

	let {
		points,
		recommendedQuantity,
		analyticQuantity,
		meanDemand,
		yAxisScale = 'focused',
		darkMode = false,
		replayKey = 0
	}: Props = $props();

	let chartHost = $state<HTMLDivElement | null>(null);
	let chart = $state<ECharts | null>(null);
	let chartWidth = $state(0);
	let animationStep = $state(5);
	let isReplaying = $state(false);

	function findClosestPoint(quantity: number): ProfitCurvePoint | null {
		if (points.length === 0) {
			return null;
		}

		return (
			points.reduce((closest, point) => {
				if (!closest) {
					return point;
				}

				return Math.abs(point.order_quantity - quantity) < Math.abs(closest.order_quantity - quantity)
					? point
					: closest;
			}, null as ProfitCurvePoint | null) ?? null
		);
	}

	function currency(value: number): string {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			maximumFractionDigits: 2
		}).format(value);
	}

	function units(value: number): string {
		return `${value.toFixed(1)} units`;
	}

	$effect(() => {
		void points.length;
		isReplaying = false;
		animationStep = points.length > 0 ? 5 : 0;
	});

	$effect(() => {
		void replayKey;
		if (replayKey === 0 || points.length === 0) {
			return;
		}
		isReplaying = true;
		animationStep = 0;
		const t1 = setTimeout(() => (animationStep = 1), 100);
		const t2 = setTimeout(() => (animationStep = 2), 1060);
		const t3 = setTimeout(() => (animationStep = 3), 2020);
		const t4 = setTimeout(() => (animationStep = 4), 2780);
		const t5 = setTimeout(() => {
			animationStep = 5;
			isReplaying = false;
		}, 3540);
		return () => {
			isReplaying = false;
			clearTimeout(t1);
			clearTimeout(t2);
			clearTimeout(t3);
			clearTimeout(t4);
			clearTimeout(t5);
		};
	});

	function buildOption(): EChartsOption {
		const recommendedPoint = findClosestPoint(recommendedQuantity) ?? points[0] ?? null;
		const analyticPoint = findClosestPoint(analyticQuantity) ?? recommendedPoint;
		const minQuantity = points.length > 0 ? Math.min(...points.map((point) => point.order_quantity)) : 0;
		const maxQuantity = points.length > 0 ? Math.max(...points.map((point) => point.order_quantity)) : 0;
		const quantitiesMerged = Math.abs(recommendedQuantity - analyticQuantity) < 0.15;
		const isCompact = chartWidth > 0 && chartWidth < 680;

		const axisColor = darkMode ? 'rgba(255,255,255,0.25)' : 'rgba(21, 37, 35, 0.22)';
		const gridColor = darkMode ? 'rgba(255,255,255,0.10)' : 'rgba(21, 37, 35, 0.08)';
		const labelColor = darkMode ? '#bfc9c6' : '#546863';
		const tooltipBg = darkMode ? '#1f2e2b' : '#13221f';
		const tooltipText = darkMode ? '#f2f2f2' : '#f7f1e8';
		const simColor = darkMode ? '#2dd4bf' : '#0f766e';
		const simArea = darkMode ? 'rgba(45, 212, 191, 0.15)' : 'rgba(15, 118, 110, 0.12)';
		const ciColor = darkMode ? 'rgba(156, 204, 101, 0.9)' : 'rgba(96, 138, 48, 0.85)';
		const anaColor = darkMode ? '#fbbf24' : '#c08a15';
		const analyticQtyColor = anaColor;
		const bestColor = simColor;

		const meanProfit =
			points.find((p) => p.order_quantity === meanDemand)?.avg_profit ??
			points[Math.floor(points.length / 2)]?.avg_profit ??
			0;
		const plottedProfitValues = points.flatMap((point) => [
			point.avg_profit,
			point.analytic_profit,
			point.avg_profit_ci_lower,
			point.avg_profit_ci_upper
		]);
		const minProfit = plottedProfitValues.length > 0 ? Math.min(...plottedProfitValues) : 0;
		const maxProfit = plottedProfitValues.length > 0 ? Math.max(...plottedProfitValues) : 0;
		const profitSpan = Math.max(maxProfit - minProfit, 1);
		const focusedPadding = Math.max(profitSpan * 0.18, 1.5);
		const fullPadding = Math.max(profitSpan * 0.12, 4);
		const axisFloor =
			yAxisScale === 'focused'
				? Math.max(0, minProfit - focusedPadding)
				: Math.min(0, minProfit - fullPadding);
		const axisCeiling =
			yAxisScale === 'focused' ? maxProfit + focusedPadding : maxProfit + fullPadding;
		const stepAnimation = (step: number, duration: number) =>
			isReplaying && animationStep === step ? duration : 0;

		const analyticTooltip = () =>
			quantitiesMerged
				? `<div style="display:grid;gap:12px;min-width:290px;">
						<div style="display:grid;gap:4px;">
							<div style="font-size:13px;letter-spacing:0.08em;text-transform:uppercase;color:${analyticQtyColor};">Analytic quantity</div>
							<div style="font-size:18px;font-weight:700;line-height:1.35;">${analyticQuantity.toFixed(1)} units</div>
							<div style="font-size:16px;font-weight:600;line-height:1.35;">Analytic profit: ${currency(analyticPoint?.analytic_profit ?? 0)}</div>
						</div>
						<div style="height:1px;background:rgba(247,241,232,0.16);"></div>
						<div style="display:grid;gap:4px;">
							<div style="font-size:13px;letter-spacing:0.08em;text-transform:uppercase;color:${bestColor};">Simulation-optimal quantity</div>
							<div style="font-size:18px;font-weight:700;line-height:1.35;">${recommendedQuantity.toFixed(1)} units</div>
							<div style="font-size:16px;font-weight:600;line-height:1.35;">Simulation-optimal profit: ${currency(recommendedPoint?.avg_profit ?? 0)}</div>
						</div>
					</div>`
				: `<div style="display:grid;gap:8px;min-width:290px;"><div style="font-size:13px;letter-spacing:0.08em;text-transform:uppercase;color:${analyticQtyColor};">Analytic quantity</div><div style="font-size:18px;font-weight:700;line-height:1.35;white-space:pre-line;">Analytic quantity: ${analyticQuantity.toFixed(1)} units\nAnalytic profit: ${currency(analyticPoint?.analytic_profit ?? 0)}\nSimulation-optimal quantity: ${recommendedQuantity.toFixed(1)} units\nSimulation-optimal profit: ${currency(recommendedPoint?.avg_profit ?? 0)}</div></div>`;

		const simulationTooltip = () =>
			quantitiesMerged
				? `<div style="display:grid;gap:12px;min-width:290px;">
						<div style="display:grid;gap:4px;">
							<div style="font-size:13px;letter-spacing:0.08em;text-transform:uppercase;color:${bestColor};">Simulation-optimal quantity</div>
							<div style="font-size:18px;font-weight:700;line-height:1.35;">${recommendedQuantity.toFixed(1)} units</div>
							<div style="font-size:16px;font-weight:600;line-height:1.35;">Simulation-optimal profit: ${currency(recommendedPoint?.avg_profit ?? 0)}</div>
						</div>
						<div style="height:1px;background:rgba(247,241,232,0.16);"></div>
						<div style="display:grid;gap:4px;">
							<div style="font-size:13px;letter-spacing:0.08em;text-transform:uppercase;color:${analyticQtyColor};">Analytic quantity</div>
							<div style="font-size:18px;font-weight:700;line-height:1.35;">${analyticQuantity.toFixed(1)} units</div>
							<div style="font-size:16px;font-weight:600;line-height:1.35;">Analytic profit: ${currency(analyticPoint?.analytic_profit ?? 0)}</div>
						</div>
					</div>`
				: `<div style="display:grid;gap:8px;min-width:290px;"><div style="font-size:13px;letter-spacing:0.08em;text-transform:uppercase;color:${bestColor};">Simulation-optimal quantity</div><div style="font-size:18px;font-weight:700;line-height:1.35;white-space:pre-line;">Simulation-optimal quantity: ${recommendedQuantity.toFixed(1)} units\nSimulation-optimal profit: ${currency(recommendedPoint?.avg_profit ?? 0)}\nAnalytic quantity: ${analyticQuantity.toFixed(1)} units\nAnalytic profit: ${currency(analyticPoint?.analytic_profit ?? 0)}</div></div>`;

		const series: any[] = [];

		if (animationStep >= 1) {
			series.push({
				name: 'Analytic profit',
				type: 'line',
				smooth: true,
				symbol: 'none',
				lineStyle: { width: 2, type: 'dashed', color: anaColor },
				data: points.map((point) => [point.order_quantity, point.analytic_profit]),
				animationDuration: stepAnimation(1, 900),
				animationDurationUpdate: stepAnimation(1, 900),
				endLabel: {
					show: !isCompact,
					formatter: 'Analytic profit',
					color: anaColor,
					fontSize: 13,
					fontWeight: 700,
					offset: [22, -18]
				}
			});
		}

		if (animationStep >= 2) {
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
				animationDuration: stepAnimation(2, 900),
				animationDurationUpdate: stepAnimation(2, 900),
				endLabel: {
					show: !isCompact,
					formatter: 'Simulated profit',
					color: simColor,
					fontSize: 13,
					fontWeight: 700,
					offset: [22, 18]
				}
			});

			series.push({
				name: '95% CI band',
				type: 'line',
				smooth: true,
				symbol: 'none',
				silent: true,
				lineStyle: {
					width: isCompact ? 1.2 : 1.4,
					type: 'dashed',
					color: ciColor,
					opacity: 0.72
				},
				data: points.map((point) => [point.order_quantity, point.avg_profit_ci_upper]),
				animationDuration: stepAnimation(2, 900),
				animationDurationUpdate: stepAnimation(2, 900)
			});

			series.push({
				name: '95% CI band',
				type: 'line',
				smooth: true,
				symbol: 'none',
				silent: true,
				lineStyle: {
					width: isCompact ? 1.2 : 1.4,
					type: 'dashed',
					color: ciColor,
					opacity: 0.72
				},
				data: points.map((point) => [point.order_quantity, point.avg_profit_ci_lower]),
				animationDuration: stepAnimation(2, 900),
				animationDurationUpdate: stepAnimation(2, 900)
			});
		}

		if (animationStep >= 3) {
			series.push({
				name: 'Mean demand',
				type: 'line',
				data: [
					[meanDemand, axisFloor],
					[meanDemand, meanProfit]
				],
				symbol: 'none',
				smooth: false,
				silent: false,
				lineStyle: {
					type: 'dashed',
					color: darkMode ? 'rgba(255,255,255,0.28)' : 'rgba(21, 37, 35, 0.34)',
					width: 2
				},
				tooltip: { show: false },
				animationDuration: stepAnimation(3, 440),
				animationDurationUpdate: stepAnimation(3, 440)
			});

			series.push({
				name: '',
				type: 'scatter',
				symbol: 'circle',
				symbolSize: 34,
				data: [[meanDemand, meanProfit]],
				itemStyle: { color: 'transparent' },
				emphasis: { scale: false },
				z: 29,
				animationDuration: stepAnimation(3, 440),
				animationDurationUpdate: stepAnimation(3, 440),
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
					formatter: () =>
						`<div style="display:grid;gap:8px;min-width:220px;"><div style="font-size:13px;letter-spacing:0.08em;text-transform:uppercase;color:${darkMode ? '#bfc9c6' : '#6f817b'};">Mean demand</div><div style="font-size:18px;font-weight:700;line-height:1.35;">${meanDemand.toFixed(1)} units</div></div>`
				}
			});
		}

		if (animationStep >= 4 && analyticPoint) {
			series.push({
				name: 'Analytic quantity',
				type: 'line',
				data: [
					[analyticQuantity, axisFloor],
					[analyticQuantity, analyticPoint.analytic_profit]
				],
				symbol: 'none',
				smooth: false,
				silent: false,
				lineStyle: { type: 'dotted', color: analyticQtyColor, width: 2 },
				animationDuration: stepAnimation(4, 440),
				animationDurationUpdate: stepAnimation(4, 440)
			});

			series.push({
				name: '',
				type: 'scatter',
				symbol: 'circle',
				symbolSize: quantitiesMerged ? 50 : 38,
				data: [[analyticQuantity, analyticPoint.analytic_profit]],
				itemStyle: { color: 'transparent' },
				emphasis: { scale: false },
				z: 30,
				animationDuration: stepAnimation(4, 440),
				animationDurationUpdate: stepAnimation(4, 440),
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
					formatter: analyticTooltip
				}
			});
		}

		if (animationStep >= 5 && recommendedPoint) {
			series.push({
				name: 'Simulation-optimal quantity',
				type: 'line',
				data: [
					[recommendedQuantity, axisFloor],
					[recommendedQuantity, recommendedPoint.avg_profit]
				],
				symbol: 'none',
				smooth: false,
				silent: false,
				lineStyle: { type: 'dashed', color: bestColor, width: 2 },
				animationDuration: stepAnimation(5, 440),
				animationDurationUpdate: stepAnimation(5, 440)
			});

			series.push({
				name: '',
				type: 'scatter',
				symbol: 'circle',
				symbolSize: quantitiesMerged ? 50 : 38,
				data: [[recommendedQuantity, recommendedPoint.avg_profit]],
				itemStyle: { color: 'transparent' },
				emphasis: { scale: false },
				z: 31,
				animationDuration: stepAnimation(5, 440),
				animationDurationUpdate: stepAnimation(5, 440),
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
					formatter: simulationTooltip
				}
			});
		}

		return {
			animationDuration: 900,
			animationEasing: 'cubicOut',
			animationDurationUpdate: 0,
			animationEasingUpdate: isReplaying ? 'cubicOut' : undefined,
			grid: {
				top: isCompact ? 16 : 24,
				right: isCompact ? 16 : 210,
				bottom: isCompact ? 108 : 52,
				left: isCompact ? 52 : 72,
				containLabel: true
			},
			tooltip: {
				trigger: 'axis',
				triggerOn: 'mousemove|click',
				backgroundColor: tooltipBg,
				borderWidth: 0,
				padding: isCompact ? 12 : 16,
				textStyle: {
					color: tooltipText,
					fontFamily: 'Space Grotesk Variable, sans-serif',
					fontSize: isCompact ? 12 : 14
				},
				valueFormatter: (value) =>
					typeof value === 'number' ? currency(value) : String(value ?? ''),
				formatter: (params) => {
					const rows = Array.isArray(params) ? params : [params];
					const quantityValue = Number(
						(rows[0] as { axisValue?: string | number } | undefined)?.axisValue ?? 0
					);
					const quantity = String(quantityValue);
					const selectedPoint = findClosestPoint(quantityValue);
					const dedupedRows = Array.from(
						rows.reduce((bySeries, row) => {
							const seriesName = row.seriesName ?? '';
							if (!seriesName) {
								return bySeries;
							}

							const pointValue = Number(Array.isArray(row.value) ? row.value[1] : row.value);
							const existing = bySeries.get(seriesName);
							if (!existing || pointValue > existing.pointValue) {
								bySeries.set(seriesName, { row, pointValue });
							}
							return bySeries;
						}, new Map<string, { row: (typeof rows)[number]; pointValue: number }>())
					).map(([, entry]) => entry);
					const lines = dedupedRows
						.map((row) => {
							const valueLabel =
								row.row.seriesName === 'Analytic quantity' ||
								row.row.seriesName === 'Simulation-optimal quantity' ||
								row.row.seriesName === 'Mean demand'
									? units(quantityValue)
									: row.row.seriesName === '95% CI band' && selectedPoint
										? `${currency(selectedPoint.avg_profit_ci_lower)} to ${currency(selectedPoint.avg_profit_ci_upper)}`
									: currency(row.pointValue);
							return `<div style="display:flex;justify-content:space-between;gap:16px;"><span>${row.row.marker}${row.row.seriesName}</span><strong>${valueLabel}</strong></div>`;
						})
						.join('');

					return `<div style="display:grid;gap:8px;"><div style="font-size:13px;letter-spacing:0.08em;text-transform:uppercase;color:rgba(247,241,232,0.68);">Order quantity</div><div style="font-size:20px;font-weight:700;">${quantity} units</div>${lines}</div>`;
				}
			},
			legend: {
				type: isCompact ? 'scroll' : 'plain',
				left: 0,
				right: 0,
				bottom: 0,
				itemWidth: isCompact ? 10 : 12,
				itemHeight: isCompact ? 10 : 12,
				itemGap: isCompact ? 12 : 18,
				pageIconColor: labelColor,
				pageIconInactiveColor: axisColor,
				pageIconSize: isCompact ? 10 : 12,
				pageTextStyle: {
					color: labelColor,
					fontFamily: 'Space Grotesk Variable, sans-serif',
					fontSize: isCompact ? 11 : 12
				},
				selectedMode: true,
				textStyle: {
					color: labelColor,
					fontFamily: 'Space Grotesk Variable, sans-serif',
					fontSize: isCompact ? 11 : 13
				}
			},
			xAxis: {
				type: 'value',
				min: minQuantity,
				max: maxQuantity,
				name: 'Order quantity',
				nameLocation: 'middle',
				nameGap: isCompact ? 24 : 34,
				nameTextStyle: {
					color: labelColor,
					fontSize: isCompact ? 11 : 13
				},
				axisLine: { lineStyle: { color: axisColor } },
				splitLine: { lineStyle: { color: gridColor } },
				splitNumber: isCompact ? 4 : 6,
				axisLabel: {
					color: labelColor,
					fontSize: isCompact ? 11 : 13,
					hideOverlap: true,
					formatter: (value: number) => value.toFixed(0)
				}
			},
			yAxis: {
				type: 'value',
				min: axisFloor,
				max: axisCeiling,
				axisLabel: {
					color: labelColor,
					fontSize: isCompact ? 11 : 13,
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

		void chartWidth;
		void yAxisScale;

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

			chartWidth = chartHost.clientWidth;
			const echarts = await import('echarts');
			chart = echarts.init(chartHost, undefined, { renderer: 'canvas' });
			chart.setOption(buildOption(), {
				notMerge: false,
				lazyUpdate: true,
				replaceMerge: ['series']
			});

			resizeObserver = new ResizeObserver((entries) => {
				const width = entries[0]?.contentRect.width ?? chartHost?.clientWidth ?? 0;
				chartWidth = width;
				chart?.resize();
			});
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

	@media (max-width: 760px) {
		.chart-host {
			min-height: 24rem;
		}
	}
</style>
