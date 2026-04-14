<script lang="ts">
	interface Props {
		hint: string;
	}

	let { hint }: Props = $props();

	let tooltipEl: HTMLDivElement | null = null;

	function show(e: MouseEvent | FocusEvent) {
		if (!tooltipEl) {
			tooltipEl = document.createElement('div');
			tooltipEl.className = 'global-tooltip';
			tooltipEl.textContent = hint;
			document.body.appendChild(tooltipEl);
		}
		const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
		const x = rect.left + rect.width / 2;
		const y = rect.top;
		tooltipEl.style.left = `${x}px`;
		tooltipEl.style.top = `${y}px`;
		tooltipEl.style.opacity = '1';
		tooltipEl.style.visibility = 'visible';
	}

	function hide() {
		if (tooltipEl) {
			tooltipEl.style.opacity = '0';
			tooltipEl.style.visibility = 'hidden';
		}
	}
</script>

<span
	class="tooltip-trigger"
	onmouseenter={show}
	onmouseleave={hide}
	onfocus={show}
	onblur={hide}
	tabindex="0"
	role="button"
	aria-label="Hint"
>
	<span class="icon">?</span>
</span>

<style>
	:global(.global-tooltip) {
		position: fixed;
		transform: translate(-50%, -110%);
		width: max-content;
		max-width: 18rem;
		padding: 0.5rem 0.7rem;
		font-size: 0.8rem;
		font-weight: 500;
		line-height: 1.35;
		color: var(--ink);
		background: #fff;
		border: 1px solid rgba(19, 34, 31, 0.08);
		border-radius: 0.5rem;
		box-shadow: 0 8px 24px rgba(23, 36, 34, 0.12);
		opacity: 0;
		visibility: hidden;
		transition: opacity 150ms ease, visibility 150ms ease;
		pointer-events: none;
		z-index: 9999;
		text-transform: none;
		letter-spacing: normal;
	}

	:global([data-theme='dark'] .global-tooltip) {
		color: #f2f2f2;
		background: #1f2e2b;
		border-color: rgba(255, 255, 255, 0.08);
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
	}

	.tooltip-trigger {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		margin-left: 0.2rem;
		width: 0.85rem;
		height: 0.85rem;
		font-size: 0.6rem;
		font-weight: 700;
		color: #fff;
		background: rgba(15, 118, 110, 0.75);
		border-radius: 999px;
		cursor: help;
		vertical-align: middle;
	}
</style>
