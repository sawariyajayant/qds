export type AttackType = "forgery" | "impersonation" | "replay" | "channel_manipulation";
export type RunStatus = "clean" | "attack_detected" | "attack_undetected";

export interface SimulationResponse {
  status: RunStatus;
  attack_type: AttackType | null;
  error_rate: number;
  threshold: number;
  verdict: string;
  forgery_probability: number;
  trial_count: number;
  timestamp: string;
  latency_ms?: number;
  session_hash?: string;

  teleportation?: TeleportationResponse | null;
}
export interface RunRecord extends SimulationResponse {
  id: number;
}

export const attackLabels: Record<AttackType, string> = {
  forgery: "Forgery",
  impersonation: "Impersonation",
  replay: "Replay",
  channel_manipulation: "Channel manipulation"
};
export interface TeleportationTrial {
  trial: number;

  bell_measurement: {
    m1: number;
    m2: number;
    bits: string;
  };

  pauli_correction: {
    gate: string;
    label: string;
    operations: string[];
  };

  verification: {
    bit: number;
    passed: boolean;
  };
}


export interface TeleportationResponse {
  protocol: string;

  shots: number;

  teleportation_success_rate: number;

  bell_measurement: {
    m1: number;
    m2: number;
    bits: string;
  };

  pauli_correction: {
    gate: string;
    label: string;
    operations: string[];
  };

  verification: {
    bit: number;
    passed: boolean;
  };

  trials: TeleportationTrial[];

  latency_ms: number;
}