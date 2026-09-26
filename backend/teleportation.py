import math
import time

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator


def get_correction(m1: int, m2: int):
    """
    Standard quantum teleportation correction.

    Bell measurement:
        00 -> I
        01 -> X
        10 -> Z
        11 -> XZ
    """

    if m1 == 0 and m2 == 0:
        return {
            "gate": "I",
            "label": "Identity",
            "operations": []
        }

    elif m1 == 0 and m2 == 1:
        return {
            "gate": "X",
            "label": "Pauli-X",
            "operations": ["X"]
        }

    elif m1 == 1 and m2 == 0:
        return {
            "gate": "Z",
            "label": "Pauli-Z",
            "operations": ["Z"]
        }

    else:
        return {
            "gate": "XZ",
            "label": "Pauli-X + Pauli-Z",
            "operations": ["X", "Z"]
        }


def run_teleportation(shots: int = 20):

    start_time = time.perf_counter()

    simulator = AerSimulator()

    trials = []

    successful_trials = 0

    for trial_number in range(1, shots + 1):

        # =========================================================
        # CREATE REGISTERS
        # =========================================================

        q = QuantumRegister(3, "q")

        bell = ClassicalRegister(2, "bell")

        verify = ClassicalRegister(1, "verify")

        circuit = QuantumCircuit(q, bell, verify)

        # =========================================================
        # 1. PREPARE ALICE'S QUANTUM STATE
        # =========================================================

        theta = math.pi / 3
        phi = math.pi / 5

        circuit.ry(theta, q[0])
        circuit.rz(phi, q[0])

        circuit.barrier()

        # =========================================================
        # 2. CREATE BELL PAIR
        #
        # q1 = Alice's entangled qubit
        # q2 = Bob's entangled qubit
        # =========================================================

        circuit.h(q[1])
        circuit.cx(q[1], q[2])

        circuit.barrier()

        # =========================================================
        # 3. BELL MEASUREMENT
        # =========================================================

        circuit.cx(q[0], q[1])
        circuit.h(q[0])

        circuit.measure(q[0], bell[0])
        circuit.measure(q[1], bell[1])

        circuit.barrier()

        # =========================================================
        # 4. CLASSICAL FEED-FORWARD
        #
        # The measured bits determine Bob's correction.
        # =========================================================

        with circuit.if_test((bell[0], 1)):
            circuit.z(q[2])

        with circuit.if_test((bell[1], 1)):
            circuit.x(q[2])

        circuit.barrier()

        # =========================================================
        # 5. VERIFY BOB'S STATE
        #
        # Undo Alice's preparation.
        # If teleportation worked, Bob should measure |0>.
        # =========================================================

        circuit.rz(-phi, q[2])
        circuit.ry(-theta, q[2])

        circuit.measure(q[2], verify[0])

        # =========================================================
        # RUN QISKIT
        # =========================================================

        result = simulator.run(
            circuit,
            shots=1
        ).result()

        counts = result.get_counts()

        raw_result = next(iter(counts.keys()))

        # =========================================================
        # QISKIT CLASSICAL REGISTER ORDER
        #
        # Output format:
        #
        # verify bell
        #
        # Example:
        #
        # 0 01
        #
        # =========================================================

        parts = raw_result.split()

        if len(parts) == 2:

            verify_bits = parts[0]
            bell_bits = parts[1]

        else:

            raise RuntimeError(
                f"Unexpected Qiskit result format: {raw_result}"
            )

        # =========================================================
        # EXTRACT ACTUAL BELL MEASUREMENT
        #
        # bell register is displayed MSB -> LSB.
        #
        # bell[1] = first displayed bit
        # bell[0] = second displayed bit
        # =========================================================

        m1 = int(bell_bits[0])
        m2 = int(bell_bits[1])

        verification_bit = int(verify_bits)

        correction = get_correction(m1, m2)

        verification_passed = verification_bit == 0

        if verification_passed:
            successful_trials += 1

        # =========================================================
        # STORE THIS REAL QISKIT TRIAL
        # =========================================================

        trials.append(
            {
                "trial": trial_number,

                "bell_measurement": {
                    "m1": m1,
                    "m2": m2,
                    "bits": f"{m1}{m2}"
                },

                "pauli_correction": correction,

                "verification": {
                    "bit": verification_bit,
                    "passed": verification_passed
                }
            }
        )

    # =============================================================
    # FINAL RESULT
    # =============================================================

    success_rate = successful_trials / shots

    latency_ms = (
        time.perf_counter() - start_time
    ) * 1000

    # Use the final actual Qiskit trial for the live UI.
    latest_trial = trials[-1]

    return {
        "protocol": "quantum_teleportation",

        "shots": shots,

        "teleportation_success_rate": success_rate,

        "bell_measurement":
            latest_trial["bell_measurement"],

        "pauli_correction":
            latest_trial["pauli_correction"],

        "verification":
            latest_trial["verification"],

        "trials": trials,

        "latency_ms": round(latency_ms, 3)
    }
    # =============================================================
