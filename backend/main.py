import hashlib
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from attacks import (
    simulate_channel_manipulation_attack,
    simulate_forgery_attack,
    simulate_impersonation_attack,
)
from detection import DEFAULT_THRESHOLD, evaluate_signature
from signatures import sign_message
from teleportation import run_attack_teleportation, run_teleportation

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Demo constants -- fixed message/key keep the live demo simple and repeatable.
DEMO_MESSAGE = "Transfer 500 credits to Bob"
DEMO_PRIVATE_KEY = "alice-secret-key-123"
NUM_COPIES = 20

# In-memory replay tracker (demo-only, resets on server restart).
# Pre-seeded so clicking "Replay Attack" ALWAYS demonstrates detection
# immediately, simulating an attacker resending an already-used signature.
used_signature_ids = {"demo-replay-signature"}


class AttackRequest(BaseModel):
    attack_type: str  # "forgery" | "impersonation" | "replay" | "channel_manipulation"


def _finalize(result: dict, attack_type: Optional[str], start_time: float) -> dict:
    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
    timestamp = datetime.now(timezone.utc).isoformat()

    error_rate = result.get("error_rate", 0.0)
    tag = "DETECTED" if result.get("status") == "attack_detected" else "CLEAN"
    raw_str = f"{attack_type}-{error_rate}-{timestamp}".encode("utf-8")
    hash_hex = hashlib.sha3_512(raw_str).hexdigest()[:16].upper()
    session_hash = f"0x{hash_hex}-QDS-{tag}"

    result["attack_type"] = attack_type
    result["timestamp"] = timestamp
    result["latency_ms"] = latency_ms
    result["session_hash"] = session_hash
    return result


@app.post("/simulate/clean")
def simulate_clean():
    start_time = time.perf_counter()

    received_states = sign_message(
        DEMO_MESSAGE,
        DEMO_PRIVATE_KEY,
        NUM_COPIES
    )

    result = evaluate_signature(
        DEMO_MESSAGE,
        DEMO_PRIVATE_KEY,
        received_states
    )

    teleportation = run_teleportation()

    result["teleportation"] = teleportation

    return _finalize(
        result,
        None,
        start_time
    )


@app.post("/simulate/attack")
def simulate_attack(request: AttackRequest):
    start_time = time.perf_counter()
    attack_type = request.attack_type
    teleportation_data = None

    if attack_type == "forgery":
        forged_states, fake_key = simulate_forgery_attack(DEMO_MESSAGE, NUM_COPIES)
        result = evaluate_signature(DEMO_MESSAGE, DEMO_PRIVATE_KEY, forged_states)
        teleportation_data = run_attack_teleportation(
            attack_type="forgery",
            shots=NUM_COPIES,
            genuine_key=DEMO_PRIVATE_KEY,
            fake_key=fake_key,
        )

    elif attack_type == "impersonation":
        impersonated_states = simulate_impersonation_attack(
            DEMO_MESSAGE,
            DEMO_PRIVATE_KEY,
            NUM_COPIES,
        )
        result = evaluate_signature(DEMO_MESSAGE, DEMO_PRIVATE_KEY, impersonated_states)
        teleportation_data = run_attack_teleportation(
            attack_type="impersonation",
            shots=NUM_COPIES,
            genuine_key=DEMO_PRIVATE_KEY,
        )

    elif attack_type == "channel_manipulation":
        manipulated_states = simulate_channel_manipulation_attack(
            DEMO_MESSAGE,
            DEMO_PRIVATE_KEY,
            NUM_COPIES,
        )
        result = evaluate_signature(DEMO_MESSAGE, DEMO_PRIVATE_KEY, manipulated_states)
        teleportation_data = run_attack_teleportation(
            attack_type="channel_manipulation",
            shots=NUM_COPIES,
            genuine_key=DEMO_PRIVATE_KEY,
        )

    elif attack_type == "replay":
        signature_id = "demo-replay-signature"
        if signature_id in used_signature_ids:
            result = {
                "status": "attack_detected",
                "error_rate": 0.0,
                "threshold": DEFAULT_THRESHOLD,
                "verdict": "Signature Rejected — Replay Detected",
                "forgery_probability": 1.0,
                "trial_count": NUM_COPIES,
            }
        else:
            used_signature_ids.add(signature_id)
            clean_states = sign_message(DEMO_MESSAGE, DEMO_PRIVATE_KEY, NUM_COPIES)
            result = evaluate_signature(DEMO_MESSAGE, DEMO_PRIVATE_KEY, clean_states)

        teleportation_data = run_attack_teleportation(
            attack_type="replay",
            shots=NUM_COPIES,
            genuine_key=DEMO_PRIVATE_KEY,
        )

    else:
        raise HTTPException(status_code=400, detail=f"Unknown attack_type: {attack_type}")

    response = _finalize(result, attack_type, start_time)
    response["teleportation"] = teleportation_data
    return response


# ============================================================
# QUANTUM TELEPORTATION SIMULATION
# ============================================================

@app.post("/simulate/teleport")
def simulate_teleport():
    return run_teleportation(shots=20)