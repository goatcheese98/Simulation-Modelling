import { dev } from '$app/environment';

import type { SimulationRequestPayload, SimulationResponse } from '$lib/types';

const configuredApiBaseUrl = (import.meta.env.PUBLIC_API_BASE_URL ?? '').trim().replace(/\/+$/, '');
const API_BASE_URL = configuredApiBaseUrl || (dev ? 'http://127.0.0.1:8000' : '');

export async function simulateNewsvendor(
	payload: SimulationRequestPayload
): Promise<SimulationResponse> {
	if (!API_BASE_URL) {
		throw new Error(
			'Frontend is missing PUBLIC_API_BASE_URL. Configure the production build to point at the Railway backend.'
		);
	}

	let response: Response;
	try {
		response = await fetch(`${API_BASE_URL}/api/simulate`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(payload)
		});
	} catch {
		throw new Error(`Unable to reach the simulation API at ${API_BASE_URL}.`);
	}

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
