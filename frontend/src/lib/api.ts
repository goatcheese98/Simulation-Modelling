import type { SimulationRequestPayload, SimulationResponse } from '$lib/types';

const API_BASE_URL = import.meta.env.PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';

export async function simulateNewsvendor(
	payload: SimulationRequestPayload
): Promise<SimulationResponse> {
	const response = await fetch(`${API_BASE_URL}/api/simulate`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(payload)
	});

	if (!response.ok) {
		const details = await readError(response);
		throw new Error(details);
	}

	return (await response.json()) as SimulationResponse;
}

async function readError(response: Response): Promise<string> {
	try {
		const body = await response.json();
		if (typeof body?.detail === 'string') {
			return body.detail;
		}
	} catch {
		// Fall back to the HTTP status when the response body is not JSON.
	}

	return `Simulation request failed with ${response.status}`;
}