# ATTACK-AWARE QUANTUM TELEPORTATION
# =============================================================

def run_attack_teleportation(
    attack_type: str,
    shots: int = 20,
    genuine_key: str = "alice-secret-key-123",
    fake_key: str = "attacker-guessed-key"
):
    """
    Runs a real Qiskit teleportation simulation while applying
    the selected attack.

    The returned Bell measurements, Pauli corrections and
    verification bits are generated by Qiskit.
    """

    from signatures import derive_angles_for_copy

    start_time = time.perf_counter()

    simulator = AerSimulator()

    trials = []
    successful_trials = 0

    for trial_number in range(1, shots + 1):

        # -----------------------------------------------------
        # Genuine Alice state
        # -----------------------------------------------------

        genuine_theta, genuine_phi = derive_angles_for_copy(
            "Transfer 500 credits to Bob",
            genuine_key,
            trial_number - 1
        )

        # -----------------------------------------------------
        # State used by the attack
        # -----------------------------------------------------

        if attack_type == "forgery":

            # Attacker creates a state using a wrong key.
            theta, phi = derive_angles_for_copy(
                "Transfer 500 credits to Bob",
                fake_key,
                trial_number - 1
            )

        else:

            # Other attacks start with Alice's genuine state.
            theta = genuine_theta
            phi = genuine_phi

        # -----------------------------------------------------
        # Registers
        # -----------------------------------------------------

        q = QuantumRegister(3, "q")

        bell = ClassicalRegister(2, "bell")
        verify = ClassicalRegister(1, "verify")

        circuit = QuantumCircuit(
            q,
            bell,
            verify
        )

        # -----------------------------------------------------
        # 1. PREPARE STATE
        # -----------------------------------------------------

        circuit.ry(theta, q[0])
        circuit.rz(phi, q[0])

        circuit.barrier()

        # -----------------------------------------------------
        # 2. CREATE BELL PAIR
        # -----------------------------------------------------

        circuit.h(q[1])
        circuit.cx(q[1], q[2])

        circuit.barrier()

        # -----------------------------------------------------
        # 3. ATTACK INJECTION
        # -----------------------------------------------------

        if attack_type == "channel_manipulation":

            # Eve measures Bob's entangled qubit.
            # This destroys the original entanglement.

            circuit.measure(
                q[2],
                bell[0]
            )

            circuit.barrier()

        # -----------------------------------------------------
        # 4. BELL MEASUREMENT
        # -----------------------------------------------------

        circuit.cx(q[0], q[1])
        circuit.h(q[0])

        circuit.measure(q[0], bell[0])
        circuit.measure(q[1], bell[1])

        circuit.barrier()

        # -----------------------------------------------------
        # 5. PAULI CORRECTION
        # -----------------------------------------------------

        # Normal teleportation:
        #
        # 00 -> I
        # 01 -> X
        # 10 -> Z
        # 11 -> XZ
        #
        # Impersonation deliberately applies the
        # WRONG correction.

        if attack_type == "impersonation":

            with circuit.if_test((bell[0], 0)):
                circuit.z(q[2])

            with circuit.if_test((bell[1], 0)):
                circuit.x(q[2])

        else:

            with circuit.if_test((bell[0], 1)):
                circuit.z(q[2])

            with circuit.if_test((bell[1], 1)):
                circuit.x(q[2])

        circuit.barrier()

        # -----------------------------------------------------
        # 6. VERIFY AGAINST GENUINE ALICE STATE
        # -----------------------------------------------------

        circuit.rz(-genuine_phi, q[2])
        circuit.ry(-genuine_theta, q[2])

        circuit.measure(q[2], verify[0])

        # -----------------------------------------------------
        # 7. RUN QISKIT
        # -----------------------------------------------------

        result = simulator.run(
            circuit,
            shots=1
        ).result()

        counts = result.get_counts()

        raw_result = next(iter(counts.keys()))

        parts = raw_result.split()

        if len(parts) == 2:

            verify_bits = parts[0]
            bell_bits = parts[1]

        else:

            raise RuntimeError(
                f"Unexpected Qiskit result format: {raw_result}"
            )

        # -----------------------------------------------------
        # 8. READ REAL QISKIT BITS
        # -----------------------------------------------------

        verification_bit = int(verify_bits)

        m1 = int(bell_bits[0])
        m2 = int(bell_bits[1])

        # -----------------------------------------------------
        # 9. DETERMINE CORRECTION
        # -----------------------------------------------------

        correction = get_correction(m1, m2)

        # For impersonation, the actual correction is intentionally
        # the opposite operation. Describe what was actually applied.

        if attack_type == "impersonation":

            wrong_operations = []

            if m1 == 0:
                wrong_operations.append("Z")

            if m2 == 0:
                wrong_operations.append("X")

            if not wrong_operations:
                wrong_gate = "I"
                wrong_label = "Identity"
            else:
                wrong_gate = "+".join(wrong_operations)
                wrong_label = "Wrong " + " + ".join(
                    f"Pauli-{x}" for x in wrong_operations
                )

            correction = {
                "gate": wrong_gate,
                "label": wrong_label,
                "operations": wrong_operations
            }

        # -----------------------------------------------------
        # 10. VERIFICATION
        # -----------------------------------------------------

        verification_passed = verification_bit == 0

        if verification_passed:
            successful_trials += 1

        # -----------------------------------------------------
        # 11. ATTACK DESCRIPTION
        # -----------------------------------------------------

        if attack_type == "forgery":

            effect = (
                "Forged quantum state prepared using an "
                "unauthorized key."
            )

        elif attack_type == "impersonation":

            effect = (
                "Incorrect Pauli correction applied by "
                "impersonating relay."
            )

        elif attack_type == "channel_manipulation":

            effect = (
                "Quantum channel disturbed before Bob "
                "received the entangled qubit."
            )

        elif attack_type == "replay":

            effect = (
                "Previously valid quantum signature replayed."
            )

        else:

            effect = "No attack."

        # -----------------------------------------------------
        # 12. STORE TRIAL
        # -----------------------------------------------------

        trials.append(
            {
                "trial": trial_number,

                "bell_measurement": {
                    "m1": m1,
                    "m2": m2,
                    "bits": f"{m1}{m2}"
                },

                "pauli_correction": correction,

                "verification": {
                    "bit": verification_bit,
                    "passed": verification_passed
                },

                "attack_effect": effect
            }
        )

    # ---------------------------------------------------------
    # FINAL RESULT
    # ---------------------------------------------------------

    success_rate = successful_trials / shots

    latency_ms = (
        time.perf_counter() - start_time
    ) * 1000

    latest_trial = trials[-1]

    return {
        "protocol": "quantum_teleportation_attack",

        "attack_type": attack_type,

        "shots": shots,

        "teleportation_success_rate": success_rate,

        "bell_measurement":
            latest_trial["bell_measurement"],

        "pauli_correction":
            latest_trial["pauli_correction"],

        "verification":
            latest_trial["verification"],

        "attack_effect":
            latest_trial["attack_effect"],

        "trials": trials,

        "latency_ms": round(latency_ms, 3)
    }