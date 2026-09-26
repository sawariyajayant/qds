import type {
  AttackType,
  SimulationResponse,
  TeleportationResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function post<T>(path: string, body?: T): Promise<SimulationResponse> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as SimulationResponse;
}

export function runCleanSimulation(): Promise<SimulationResponse> {
  return post("/simulate/clean");
}

export function runAttackSimulation(attack_type: AttackType): Promise<SimulationResponse> {
  return post("/simulate/attack", { attack_type });
}
export async function runTeleportationSimulation(): Promise<TeleportationResponse> {
  const response = await fetch(
    `${API_BASE}/simulate/teleport`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    const detail = await response.text();

    throw new Error(
      detail || `Teleportation request failed with status ${response.status}`
    );
  }

  return (await response.json()) as TeleportationResponse;
}